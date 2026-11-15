"""Saídas para o grupo (tema A): CT-04 (FEMD), CT-05 (GABA e CQIA) e fila de revisão humana."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from . import calculos

AVISO = ("Dados simulados. Não atesta que o alimento é seguro para consumo. CO₂ evitado é estimativa. Pontos e Selo "
         "Verde ESG: regra de demonstração, reconhecimento interno, não certificação.")


def ct04_base(lote: dict, params: dict, id_execucao: str, agora: str) -> dict:
    return {
        "versao_contrato": "ct04-v0", "simulado": True,
        "lote_id": lote.get("lote_id") or None, "doador_id": lote.get("doador_id") or None,
        "status": None, "motivo": [], "revisao": None,
        "quantidade_recebida_kg": None, "origem_quantidade": None, "co2_evitado_kg_co2eq": None,
        "metodologia_carbono": calculos.metodologia(params),
        "pontos": None, "kg_acumulado_doador": None, "pontos_acumulados_doador": None,
        "selo_verde_esg": None, "selo_situacao": "nao_calculado", "regras_recompensa": calculos.regras_recompensa(params),
        "termo_doacao_id": None, "termo_doacao_arquivo": None,
        "portal": {"lancado": False, "protocolo": None, "confirmado_api": False, "meio": None},
        "ia": {"ocorrencia": None, "confianca": None, "kg_extraido": None, "alerta_iot": None, "iot_monitorado": None,
               "iot_origem": None, "alerta_ct03": None, "modelo": None},
        "aviso": AVISO, "processado_em": agora, "id_execucao": id_execucao,
    }


def gravar_json(caminho: Path, dados) -> Path:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    return caminho


def gravar_ct04(pasta: Path, ct04: dict, indice: int) -> Path:
    nome = ct04["lote_id"] or f"SEM_ID_indice{indice}"
    return gravar_json(pasta / f"{nome}.json", ct04)


def gravar_ct04_agregado(pasta: Path, todos: list[dict]) -> Path:
    return gravar_json(pasta / "ct04_lotes.json", {"versao_contrato": "ct04-v0", "simulado": True, "lotes": todos})


def gravar_ct05(pasta: Path, lotes_estado: list[dict], resumo_execucao: dict, params: dict, id_execucao: str,
                agora: str, entradas: dict) -> tuple[Path, Path]:
    cts = [l["ct04"] for l in lotes_estado if l and l.get("ct04")]
    proc = [c for c in cts if c["status"] == "processado"]
    massa = round(sum(c["quantidade_recebida_kg"] for c in proc), 3)
    por_doador: dict[str, float] = {}
    for c in cts:
        por_doador.setdefault(c["doador_id"], 0.0)
        if c["status"] == "processado":
            por_doador[c["doador_id"]] += c["quantidade_recebida_kg"]
    ranking = []
    for d, kg in sorted(por_doador.items(), key=lambda x: -x[1]):
        selo, sit = calculos.selo(kg, params)
        ranking.append({"doador_id": d, "kg_acumulado": round(kg, 3), "pontos_acumulados": sum(
            c["pontos"] for c in proc if c["doador_id"] == d), "selo_verde_esg": selo, "selo_situacao": sit})
    ind = {
        "versao_contrato": "ct05-v0", "simulado": True, "gerado_em": agora, "id_execucao": id_execucao,
        "massa_recebida_validada_kg": massa,
        "co2_evitado_estimado_kg_co2eq": calculos.co2_evitado(massa, params) if proc else None,
        "metodologia_carbono": calculos.metodologia(params),
        "lotes": {"processado": len(proc), "revisao_humana": sum(c["status"] == "revisao_humana" for c in cts),
                  "falha": sum(c["status"] == "falha" for c in cts),
                  "ignorados_nao_entregues": resumo_execucao.get("ignorados_nao_entregues", 0)},
        "taxa_automacao": resumo_execucao.get("taxa_automacao"),
        "taxa_revisao_humana": resumo_execucao.get("taxa_revisao_humana"),
        "taxa_erros": resumo_execucao.get("taxa_erros"),
        "_nota_taxas": "contagens e massa = estado acumulado do robô; taxas = desta execução (relatório BPMN)",
        "ranking_esg": ranking,
        "nao_calculados": {"massa_aproveitada_kg": None, "beneficiarios_atendidos": None, "refeicoes": None,
                           "desperdicio_evitado_kg": None,
                           "_nota": "Sem base de dados ou metodologia (arquivo de parâmetros do Erick, §11)."},
        "aviso": AVISO,
    }
    p1 = gravar_json(pasta / "indicadores.json", ind)
    p2 = pasta / "historico_entregas.csv"
    cols = ["lote_id", "doador_id", "beneficiario_id", "beneficiario_tipo", "entrega_confirmada_em",
            "quantidade_disponibilizada_kg", "quantidade_recebida_kg", "status", "motivo"]
    with open(p2, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(cols)
        for c in cts:
            e = entradas.get(c["lote_id"], {})
            w.writerow([c["lote_id"], c["doador_id"], e.get("beneficiario_id") or "", e.get("beneficiario_tipo") or "",
                        e.get("entrega_confirmada_em") or "", e.get("quantidade_disponibilizada_kg") or "",
                        "" if c["quantidade_recebida_kg"] is None else c["quantidade_recebida_kg"], c["status"],
                        ",".join(c["motivo"])])
    return p1, p2


COLUNAS_FILA = ["lote_id", "doador_id", "motivos", "ocorrencia_prevista", "confianca", "kg_extraido",
                "kg_cadastrado", "alerta_iot", "texto_confirmacao_mascarado", "decisao", "kg_aprovado", "revisor"]


def gravar_fila_revisao(pasta: Path, linhas: list[dict]) -> Path:
    """CSV ';' UTF-8 com BOM (abre no Excel). O operador preenche decisao/kg_aprovado/revisor (código)."""
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / "fila_revisao.csv"
    with open(caminho, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUNAS_FILA, delimiter=";")
        w.writeheader()
        for l in linhas:
            w.writerow({k: l.get(k, "") for k in COLUNAS_FILA})
    # cópia em Excel para leitura (openpyxl, aula 01_hyperautomation p. 11); a decisão volta pelo CSV
    import pandas as pd
    pd.DataFrame(linhas, columns=COLUNAS_FILA).to_excel(pasta / "fila_revisao.xlsx", index=False,
                                                        sheet_name="fila_revisao", engine="openpyxl")
    return caminho


def ler_decisoes(caminho: Path) -> tuple[dict, list[str]]:
    """Lê entrada/decisoes_revisao.csv. Retorna ({lote_id: decisao}, avisos)."""
    if not caminho.exists():
        return {}, []
    import pandas as pd
    avisos, dec = [], {}
    df = pd.read_csv(caminho, sep=";", encoding="utf-8-sig", dtype=str, keep_default_na=False)
    for _, r in df.iterrows():
        d = (r.get("decisao") or "").strip().lower()
        if d not in ("aprovado", "reprovado"):
            continue
        kg = None
        if d == "aprovado":
            try:
                kg = float(str(r.get("kg_aprovado", "")).replace(",", "."))
                if kg <= 0:
                    raise ValueError
            except ValueError:
                avisos.append(f"{r['lote_id']}: aprovado sem kg_aprovado válido (decisão ignorada)")
                continue
        dec[r["lote_id"].strip()] = {"decisao": d, "kg_aprovado": kg, "revisor": (r.get("revisor") or "").strip()}
    return dec, avisos
