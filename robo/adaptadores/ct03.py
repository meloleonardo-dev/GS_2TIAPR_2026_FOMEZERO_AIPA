"""Adaptador do lote de doação (CT-03, FEMD -> AIPA).

Nomes = 'modelo de aplicação' proposto pelo Erick v1.0, NÃO confirmado (PEN-001): o mapa fica em
config/mapa_campos_ct03.json. Converte vírgula decimal e mantém null como None (nunca 0).
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path


class EntradaIlegivel(Exception):
    pass


def ler_arquivo(caminho: Path) -> list[dict]:
    """Lê o JSON exportado. Aceita {"lotes": [...]} ou uma lista. Ausente -> FileNotFoundError."""
    if not os.path.exists(caminho):  # aula rpa_ia_arquivos p. 21
        raise FileNotFoundError(str(caminho))
    try:
        with open(caminho, encoding="utf-8") as f:
            dados = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise EntradaIlegivel(f"{type(e).__name__}: {e}") from e
    lotes = dados.get("lotes") if isinstance(dados, dict) else dados
    if not isinstance(lotes, list):
        raise EntradaIlegivel("estrutura inesperada: esperado {'lotes': [...]} ou lista")
    return lotes


def numero(v):
    if v is None or v == "":
        return None
    if isinstance(v, bool):
        raise ValueError("booleano não é número")
    if isinstance(v, (int, float)):
        return float(v)
    return float(str(v).strip().replace(",", "."))


def data_iso(v):
    if v in (None, ""):
        return None
    return datetime.fromisoformat(str(v).replace("Z", "+00:00"))


def hash_registro(registro: dict) -> str:
    return hashlib.sha256(json.dumps(registro, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def adaptar(registro: dict, mapa: dict) -> tuple[dict, list[str]]:
    """Retorna (lote interno, campos com erro de conversão). O bruto vai em lote['_bruto']."""
    campos = mapa["campos"]
    lote, erros = {}, []
    for interno, externo in campos.items():
        lote[interno] = registro.get(externo) if isinstance(registro, dict) else None
    for c in ("quantidade_disponibilizada_kg", "quantidade_recebida_kg", "quantidade_aproveitada_kg"):
        try:
            lote[c] = numero(lote[c])
        except (TypeError, ValueError):
            erros.append(c)
    try:
        lote["_entrega_dt"] = data_iso(lote["entrega_confirmada_em"])
    except (TypeError, ValueError):
        lote["_entrega_dt"] = None
        erros.append("entrega_confirmada_em")
    for c in ("lote_id", "doador_id", "beneficiario_id", "status_logistico"):
        if isinstance(lote.get(c), str):
            lote[c] = lote[c].strip()
    # acréscimos da integração com o FEMD (opcionais): divergências marcadas e resumo da triagem visual
    div = lote.get("divergencias_informadas")
    if div is None:
        lote["divergencias_informadas"] = []
    elif isinstance(div, list) and all(isinstance(d, str) for d in div):
        lote["divergencias_informadas"] = [d.strip() for d in div if d.strip()]
    else:
        lote["divergencias_informadas"] = []
        erros.append("divergencias_informadas")
    tri = lote.get("triagem_visual")
    if tri is not None and not isinstance(tri, dict):
        lote["triagem_visual"] = None
        erros.append("triagem_visual")
    lote["_bruto"] = registro
    lote["_hash"] = hash_registro(registro) if isinstance(registro, dict) else None
    return lote, erros
