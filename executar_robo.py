"""PONTO DE ENTRADA do robô pós-entrega do FOMEZERO (AIPA).

Lê os lotes de doação entregues (entrada/lotes_entregues.json) e as mensagens da IoT (entrada/iot/*.log),
usa IA (spaCy + scikit-learn + regras) para decidir o que segue sozinho e o que vai para revisão humana,
calcula o CO₂ evitado (kg CO₂eq, estimativa), pontos e Selo Verde ESG, gera o Termo de Doação em PDF,
lança no portal SIMULADO com Selenium, confirma pela API REST e grava CT-04, CT-05, log e relatório.

Uso:
  python executar_robo.py                    execução normal (sobe o portal simulado se preciso)
  python executar_robo.py --limpar           apaga saida/ e o banco do portal antes (execução limpa)
  python executar_robo.py --agendar 10       repete a cada 10 minutos (Ctrl+C para parar)
  python executar_robo.py --sem-portal       não sobe o portal (simula portal fora do ar)
  python executar_robo.py --cenario NOME     demonstração de falha (ver robo/cenarios.py)
  python executar_robo.py --trabalho PASTA   usa outra pasta de trabalho (entrada/ e saida/ dentro dela)
  python executar_robo.py --param CHAVE=VALOR  sobrescreve um parâmetro de config/parametros.json
"""
from __future__ import annotations

import argparse
import secrets
import shutil
import sys
import time

from robo.cenarios import CENARIOS, preparar
from robo.config import BASE, Caminhos, carregar_parametros, carregar_segredos
from robo.processo import Robo


def rodar(args) -> int:
    trabalho = BASE if not args.trabalho else (BASE / args.trabalho if not args.trabalho.is_absolute() else args.trabalho)
    overrides = list(args.param or [])
    sem_portal, modo = args.sem_portal, args.portal_modo
    segredos = carregar_segredos()
    if args.cenario:
        trabalho, c = preparar(args.cenario)
        overrides = list(c.get("params", [])) + overrides
        sem_portal = sem_portal or c.get("sem_portal", False)
        modo = c.get("portal_modo", modo)
        if c.get("senha_errada"):
            segredos = dict(segredos, PORTAL_SENHA=secrets.token_urlsafe(12))  # senha errada só em memória
        print(f"[cenário {args.cenario} | {c['falha']}] {c['descricao']} -> pasta {trabalho.relative_to(BASE)}")
    params = carregar_parametros(overrides)
    if args.headful:
        params["HEADLESS"] = False
    if args.limpar:
        cam = Caminhos(trabalho, params)
        if cam.saida.exists() and trabalho == BASE:
            for sub in cam.PASTAS_SAIDA + ("estado.db",):
                alvo = cam.saida / sub
                if alvo.is_dir():
                    shutil.rmtree(alvo)
                elif alvo.exists():
                    alvo.unlink()
        if cam.portal_db.exists():
            cam.portal_db.unlink()
    robo = Robo(trabalho, params, segredos, sem_portal=sem_portal, portal_modo=modo)
    rel = robo.executar()
    r = rel["resumo"]
    print(f"\n== {rel['id_execucao']} | tratados {r['lotes_tratados']} | processado {r['processado']} | revisão humana "
          f"{r['revisao_humana']} | falha {r['falha']} | duplicados {r['ignorado_duplicado']} | não entregues "
          f"{r['ignorado_nao_entregue']} | taxa de erros {r['taxa_erros']} | {rel['duracao_total_s']} s")
    print(f"   relatório: {robo.relatorio_md.relative_to(BASE)} | log: {robo.arquivo_log.relative_to(BASE)}")
    cg = rel.get("conferencia_gabarito")
    if cg:
        print(f"   gabarito: {cg['acertos']} de {cg['n_registros']} registros conferem")
    return 3 if rel.get("abortado") else 0


def main() -> int:
    for fluxo in (sys.stdout, sys.stderr):  # console do Windows: CO₂ e acentos sem erro de codificação
        if hasattr(fluxo, "reconfigure"):
            fluxo.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Robô pós-entrega do FOMEZERO (AIPA). Dados e portal SIMULADOS.")
    ap.add_argument("--trabalho", type=lambda s: __import__("pathlib").Path(s))
    ap.add_argument("--sem-portal", action="store_true")
    ap.add_argument("--portal-modo", default="nenhum", choices=["nenhum", "erro_api", "lento", "json_invalido"])
    ap.add_argument("--param", action="append")
    ap.add_argument("--cenario", choices=sorted(CENARIOS))
    ap.add_argument("--limpar", action="store_true")
    ap.add_argument("--headful", action="store_true", help="mostra o navegador (para gravar a demonstração)")
    ap.add_argument("--agendar", type=float, metavar="MIN", help="repete a cada MIN minutos (schedule)")
    ap.add_argument("--ciclos", type=int, default=0, help="com --agendar: para depois de N execuções (0 = sem fim)")
    args = ap.parse_args()
    if not args.agendar:
        return rodar(args)
    import schedule
    feitos = {"n": 0}

    def ciclo():
        feitos["n"] += 1
        print(f"\n[agendamento] execução {feitos['n']}")
        try:
            rodar(args)
        except Exception as e:  # noqa: BLE001 - o agendador não para por causa de uma execução
            print(f"[agendamento] execução falhou: {type(e).__name__}: {e}", file=sys.stderr)
        args.limpar = False

    ciclo()
    schedule.every(args.agendar).minutes.do(ciclo)
    while not args.ciclos or feitos["n"] < args.ciclos:
        schedule.run_pending()
        time.sleep(1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
