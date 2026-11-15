"""Relatório de execução (T12, temas G e H): tempo de ciclo e taxa de erros por tarefa do BPMN.

Métricas da aula de BPM (02_Process_tasks_bpm_bpmn.pdf p. 31-32): tempo de ciclo e taxa de erros.
Custo por processo NÃO é medido (não há custo real): limitação declarada.
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path

NOMES = {"T1": "Verificar ambiente", "T2": "Ler entradas", "T3": "Validar dados", "T4": "Checar idempotência",
         "T5": "IA: extrair kg e classificar", "T6": "Regras inteligentes", "T7": "Calcular CO₂, pontos e selo",
         "T8": "Gerar e conferir Termo de Doação", "T9": "Lançar no portal e confirmar via API",
         "T10": "Gravar estado e CT-04", "T11": "Gravar CT-05", "T12": "Relatório de execução"}


def _estat(v: list[float]) -> dict:
    if not v:
        return {"n": 0, "media_ms": None, "min_ms": None, "max_ms": None}
    return {"n": len(v), "media_ms": round(statistics.mean(v), 2), "min_ms": round(min(v), 2),
            "max_ms": round(max(v), 2)}


def _conferir_gabarito(caminho: Path, resultados: list[dict]) -> dict | None:
    if not caminho.exists():
        return None
    esperado = json.loads(caminho.read_text(encoding="utf-8"))["esperado"]
    por_indice = {r["indice"]: r for r in resultados}
    linhas, acertos = [], 0
    for e in esperado:
        r = por_indice.get(e["indice"])
        if r is None or (r.get("lote_id") or "") != (e["lote_id"] or ""):
            return None  # a entrada não é o conjunto de demonstração
        ok_status = r["status"] == e["status"]
        ok_motivo = all(m in r.get("motivo", []) for m in e["motivo_contem"])
        ok_extra = all(r.get(k) == e[k] for k in ("selo_verde_esg", "selo_situacao") if k in e)
        ok = ok_status and ok_motivo and ok_extra
        acertos += ok
        linhas.append({"indice": e["indice"], "lote_id": e["lote_id"], "caso": e["caso"], "esperado": e["status"],
                       "obtido": r["status"], "motivo_esperado_contem": e["motivo_contem"],
                       "motivo_obtido": r.get("motivo", []), "acerto": ok})
    demo = [l for l in linhas if l["esperado"] != "ignorado_nao_entregue"]
    return {"n_registros": len(linhas), "acertos": acertos, "erros": len(linhas) - acertos,
            "n_lotes_demonstracao": len(demo), "acertos_lotes_demonstracao": sum(l["acerto"] for l in demo),
            "linhas": linhas}


def gerar(pasta: Path, obs, resultados: list[dict], contexto: dict, gabarito: Path | None) -> tuple[Path, Path]:
    por_tarefa = {}
    for ex in obs.execucoes:
        t = por_tarefa.setdefault(ex["elemento"], {"execucoes": 0, "erros": 0, "duracoes": [], "motivos_erro": {}})
        t["execucoes"] += 1
        t["duracoes"].append(ex["duracao_ms"])
        if ex["resultado"] == "erro":
            t["erros"] += 1
            t["motivos_erro"][ex["motivo"]] = t["motivos_erro"].get(ex["motivo"], 0) + 1
    tarefas = {}
    for k in sorted(por_tarefa, key=lambda x: int(x[1:])):
        t = por_tarefa[k]
        tarefas[k] = {"nome": NOMES.get(k, k), "execucoes": t["execucoes"], "erros": t["erros"],
                      "taxa_erros": round(t["erros"] / t["execucoes"], 4), "motivos_erro": t["motivos_erro"],
                      **_estat(t["duracoes"])}
    cont = {s: sum(r["status"] == s for r in resultados) for s in
            ("processado", "revisao_humana", "falha", "ignorado_duplicado", "ignorado_nao_entregue")}
    tratados = cont["processado"] + cont["revisao_humana"] + cont["falha"]
    taxa = (lambda n: round(n / tratados, 4) if tratados else None)
    ciclo = list(obs.ciclo_lote.values())
    resumo = {
        "lotes_no_arquivo": len(resultados), "lotes_tratados": tratados, **cont,
        "ignorados_nao_entregues": cont["ignorado_nao_entregue"],
        "taxa_automacao": taxa(cont["processado"]), "taxa_revisao_humana": taxa(cont["revisao_humana"]),
        "taxa_erros": taxa(cont["falha"]),
    }
    rel = {
        "_aviso": "Relatório gerado pelo robô (execução real) com dados SIMULADOS; evidência da IoT física e simulada "
                  "nunca misturadas: veja 'modo_iot'.",
        **contexto, "resumo": resumo,
        "definicoes": {"lotes_tratados": "entregues, sem contar duplicados nem não entregues",
                       "taxa_erros": "lotes com status falha / lotes tratados",
                       "tempo_de_ciclo_lote": "T3 a T10 por lote, em ms (inclui espera do portal)",
                       "custo_por_processo": "não medido (sem custo real)"},
        "tempo_de_ciclo_lote_ms": _estat(ciclo), "tempo_de_ciclo_por_lote": obs.ciclo_lote,
        "tarefas_bpmn": tarefas,
        "gateways": {g: dict(s) for g, s in obs.gateways.items()},
        "falhas_tratadas": obs.falhas_tratadas,
        "resultados": resultados,
        "trilhas_bpmn": {k: v for k, v in obs.trilhas.items()},
        "conferencia_gabarito": _conferir_gabarito(gabarito, resultados) if gabarito else None,
    }
    pasta.mkdir(parents=True, exist_ok=True)
    pj = pasta / f"relatorio_{obs.id_execucao}.json"
    pj.write_text(json.dumps(rel, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    def tab(cab, linhas):
        out = ["| " + " | ".join(cab) + " |", "|" + "---|" * len(cab)]
        out += ["| " + " | ".join("" if x is None else str(x) for x in l) + " |" for l in linhas]
        return "\n".join(out)

    md = [f"# Relatório de execução {obs.id_execucao}", "",
          "> Gerado pelo robô. Dados de lote SIMULADOS; portal SIMULADO. " + contexto.get("modo_iot_texto", ""), "",
          f"- Início: {contexto.get('inicio')} · fim: {contexto.get('fim')} · duração total: "
          f"{contexto.get('duracao_total_s')} s",
          f"- Entrada: `{contexto.get('arquivo_lotes')}` · IoT: {contexto.get('iot_resumo')}",
          f"- Modelo: {contexto.get('modelo')} · limiar de confiança {contexto.get('limiar_confianca')}",
          f"- Portal: {contexto.get('portal')}", "",
          "## Resumo", "",
          tab(["lotes no arquivo", "tratados", "processado", "revisão humana", "falha", "duplicados ignorados",
               "não entregues", "taxa de automação", "taxa de revisão", "taxa de erros"],
              [[resumo["lotes_no_arquivo"], tratados, cont["processado"], cont["revisao_humana"], cont["falha"],
                cont["ignorado_duplicado"], cont["ignorado_nao_entregue"], resumo["taxa_automacao"],
                resumo["taxa_revisao_humana"], resumo["taxa_erros"]]]), "",
          f"Tempo de ciclo por lote (T3 a T10): {rel['tempo_de_ciclo_lote_ms']}", "",
          "## Tarefas do BPMN (tempo e taxa de erros)", "",
          tab(["tarefa", "nome", "execuções", "erros", "taxa de erros", "média ms", "mín ms", "máx ms", "motivos de erro"],
              [[k, v["nome"], v["execucoes"], v["erros"], v["taxa_erros"], v["media_ms"], v["min_ms"], v["max_ms"],
                ", ".join(f"{m}: {n}" for m, n in v["motivos_erro"].items())] for k, v in tarefas.items()]), "",
          "## Gateways (caminho tomado)", "",
          tab(["gateway", "saídas"], [[g, ", ".join(f"{s}: {n}" for s, n in v.items())] for g, v in rel["gateways"].items()]), "",
          "## Lotes", "",
          tab(["#", "lote_id", "status", "motivo", "CO₂ evitado (kg CO₂eq)", "pontos", "Selo Verde ESG", "protocolo"],
              [[r["indice"], r.get("lote_id") or "(vazio)", r["status"], ", ".join(r.get("motivo", [])),
                r.get("co2_evitado_kg_co2eq"), r.get("pontos"), r.get("selo_verde_esg"), r.get("protocolo")]
               for r in resultados]), "",
          f"## Falhas tratadas ({len(obs.falhas_tratadas)})", "",
          tab(["falha", "lote", "motivo", "caminho seguro"],
              [[f["falha"], f["lote_id"], f["motivo"], f["caminho_seguro"]] for f in obs.falhas_tratadas])
          if obs.falhas_tratadas else "(nenhuma)", ""]
    cg = rel["conferencia_gabarito"]
    if cg:
        md += [f"## Conferência com o gabarito: {cg['acertos']} de {cg['n_registros']} registros "
               f"({cg['acertos_lotes_demonstracao']} de {cg['n_lotes_demonstracao']} lotes de demonstração)", "",
               tab(["#", "lote_id", "caso", "esperado", "obtido", "motivo esperado contém", "acerto"],
                   [[l["indice"], l["lote_id"] or "(vazio)", l["caso"], l["esperado"], l["obtido"],
                     ", ".join(l["motivo_esperado_contem"]), "sim" if l["acerto"] else "NÃO"] for l in cg["linhas"]]), ""]
    md += ["Custo por processo: não medido (sem custo real).", ""]
    pm = pasta / f"relatorio_{obs.id_execucao}.md"
    pm.write_text("\n".join(md), encoding="utf-8")
    return pj, pm
