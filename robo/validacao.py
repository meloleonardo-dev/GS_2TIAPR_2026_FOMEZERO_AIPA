"""Validação do lote (T3) e quarentena do inválido (tema A: os/shutil/json)."""
from __future__ import annotations

import json
from pathlib import Path


def validar(lote: dict, erros_conversao: list[str], obrigatorios: list[str]) -> list[str]:
    """Lista de campos inválidos (vazia = válido). Ordem estável para o motivo."""
    erros: list[str] = []
    for c in obrigatorios:
        v = lote.get(c)
        if v is None or (isinstance(v, str) and not v.strip()):
            erros.append(c)
    erros += [c for c in erros_conversao if c not in erros]
    kg = lote.get("quantidade_disponibilizada_kg")
    if "quantidade_disponibilizada_kg" not in erros and (not isinstance(kg, float) or kg <= 0):
        erros.append("quantidade_disponibilizada_kg")
    rec = lote.get("quantidade_recebida_kg")
    if rec is not None and "quantidade_recebida_kg" not in erros and rec < 0:
        erros.append("quantidade_recebida_kg")
    if lote.get("simulado") is not True and "simulado" not in erros:
        erros.append("simulado")
    if lote.get("_entrega_dt") is None and "entrega_confirmada_em" not in erros:
        erros.append("entrega_confirmada_em")
    ordem = list(lote.keys())
    return sorted(set(erros), key=lambda c: ordem.index(c) if c in ordem else 99)


def quarentena(pasta: Path, indice: int, lote: dict, erros: list[str], id_execucao: str) -> Path:
    pasta.mkdir(parents=True, exist_ok=True)
    nome = (lote.get("lote_id") or f"SEM_ID_indice{indice}").replace("/", "_")
    destino = pasta / f"{id_execucao}_{nome}.json"
    with open(destino, "w", encoding="utf-8") as f:
        json.dump({"indice_no_arquivo": indice, "campos_invalidos": erros, "registro_bruto": lote.get("_bruto")},
                  f, ensure_ascii=False, indent=2)
    return destino
