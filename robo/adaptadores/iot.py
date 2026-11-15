"""Adaptador das mensagens da IoT (log do mosquitto_sub: 'tópico JSON' por linha).

Chaves OBSERVADAS nos logs de 10 e 11/11/2026 (commit 4b09c42), confirmação pendente (PC-012).
Distingue ativação e normalização do alerta (as duas vêm com evento = quebra_cadeia_frio).
Preserva valor bruto, origem (nunca inferida), arquivo e linha. Não usa temp_c para decidir nada.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


def _ts(v):
    if not v:
        return None
    try:
        dt = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def normalizar(topico: str, payload: dict, mapa: dict, fonte: str, linha: int, bruto: str) -> dict:
    ch = mapa["chaves"]
    g = lambda k: payload.get(ch[k])  # noqa: E731
    sufixo = topico.rsplit("/", 1)[-1].lower()
    tipo_base = mapa["sufixos_topico"].get(sufixo, "desconhecido")
    estado_bruto, evento_bruto = g("estado"), g("evento")
    estado = str(estado_bruto).lower() if estado_bruto is not None else None
    evento = str(evento_bruto).lower() if evento_bruto is not None else None
    if tipo_base == "alerta":
        if estado == "normalizado":
            tipo, situacao = "alerta_normalizacao", "normalizacao"
        elif g("duracao_acima_s") is not None or g("severidade") is not None:
            tipo, situacao = "alerta_ativacao", "ativacao"
        else:
            tipo, situacao = "alerta_desconhecido", "desconhecido"
    elif tipo_base == "telemetria":
        tipo = "telemetria"
        if estado is not None:
            situacao = mapa["valores_estado"].get(estado, "desconhecido")
        elif evento is not None:
            situacao = {"quebra_cadeia_frio": "ativacao", "normal": "normal"}.get(evento, "desconhecido")
        else:
            situacao = "desconhecido"
    else:
        tipo, situacao = tipo_base, None  # status, ack: ignorados
    return {
        "lote_id": g("lote_id"), "device_id": g("device_id"), "seq": g("seq"), "ts": g("ts"),
        "ts_valido": g("ts_valido"), "temp_c": g("temp_c"), "limite_c": g("limite_c"),
        "duracao_acima_s": g("duracao_acima_s"), "severidade": g("severidade"),
        "tipo_mensagem": tipo, "evento_bruto": evento_bruto, "estado_bruto": estado_bruto,
        "situacao_termica": situacao, "origem": g("origem"),
        "fonte_arquivo": fonte, "linha": linha, "payload_raw": bruto,
    }


def ler_pasta(pasta: Path, mapa: dict) -> dict:
    """Lê todos os *.log da pasta. Linha quebrada é registrada e ignorada, sem parar a leitura."""
    pasta = Path(pasta)
    arquivos = sorted(pasta.glob("*.log")) if pasta.exists() else []
    mensagens, invalidas = [], []
    for arq in arquivos:
        with open(arq, encoding="utf-8") as f:
            for n, texto in enumerate(f, start=1):
                texto = texto.strip()
                if not texto:
                    continue
                topico, _, bruto = texto.partition(" ")
                try:
                    payload = json.loads(bruto)
                    if not isinstance(payload, dict):
                        raise ValueError("payload não é objeto")
                except ValueError as e:
                    invalidas.append({"fonte_arquivo": arq.name, "linha": n, "erro": f"{type(e).__name__}"})
                    continue
                mensagens.append(normalizar(topico, payload, mapa, arq.name, n, bruto))
    return {"disponivel": bool(arquivos), "arquivos": [a.name for a in arquivos], "mensagens": mensagens,
            "linhas_invalidas": invalidas}


def avaliar_lote(lote_id: str, entrega_dt: datetime | None, fonte: dict, origens_aceitas: list[str],
                 janela_horas: float) -> dict:
    """Resumo da IoT para um lote no período do transporte (janela antes da entrega)."""
    msgs = [m for m in fonte["mensagens"] if m["lote_id"] == lote_id
            and m["tipo_mensagem"] in ("telemetria", "alerta_ativacao", "alerta_normalizacao", "alerta_desconhecido")]
    aceitas = [m for m in msgs if m["origem"] in origens_aceitas]
    ignoradas = [m for m in msgs if m["origem"] not in origens_aceitas and m["tipo_mensagem"] != "alerta_normalizacao"]
    fim = entrega_dt.astimezone(timezone.utc) if entrega_dt else None
    inicio = fim - timedelta(hours=janela_horas) if fim else None

    def no_periodo(m):
        t = _ts(m["ts"])
        if t is None or m.get("ts_valido") is False or fim is None:
            return True  # lado seguro
        return inicio <= t <= fim

    periodo = [m for m in aceitas if no_periodo(m)]
    ativacoes = [m for m in periodo if m["situacao_termica"] == "ativacao"]
    desconhecidos = [m for m in periodo if m["situacao_termica"] == "desconhecido"]
    normalizacoes = [m for m in msgs if m["tipo_mensagem"] == "alerta_normalizacao" and no_periodo(m)]
    origens = sorted({m["origem"] for m in aceitas if m["origem"]})
    return {
        "monitorado": bool(aceitas), "ativacao_aceita": bool(ativacoes), "desconhecido": bool(desconhecidos),
        "n_mensagens_lote": len(msgs), "n_aceitas_no_periodo": len(periodo), "n_ignoradas_por_origem": len(ignoradas),
        "n_normalizacoes_no_periodo": len(normalizacoes),
        "ativacoes": [{k: m[k] for k in ("tipo_mensagem", "seq", "ts", "origem", "estado_bruto", "fonte_arquivo", "linha")}
                      for m in ativacoes],
        "desconhecidos": [{k: m[k] for k in ("seq", "ts", "estado_bruto", "evento_bruto", "fonte_arquivo", "linha")}
                          for m in desconhecidos],
        "origem": origens[0] if len(origens) == 1 else (origens or None),
        "janela": {"inicio_utc": inicio.isoformat() if inicio else None, "fim_utc": fim.isoformat() if fim else None},
    }
