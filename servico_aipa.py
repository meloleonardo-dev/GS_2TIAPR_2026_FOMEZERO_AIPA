"""SERVIÇO LOCAL da AIPA para o portal FOMEZERO (FEMD): o robô roda na hora em que a entrega é confirmada.

O frontend manda o lote de doação entregue (CT-03) para POST /api/lotes. O serviço guarda o lote na pasta
de trabalho do serviço (servico_dados/entrada/lotes_entregues.json) e executa o MESMO robô do
executar_robo.py: validação, idempotência, IA (spaCy + scikit-learn + regras R1 a R11), CO₂ evitado,
pontos, Selo Verde ESG, Termo de Doação em PDF, lançamento no portal SIMULADO (Selenium) e confirmação
pela API. Devolve o CT-04 do lote. Nada aqui declara que o alimento é seguro para consumo.

Uso:
  python servico_aipa.py               sobe em http://127.0.0.1:5070 (só neste computador)
  python servico_aipa.py --porta 5071  outra porta
  python servico_aipa.py --limpar      apaga o estado do serviço antes (servico_dados/)

Rotas:
  GET  /api/saude                 serviço no ar
  POST /api/lotes                 processa um lote ({...} ou {"lotes": [...]}); devolve o CT-04
  GET  /api/resultados            todos os CT-04 do serviço (ct04_lotes.json)
  GET  /api/termos/<lote_id>      Termo de Doação em PDF do lote processado
  GET  /api/revisao               fila de revisão humana (lotes pendentes, texto já mascarado)
  POST /api/revisao/<lote_id>     decisão do operador ({"decisao", "kg_aprovado", "revisor"}); roda o robô
Dados e portal SIMULADOS.
"""
from __future__ import annotations

import argparse
import atexit
import csv
import json
import re
import shutil
import sys
import threading
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_file

from robo import portal_servidor
from robo.config import BASE, Caminhos, carregar_parametros, carregar_segredos
from robo.processo import Robo

TRABALHO = BASE / "servico_dados"
ORIGEM_LOCAL = re.compile(r"^http://(localhost|127\.0\.0\.1)(:\d+)?$")
# Mesmo que o cadastro do portal aceita (texto livre, com espaço e acento), menos o que quebra o nome do
# arquivo do Termo no Windows: barras, : * ? " < > |, caracteres de controle e ponto ou espaço no fim.
LOTE_ID = re.compile(r'^[^\x00-\x1f/\\:*?"<>|]{0,79}[^\x00-\x1f/\\:*?"<>|. ]$')
LIMITE_LOTES_POR_PEDIDO = 50

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 256 * 1024
trava = threading.Lock()  # uma execução do robô por vez (o estado é um SQLite e um arquivo de entrada)
estado = {"params": None, "segredos": None, "portal": None, "trabalho": TRABALHO}


def parametros(trabalho: Path, portal_porta: int) -> dict:
    """Parâmetros do robô com a pasta de trabalho do serviço; a IoT lida é a física versionada."""
    return carregar_parametros([
        "ARQUIVO_LOTES=entrada/lotes_entregues.json",
        f"PASTA_IOT={json.dumps(str(BASE / 'dados' / 'iot_fisico'))}",
        "ARQUIVO_DECISOES=entrada/decisoes_revisao.csv",
        f"GABARITO_DEMO={json.dumps(str(trabalho / 'sem_gabarito.json'))}",  # sem gabarito: lotes do portal
        f"PORTAL_PORTA={portal_porta}",
        f"PORTAL_URL={json.dumps(f'http://127.0.0.1:{portal_porta}')}",
    ])


@app.after_request
def cors(resposta):
    origem = request.headers.get("Origin", "")
    if ORIGEM_LOCAL.match(origem):  # só o frontend rodando neste computador
        resposta.headers["Access-Control-Allow-Origin"] = origem
        resposta.headers["Vary"] = "Origin"
        resposta.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        resposta.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resposta


def ler_entrada(arquivo: Path) -> list[dict]:
    if not arquivo.exists():
        return []
    dados = json.loads(arquivo.read_text(encoding="utf-8"))
    return dados.get("lotes", []) if isinstance(dados, dict) else []


def guardar_entrada(arquivo: Path, novos: list[dict]):
    """Acrescenta ou substitui (mesmo lote_id) os lotes recebidos. A idempotência fica com o robô (T4)."""
    lotes = ler_entrada(arquivo)
    por_id = {l.get("lote_id"): i for i, l in enumerate(lotes) if isinstance(l, dict)}
    for novo in novos:
        i = por_id.get(novo.get("lote_id"))
        if i is None:
            por_id[novo.get("lote_id")] = len(lotes)
            lotes.append(novo)
        else:
            lotes[i] = novo
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    temporario = arquivo.with_suffix(".tmp")
    temporario.write_text(json.dumps({"_aviso": "SIMULADO. Lotes recebidos do portal FOMEZERO pelo serviço da AIPA.",
                                      "lotes": lotes}, ensure_ascii=False, indent=2), encoding="utf-8")
    temporario.replace(arquivo)


def ler_ct04() -> dict:
    arquivo = Caminhos(estado["trabalho"], estado["params"]).sub("ct04") / "ct04_lotes.json"
    if not arquivo.exists():
        return {"versao_contrato": "ct04-v0", "simulado": True, "lotes": []}
    return json.loads(arquivo.read_text(encoding="utf-8"))


@app.get("/api/saude")
def saude():
    return jsonify({"status": "ok", "servico": "aipa-robo-pos-entrega", "versao_contrato": "ct04-v0",
                    "simulado": True, "portal_simulado_no_ar": portal_servidor.no_ar(estado["params"]["PORTAL_URL"])})


@app.route("/api/lotes", methods=["POST", "OPTIONS"])
def processar():
    if request.method == "OPTIONS":
        return ("", 204)
    corpo = request.get_json(silent=True)
    if corpo is None:
        return jsonify({"status": "erro", "mensagem": "Envie o lote de doação em JSON (CT-03)."}), 400
    lotes = corpo.get("lotes") if isinstance(corpo, dict) and "lotes" in corpo else [corpo]
    if not isinstance(lotes, list) or not lotes or len(lotes) > LIMITE_LOTES_POR_PEDIDO \
            or not all(isinstance(l, dict) for l in lotes):
        return jsonify({"status": "erro", "mensagem": f"Envie de 1 a {LIMITE_LOTES_POR_PEDIDO} lotes."}), 400
    ids = [l.get("lote_id") for l in lotes]
    if not all(isinstance(i, str) and LOTE_ID.match(i) for i in ids):
        return jsonify({"status": "erro", "mensagem": "Identificador do lote inválido para a AIPA: até 80 caracteres, sem barras, dois-pontos, * ? \" < > | e sem ponto ou espaço no fim."}), 400
    with trava:
        cam = Caminhos(estado["trabalho"], estado["params"])
        guardar_entrada(cam.arquivo_lotes, lotes)
        robo = Robo(estado["trabalho"], dict(estado["params"]), estado["segredos"])
        relatorio = robo.executar()
        todos = {c.get("lote_id"): c for c in ler_ct04()["lotes"]}
    resultados = [todos.get(i) for i in ids]
    return jsonify({"status": "ok", "id_execucao": relatorio["id_execucao"], "resumo": relatorio["resumo"],
                    "lotes": resultados})


@app.get("/api/resultados")
def resultados():
    with trava:
        return jsonify(ler_ct04())


@app.get("/api/termos/<lote_id>")
def termo(lote_id: str):
    if not LOTE_ID.match(lote_id):
        abort(404)
    arquivo = Caminhos(estado["trabalho"], estado["params"]).sub("termos") / f"TERMO_{lote_id}.pdf"
    if not arquivo.exists():
        abort(404)
    return send_file(arquivo, mimetype="application/pdf", download_name=arquivo.name)


REVISOR = re.compile(r"^[A-Za-z0-9_-]{1,24}$")  # código do operador, nunca nome
COLUNAS_DECISAO = ["lote_id", "decisao", "kg_aprovado", "revisor"]
LIMITE_KG = 100000


def ler_fila() -> list[dict]:
    """Fila gerada pelo robô (T11), com o CT-04 de cada lote para mostrar o contexto ao operador."""
    cam = Caminhos(estado["trabalho"], estado["params"])
    arquivo = cam.sub("revisao") / "fila_revisao.csv"
    if not arquivo.exists():
        return []
    with open(arquivo, encoding="utf-8-sig", newline="") as f:
        linhas = list(csv.DictReader(f, delimiter=";"))
    ct04 = {c.get("lote_id"): c for c in ler_ct04()["lotes"]}
    fila = []
    for l in linhas:
        c = ct04.get(l["lote_id"]) or {}
        ia = c.get("ia") or {}
        fila.append({"lote_id": l["lote_id"], "doador_id": l["doador_id"], "motivos": c.get("motivo") or [],
                     "texto_confirmacao_mascarado": l.get("texto_confirmacao_mascarado") or "",
                     "kg_cadastrado": l.get("kg_cadastrado") or None, "kg_extraido": ia.get("kg_extraido"),
                     "kg_informado": ia.get("kg_informado"), "ocorrencia_prevista": ia.get("ocorrencia"),
                     "confianca": ia.get("confianca"), "alerta_iot": ia.get("alerta_iot"),
                     "divergencias_informadas": ia.get("divergencias_informadas") or [],
                     "triagem_visual": ia.get("triagem_visual")})
    return fila


def gravar_decisao(arquivo: Path, decisao: dict):
    """Acrescenta ou substitui a decisão do lote no CSV que o robô já lê (entrada/decisoes_revisao.csv)."""
    linhas = []
    if arquivo.exists():
        with open(arquivo, encoding="utf-8-sig", newline="") as f:
            linhas = [l for l in csv.DictReader(f, delimiter=";") if l.get("lote_id") != decisao["lote_id"]]
    linhas.append(decisao)
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    temporario = arquivo.with_suffix(".tmp")
    with open(temporario, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUNAS_DECISAO, delimiter=";", extrasaction="ignore")
        w.writeheader()
        w.writerows(linhas)
    temporario.replace(arquivo)


@app.get("/api/revisao")
def fila_revisao():
    with trava:
        return jsonify({"simulado": True, "lotes": ler_fila()})


@app.route("/api/revisao/<lote_id>", methods=["POST", "OPTIONS"])
def decidir(lote_id: str):
    if request.method == "OPTIONS":
        return ("", 204)
    if not LOTE_ID.match(lote_id):
        abort(404)
    corpo = request.get_json(silent=True) or {}
    decisao = str(corpo.get("decisao") or "").strip().lower()
    revisor = str(corpo.get("revisor") or "").strip()
    if decisao not in ("aprovado", "reprovado"):
        return jsonify({"status": "erro", "mensagem": "Escolha aprovar ou reprovar."}), 400
    if not REVISOR.match(revisor):
        return jsonify({"status": "erro", "mensagem": "Informe o código do revisor (sem nome)."}), 400
    kg = ""
    if decisao == "aprovado":
        try:
            kg_num = float(str(corpo.get("kg_aprovado")).replace(",", "."))
        except ValueError:
            kg_num = 0
        if not 0 < kg_num <= LIMITE_KG:
            return jsonify({"status": "erro", "mensagem": "Para aprovar, informe os kg aprovados (maior que zero)."}), 400
        kg = f"{kg_num:.3f}"
    with trava:
        if lote_id not in {l["lote_id"] for l in ler_fila()}:
            return jsonify({"status": "erro", "mensagem": "Este lote não está pendente na fila de revisão."}), 409
        cam = Caminhos(estado["trabalho"], estado["params"])
        gravar_decisao(cam.arquivo_decisoes, {"lote_id": lote_id, "decisao": decisao, "kg_aprovado": kg,
                                              "revisor": revisor})
        relatorio = Robo(estado["trabalho"], dict(estado["params"]), estado["segredos"]).executar()
        lote = next((c for c in ler_ct04()["lotes"] if c.get("lote_id") == lote_id), None)
    return jsonify({"status": "ok", "id_execucao": relatorio["id_execucao"], "lote": lote})


def main() -> int:
    for fluxo in (sys.stdout, sys.stderr):
        if hasattr(fluxo, "reconfigure"):
            fluxo.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Serviço local da AIPA para o portal FOMEZERO. Dados SIMULADOS.")
    ap.add_argument("--porta", type=int, default=5070, help="porta local (evite 5060 e 5061: o Chrome bloqueia)")
    ap.add_argument("--limpar", action="store_true", help="apaga a pasta de trabalho antes de subir")
    ap.add_argument("--trabalho", type=Path, default=TRABALHO, help="pasta de trabalho (padrão servico_dados/)")
    ap.add_argument("--portal-porta", type=int, default=5050, help="porta do portal SIMULADO")
    args = ap.parse_args()
    trabalho = args.trabalho.resolve()
    if args.limpar and trabalho.exists():
        shutil.rmtree(trabalho)
    trabalho.mkdir(parents=True, exist_ok=True)
    estado["trabalho"] = trabalho
    estado["params"], estado["segredos"] = parametros(trabalho, args.portal_porta), carregar_segredos()
    if not estado["segredos"]:
        print("Aviso: .env não encontrado. Copie .env.exemplo para .env (lançamento no portal vai falhar).")
    p, cam = estado["params"], Caminhos(estado["trabalho"], estado["params"])
    if not portal_servidor.no_ar(p["PORTAL_URL"]):  # portal SIMULADO fica no ar enquanto o serviço roda
        cam.sub("logs").mkdir(parents=True, exist_ok=True)
        estado["portal"] = portal_servidor.iniciar(p["PORTAL_URL"], p["PORTAL_PORTA"], cam.portal_db,
                                                   log=cam.sub("logs") / "portal_simulado.log")
        atexit.register(portal_servidor.parar, estado["portal"])
    print(f"Serviço da AIPA em http://127.0.0.1:{args.porta} (portal SIMULADO em {p['PORTAL_URL']}). Ctrl+C para parar.")
    app.run(host="127.0.0.1", port=args.porta, debug=False, threaded=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
