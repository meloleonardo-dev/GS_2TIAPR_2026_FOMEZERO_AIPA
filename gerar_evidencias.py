"""Regenera as evidências de validação em evidencias/ executando o robô de verdade (opcional; ~4 min).

1. execução normal limpa (12 lotes de demonstração + 1 em transporte, IoT FÍSICA) -> evidencias/execucao_normal/
2. segunda execução na mesma pasta (idempotência) -> evidencias/idempotencia/
3. fila de revisão + decisões (SIMULADAS pelo script, revisor OP-DEMO) + execução seguinte -> evidencias/revisao_humana/
4. cenários de falha F1 a F11, cada um em pasta separada (+ retomada de F6 e F7) -> evidencias/falhas/
5. agendamento (2 ciclos com schedule) -> evidencias/agendamento/
6. pytest -> evidencias/pytest/

Pré-requisitos: .env criado, gerar_dados_sinteticos.py e treinar_modelo.py já rodados.
Uso: python gerar_evidencias.py
"""
from __future__ import annotations

import csv
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
EV = BASE / "evidencias"
PY = sys.executable
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")

FALHAS = [("F1", "arquivo_ausente"), ("F2", "iot_ausente"), ("F3", "modelo_ausente"), ("F4", "iot_invalido"),
          ("F6", "portal_fora"), ("F7", "portal_lento"), ("F8", "erro_api"), ("F8b", "json_invalido"),
          ("F9", "credencial_invalida"), ("F10", "navegador_indisponivel"), ("F11", "disco_cheio")]
RETOMADA = {"portal_fora", "portal_lento"}


def rodar(args: list[str], destino_console: Path | None = None) -> tuple[str, int, str | None]:
    time.sleep(1.1)  # id_execucao tem resolução de segundo
    r = subprocess.run([PY, *args], cwd=BASE, env=ENV, capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    saida = r.stdout + (("\n[stderr]\n" + r.stderr) if r.stderr.strip() else "")
    if destino_console:
        destino_console.parent.mkdir(parents=True, exist_ok=True)
        destino_console.write_text(f"$ python {' '.join(args)}\n(código de saída {r.returncode})\n\n{saida}",
                                   encoding="utf-8")
    m = re.search(r"== (EXEC-\d{8}-\d{6})", r.stdout)
    return saida, r.returncode, (m.group(1) if m else None)


def copiar_execucao(trabalho: Path, id_exec: str, destino: Path, tudo: bool = True):
    s = trabalho / "saida"
    destino.mkdir(parents=True, exist_ok=True)
    for arq in (s / "logs" / f"{id_exec}.log", s / "relatorios" / f"relatorio_{id_exec}.md",
                s / "relatorios" / f"relatorio_{id_exec}.json"):
        if arq.exists():
            shutil.copy2(arq, destino / arq.name)
    if not tudo:
        return
    for sub in ("ct04", "ct05", "termos", "prints", "revisao", "quarentena"):
        if (s / sub).exists() and any((s / sub).iterdir()):
            shutil.copytree(s / sub, destino / sub, dirs_exist_ok=True)


def trecho_log(log: Path, n: int = 30) -> str:
    if not log.exists():
        return "(sem log)"
    linhas = [l.rstrip() for l in log.read_text(encoding="utf-8").splitlines()
              if re.search(r"\| (WARNING|ERROR|CRITICAL) \||\| T10 \||gateway -> (nao|revisao|duplicado|retomar)|"
                           r"contingência|já lançado|retomando|confirmado pela API", l)]
    return "\n".join(linhas[:n]) + ("\n..." if len(linhas) > n else "")


def resumo_rel(trabalho: Path, id_exec: str) -> dict:
    p = trabalho / "saida" / "relatorios" / f"relatorio_{id_exec}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def tabela_lotes(rel: dict) -> str:
    linhas = ["| lote_id | status | motivo | protocolo |", "|---|---|---|---|"]
    for r in rel.get("resultados", []):
        linhas.append(f"| {r.get('lote_id') or '(vazio)'} | {r['status']} | {', '.join(r.get('motivo', []))} | "
                      f"{r.get('protocolo') or ''} |")
    return "\n".join(linhas)


def main():
    for sub in ("execucao_normal", "idempotencia", "revisao_humana", "falhas", "agendamento", "pytest"):
        if (EV / sub).exists():
            shutil.rmtree(EV / sub)
    indice = []

    # 1. execução normal
    print("1/6 execução normal")
    _, cod, id1 = rodar(["executar_robo.py", "--limpar"], EV / "execucao_normal" / "console.txt")
    copiar_execucao(BASE, id1, EV / "execucao_normal")
    rel1 = resumo_rel(BASE, id1)
    indice.append(("Execução normal", f"execucao_normal/relatorio_{id1}.md", rel1["resumo"]))

    # 2. idempotência
    print("2/6 idempotência")
    _, _, id2 = rodar(["executar_robo.py"], EV / "idempotencia" / "console_2a_execucao.txt")
    copiar_execucao(BASE, id2, EV / "idempotencia", tudo=False)
    rel2 = resumo_rel(BASE, id2)
    (EV / "idempotencia" / "LEIA-ME.md").write_text("\n".join([
        "# Idempotência (rodar duas vezes não lança de novo)", "",
        "Comandos: `python executar_robo.py --limpar` (1ª) e depois `python executar_robo.py` (2ª), mesma pasta e mesmo "
        "banco do portal SIMULADO. Contagem lida da API do portal (`GET /api/resumo`) no fim de cada execução.", "",
        "| execução | lançamentos no portal (total) | processados nesta execução | duplicados ignorados |",
        "|---|---|---|---|",
        f"| 1ª {id1} | {rel1.get('portal_total_lancamentos')} | {rel1['resumo']['processado']} | {rel1['resumo']['ignorado_duplicado']} |",
        f"| 2ª {id2} | {rel2.get('portal_total_lancamentos')} | {rel2['resumo']['processado']} | {rel2['resumo']['ignorado_duplicado']} |",
        "", "Trecho do log da 2ª execução:", "", "```", trecho_log(BASE / "saida" / "logs" / f"{id2}.log", 20), "```"]) + "\n",
        encoding="utf-8")
    indice.append(("Idempotência (F5)", "idempotencia/LEIA-ME.md", rel2["resumo"]))

    # 3. revisão humana (decisões SIMULADAS pelo script)
    print("3/6 revisão humana")
    trab = BASE / "saida" / "cenarios" / "revisao_humana"
    if trab.exists():
        shutil.rmtree(trab)
    (trab / "entrada" / "iot").mkdir(parents=True)
    shutil.copy2(BASE / "dados" / "sinteticos" / "lotes_demo.json", trab / "entrada" / "lotes_entregues.json")
    for log in (BASE / "dados" / "iot_fisico").glob("*.log"):
        shutil.copy2(log, trab / "entrada" / "iot" / log.name)
    _, _, ida = rodar(["executar_robo.py", "--trabalho", str(trab.relative_to(BASE))],
                      EV / "revisao_humana" / "console_1a_execucao.txt")
    fila = trab / "saida" / "revisao" / "fila_revisao.csv"
    shutil.copy2(fila, EV / "revisao_humana" / "fila_revisao_gerada.csv")
    decisoes = {"LOTE-2026-0006": ("aprovado", "6", "IA errou: texto sem ocorrência"),
                "LOTE-2026-0007": ("aprovado", "8", "2 kg amassados descontados"),
                "LOTE-2026-0001": ("reprovado", "", "alerta físico de quebra_cadeia_frio")}
    with open(fila, encoding="utf-8-sig") as f:
        linhas = list(csv.DictReader(f, delimiter=";"))
    with open(trab / "entrada" / "decisoes_revisao.csv", "w", encoding="utf-8-sig", newline="") as f:
        cols = list(linhas[0].keys()) + ["observacao"]
        w = csv.DictWriter(f, fieldnames=cols, delimiter=";")
        w.writeheader()
        for l in linhas:
            if l["lote_id"] in decisoes:
                d, kg, obs = decisoes[l["lote_id"]]
                l.update({"decisao": d, "kg_aprovado": kg, "revisor": "OP-DEMO",
                          "observacao": "decisão SIMULADA pelo script de demonstração (não é revisão humana real): " + obs})
            w.writerow(l)
    shutil.copy2(trab / "entrada" / "decisoes_revisao.csv", EV / "revisao_humana" / "decisoes_revisao_SIMULADAS.csv")
    _, _, idb = rodar(["executar_robo.py", "--trabalho", str(trab.relative_to(BASE))],
                      EV / "revisao_humana" / "console_2a_execucao.txt")
    copiar_execucao(trab, idb, EV / "revisao_humana", tudo=False)
    for lid in decisoes:
        shutil.copy2(trab / "saida" / "ct04" / f"{lid}.json", EV / "revisao_humana" / f"ct04_{lid}_apos_decisao.json")
    relb = resumo_rel(trab, idb)
    (EV / "revisao_humana" / "LEIA-ME.md").write_text("\n".join([
        "# Revisão humana (raia do Operador no BPMN)", "",
        "1ª execução gera `fila_revisao_gerada.csv`. As decisões em `decisoes_revisao_SIMULADAS.csv` foram escritas "
        "**pelo script de demonstração** (revisor `OP-DEMO`), no lugar do operador; **não são revisão humana real**. "
        "A 2ª execução lê o arquivo (H1) e: aprovado -> T7 em diante com `origem_quantidade = revisao_humana`; "
        "reprovado -> continua `revisao_humana` com `revisao.situacao = reprovado` (final), sem pontos.", "",
        f"Resultado da 2ª execução ({idb}):", "", tabela_lotes(relb), "", "Trecho do log:", "", "```",
        trecho_log(trab / "saida" / "logs" / f"{idb}.log", 25), "```"]) + "\n", encoding="utf-8")
    indice.append(("Revisão humana", "revisao_humana/LEIA-ME.md", relb["resumo"]))

    # 4. falhas
    print("4/6 cenários de falha")
    sys.path.insert(0, str(BASE))
    from robo.cenarios import CENARIOS
    for cod_f, nome in FALHAS:
        dest = EV / "falhas" / f"{cod_f}_{nome}"
        cmd = ["executar_robo.py", "--cenario", nome]
        _, cod, idc = rodar(cmd, dest / "console.txt")
        trab = BASE / "saida" / "cenarios" / nome
        copiar_execucao(trab, idc, dest)
        relc = resumo_rel(trab, idc)
        partes = [f"# {cod_f} · {CENARIOS[nome]['descricao']}", "",
                  f"Comando: `python {' '.join(cmd)}` (código de saída {cod}). Pasta de trabalho separada "
                  f"`saida/cenarios/{nome}/`. Dados SIMULADOS; portal SIMULADO.", "",
                  "## Trecho do log", "", "```", trecho_log(trab / "saida" / "logs" / f"{idc}.log"), "```", "",
                  "## Resultado", "", tabela_lotes(relc) if relc.get("resultados") else
                  f"Nenhum lote processado: {relc.get('falhas_tratadas')}", "",
                  f"Falhas tratadas registradas no relatório: {len(relc.get('falhas_tratadas', []))}. "
                  f"Execução terminou com relatório (`relatorio_{idc}.md`)."]
        if nome in RETOMADA:
            cmd2 = ["executar_robo.py", "--trabalho", f"saida/cenarios/{nome}"]
            _, _, idr = rodar(cmd2, dest / "console_retomada.txt")
            copiar_execucao(trab, idr, dest / "retomada", tudo=False)
            relr = resumo_rel(trab, idr)
            partes += ["", "## Retomada (portal normal, mesma pasta)", "", f"Comando: `python {' '.join(cmd2)}`", "",
                       tabela_lotes(relr), "", "```", trecho_log(trab / "saida" / "logs" / f"{idr}.log", 12), "```"]
        (dest / "LEIA-ME.md").write_text("\n".join(partes) + "\n", encoding="utf-8")
        indice.append((f"{cod_f} {CENARIOS[nome]['descricao']}", f"falhas/{cod_f}_{nome}/LEIA-ME.md",
                       relc.get("resumo", {})))

    # 5. agendamento
    print("5/6 agendamento")
    trab = BASE / "saida" / "cenarios" / "agendamento"
    if trab.exists():
        shutil.rmtree(trab)
    (trab / "entrada" / "iot").mkdir(parents=True)
    shutil.copy2(BASE / "dados" / "sinteticos" / "lotes_demo.json", trab / "entrada" / "lotes_entregues.json")
    for log in (BASE / "dados" / "iot_fisico").glob("*.log"):
        shutil.copy2(log, trab / "entrada" / "iot" / log.name)
    rodar(["executar_robo.py", "--trabalho", "saida/cenarios/agendamento", "--agendar", "0.25", "--ciclos", "2"],
          EV / "agendamento" / "console.txt")
    indice.append(("Agendamento (schedule, 2 ciclos de 15 s)", "agendamento/console.txt", {}))

    # 6. pytest
    print("6/6 pytest")
    r = subprocess.run([PY, "-m", "pytest", "testes", "-v", "-p", "no:cacheprovider"], cwd=BASE, env=ENV,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    (EV / "pytest").mkdir(parents=True, exist_ok=True)
    (EV / "pytest" / "saida_pytest.txt").write_text(f"$ python -m pytest testes -v\n(código {r.returncode})\n\n"
                                                    + r.stdout + r.stderr, encoding="utf-8")
    ult = [l for l in r.stdout.splitlines() if "passed" in l or "failed" in l][-1:]
    indice.append(("pytest", "pytest/saida_pytest.txt", {"resultado": ult[0] if ult else r.returncode}))

    linhas = ["# Evidências de validação (geradas por `python gerar_evidencias.py`)", "",
              "Tudo foi produzido por execução real do robô nesta máquina. Dados de lote SINTÉTICOS (SIMULADO); portal "
              "SIMULADO; IoT FÍSICA real (logs de 10 e 11/11/2026) na execução normal e SIMULADA só no cenário F4, em "
              "pasta separada. Métricas da IA: `metricas_ia_AAAA-MM-DD.md` (v1 x v2 no teste sintético e no "
              "desenvolvimento, gerado por `treinar_modelo.py`), `metricas_cego_v2_AAAA-MM-DD.md` (medição única do "
              "cego v2, gerado por `medir_cego_v2.py`; congelamento e hash em `cego_v2_CONGELADO.md`) e "
              "`arquivo_v1/` (métricas da v1 publicadas no TAR-012, sem mudança).", "",
              "| evidência | arquivo | resumo |", "|---|---|---|"]
    for nome, arq, res in indice:
        txt = ", ".join(f"{k}={v}" for k, v in res.items() if k in ("processado", "revisao_humana", "falha",
                                                                    "ignorado_duplicado", "taxa_erros", "resultado"))
        linhas.append(f"| {nome} | `{arq}` | {txt} |")
    (EV / "LEIA-ME.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print("evidências em", EV)


if __name__ == "__main__":
    main()
