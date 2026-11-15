"""Cenários de falha F1 a F11 para demonstração (cada um numa pasta de trabalho separada).

Todos SIMULADOS; nenhum toca portal real. A pasta é saida/cenarios/<nome>/ (fora do repositório).
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from .config import BASE

LOTES_PORTAL = ["LOTE-2026-0002", "LOTE-2026-0003"]  # subconjunto para os cenários de portal (mais rápidos)

CENARIOS = {
    "arquivo_ausente": {"falha": "F1", "descricao": "arquivo de lotes ausente", "lotes": None},
    "iot_ausente": {"falha": "F2", "descricao": "fonte da IoT ausente", "iot": "nenhuma"},
    "modelo_ausente": {"falha": "F3", "descricao": "modelo de IA ausente",
                       "params": ["MODELO=modelos/inexistente-v0.joblib"]},
    "iot_invalido": {"falha": "F4", "descricao": "IoT SIMULADA com linha JSON quebrada, valor não mapeado e alerta "
                                                 "simulado (execução separada da física)",
                     "iot": "simulada", "params": ['ORIGENS_IOT_ACEITAS=["simulador"]'],
                     "lotes": ["LOTE-2026-0003", "LOTE-2026-0005", "LOTE-2026-0006"]},
    "portal_fora": {"falha": "F6", "descricao": "portal fora do ar", "sem_portal": True, "lotes": LOTES_PORTAL},
    "portal_lento": {"falha": "F7", "descricao": "timeout (portal lento)", "portal_modo": "lento", "lotes": LOTES_PORTAL},
    "erro_api": {"falha": "F8", "descricao": "erro de API (HTTP 500)", "portal_modo": "erro_api", "lotes": LOTES_PORTAL},
    "json_invalido": {"falha": "F8", "descricao": "erro de API (JSON inválido)", "portal_modo": "json_invalido",
                      "lotes": LOTES_PORTAL[:1]},
    "credencial_invalida": {"falha": "F9", "descricao": "senha errada no login do portal", "senha_errada": True,
                            "lotes": LOTES_PORTAL},
    "navegador_indisponivel": {"falha": "F10", "descricao": "navegador/WebDriver não inicia -> contingência API",
                               "params": ["NAVEGADOR=C:/nao_existe/msedge.exe"], "lotes": LOTES_PORTAL},
    "disco_cheio": {"falha": "F11", "descricao": "disco abaixo do mínimo", "params": ["DISCO_MIN_LIVRE_MB=999999999"]},
}


def preparar(nome: str) -> tuple[Path, dict]:
    c = CENARIOS[nome]
    pasta = BASE / "saida" / "cenarios" / nome
    if pasta.exists():
        shutil.rmtree(pasta)
    (pasta / "entrada").mkdir(parents=True)
    demo = json.loads((BASE / "dados" / "sinteticos" / "lotes_demo.json").read_text(encoding="utf-8"))
    sel = c.get("lotes", "todos")
    if sel is not None:
        if sel != "todos":
            vistos, lotes = set(), []
            for l in demo["lotes"]:
                if l["lote_id"] in sel and l["lote_id"] not in vistos:
                    lotes.append(l)
                    vistos.add(l["lote_id"])
            demo["lotes"] = lotes
        demo["_aviso"] = f"SIMULADO. Cenário {nome} ({c['falha']}). " + demo["_aviso"]
        (pasta / "entrada" / "lotes_entregues.json").write_text(json.dumps(demo, ensure_ascii=False, indent=2),
                                                                encoding="utf-8")
    iot = c.get("iot", "fisica")
    if iot == "fisica":
        (pasta / "entrada" / "iot").mkdir()
        for log in sorted((BASE / "dados" / "iot_fisico").glob("*.log")):
            shutil.copy2(log, pasta / "entrada" / "iot" / log.name)
    elif iot == "simulada":
        (pasta / "entrada" / "iot").mkdir()
        shutil.copy2(BASE / "dados" / "cenarios" / "iot_simulado_invalido.log", pasta / "entrada" / "iot")
    return pasta, c
