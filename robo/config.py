"""Parâmetros, segredos e caminhos (tema A: arquivos e pastas)."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import dotenv_values

BASE = Path(__file__).resolve().parent.parent  # 05_ENTREGAVEIS/AIPA
SEGREDOS_OBRIGATORIOS = ("PORTAL_USUARIO", "PORTAL_SENHA", "PORTAL_API_TOKEN")


def carregar_json(caminho: Path) -> dict:
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def _converter(valor: str):
    """Converte o texto de --param CHAVE=VALOR para o tipo certo (json quando possível)."""
    try:
        return json.loads(valor)
    except json.JSONDecodeError:
        return valor


def carregar_parametros(overrides: list[str] | None = None) -> dict:
    p = carregar_json(BASE / "config" / "parametros.json")
    for item in overrides or []:
        chave, _, valor = item.partition("=")
        p[chave.strip()] = _converter(valor.strip())
    return p


def carregar_segredos(env_arquivo: Path | None = None) -> dict:
    """Lê o .env sem jogar os valores em os.environ (o portal lê o próprio .env)."""
    caminho = Path(env_arquivo) if env_arquivo else BASE / ".env"
    if not caminho.exists():
        return {}
    return {k: v for k, v in dotenv_values(caminho).items() if v is not None}


def agora(fuso: str = "America/Sao_Paulo") -> datetime:
    return datetime.now(ZoneInfo(fuso)).replace(microsecond=0)


@dataclass
class Caminhos:
    trabalho: Path
    params: dict = field(default_factory=dict)

    def __post_init__(self):
        self.trabalho = Path(self.trabalho)

    def _rel(self, chave: str) -> Path:
        v = Path(self.params[chave])
        return v if v.is_absolute() else self.trabalho / v

    @property
    def arquivo_lotes(self) -> Path:
        return self._rel("ARQUIVO_LOTES")

    @property
    def pasta_iot(self) -> Path:
        return self._rel("PASTA_IOT")

    @property
    def arquivo_decisoes(self) -> Path:
        return self._rel("ARQUIVO_DECISOES")

    @property
    def modelo(self) -> Path:
        v = Path(self.params["MODELO"])
        return v if v.is_absolute() else BASE / v

    @property
    def metadados_modelo(self) -> Path:
        v = Path(self.params["METADADOS_MODELO"])
        return v if v.is_absolute() else BASE / v

    @property
    def gabarito_demo(self) -> Path:
        v = Path(self.params["GABARITO_DEMO"])
        return v if v.is_absolute() else BASE / v

    @property
    def saida(self) -> Path:
        return self.trabalho / "saida"

    @property
    def estado_db(self) -> Path:
        return self.saida / "estado.db"

    @property
    def portal_db(self) -> Path:
        if self.trabalho.resolve() == BASE.resolve():
            return BASE / "portal_simulado" / "portal.db"
        return self.trabalho / "portal.db"

    def sub(self, nome: str) -> Path:
        return self.saida / nome

    PASTAS_SAIDA = ("termos", "ct04", "ct05", "revisao", "relatorios", "logs", "quarentena", "prints", "backup")

    def criar_pastas(self):
        for n in self.PASTAS_SAIDA:
            os.makedirs(self.sub(n), exist_ok=True)
