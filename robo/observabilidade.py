"""Log, cronômetro por elemento do BPMN e checagem de recursos (tema G e H).

Cada linha de log: data | nível | id_execucao | elemento BPMN | lote_id | evento.
Nenhum segredo e nenhum texto livre do beneficiário vai para o log.
"""
from __future__ import annotations

import functools
import logging
import re
import shutil
import sys
import time
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path

import psutil

FORMATO = "%(asctime)s | %(levelname)s | %(id_execucao)s | %(elemento)s | %(lote_id)s | %(message)s"

_RE_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
_RE_CPF = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
_RE_FONE = re.compile(r"(\(?\d{2}\)?\s?)?9?\d{4}[-\s]?\d{4}\b")


def mascarar(texto: str | None) -> str | None:
    """Máscara de e-mail, CPF e telefone (precaução; os textos são sintéticos)."""
    if texto is None:
        return None
    t = _RE_EMAIL.sub("[email]", texto)
    t = _RE_CPF.sub("[cpf]", t)
    t = _RE_FONE.sub(lambda m: "[telefone]" if len(re.sub(r"\D", "", m.group())) >= 8 else m.group(), t)
    return t


class FalhaTarefa(Exception):
    """Falha de negócio ou técnica tratada dentro de uma tarefa BPMN."""

    def __init__(self, motivo: str, detalhe: str = ""):
        super().__init__(f"{motivo} {detalhe}".strip())
        self.motivo = motivo
        self.detalhe = detalhe


class _Contexto(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        extra = dict(self.extra)
        extra.update(kwargs.pop("extra", {}) or {})
        kwargs["extra"] = extra
        return msg, kwargs


def configurar_log(pasta_logs: Path, id_execucao: str) -> tuple[logging.Logger, Path]:
    pasta_logs.mkdir(parents=True, exist_ok=True)
    arquivo = pasta_logs / f"{id_execucao}.log"
    logger = logging.getLogger(f"robo.{id_execucao}")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    for h in list(logger.handlers):
        logger.removeHandler(h)
    fmt = logging.Formatter(FORMATO)
    fh = logging.FileHandler(arquivo, encoding="utf-8")
    fh.setFormatter(fmt)
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger, arquivo


class Observador:
    """Registra execuções de tarefas e saídas de gateways para o relatório (T12)."""

    def __init__(self, logger: logging.Logger, id_execucao: str):
        self.id_execucao = id_execucao
        self._logger = logger
        self.execucoes: list[dict] = []  # tarefa por lote
        self.gateways: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.trilhas: dict[str, list[str]] = defaultdict(list)
        self.falhas_tratadas: list[dict] = []
        self.inicio_lote: dict[str, float] = {}
        self.ciclo_lote: dict[str, float] = {}

    def log(self, nivel: int, elemento: str, lote_id: str | None, msg: str):
        self._logger.log(nivel, msg, extra={"id_execucao": self.id_execucao, "elemento": elemento,
                                             "lote_id": lote_id or "-"})

    def info(self, elemento, lote_id, msg):
        self.log(logging.INFO, elemento, lote_id, msg)

    def aviso(self, elemento, lote_id, msg):
        self.log(logging.WARNING, elemento, lote_id, msg)

    def erro(self, elemento, lote_id, msg):
        self.log(logging.ERROR, elemento, lote_id, msg)

    def critico(self, elemento, lote_id, msg):
        self.log(logging.CRITICAL, elemento, lote_id, msg)

    @contextmanager
    def tarefa(self, elemento: str, lote_id: str | None = None):
        """Cronometra uma tarefa BPMN. Exceção = execução com erro (relançada)."""
        chave = lote_id or "-"
        self.trilhas[chave].append(elemento)
        t0 = time.perf_counter()
        reg = {"elemento": elemento, "lote_id": chave, "resultado": "ok", "motivo": None}
        try:
            yield reg
        except FalhaTarefa as e:
            reg["resultado"] = "erro"
            reg["motivo"] = e.motivo
            raise
        except Exception as e:  # noqa: BLE001 - registrado e relançado
            reg["resultado"] = "erro"
            reg["motivo"] = f"excecao:{type(e).__name__}"
            raise
        finally:
            reg["duracao_ms"] = round((time.perf_counter() - t0) * 1000, 2)
            self.execucoes.append(reg)

    def gateway(self, elemento: str, lote_id: str | None, saida: str):
        chave = lote_id or "-"
        self.gateways[elemento][saida] += 1
        self.trilhas[chave].append(f"{elemento}:{saida}")
        self.info(elemento, lote_id, f"gateway -> {saida}")

    def falha(self, codigo: str, lote_id: str | None, motivo: str, caminho_seguro: str):
        self.falhas_tratadas.append({"falha": codigo, "lote_id": lote_id, "motivo": motivo,
                                     "caminho_seguro": caminho_seguro})

    def iniciar_lote(self, lote_id: str):
        self.inicio_lote[lote_id] = time.perf_counter()

    def fechar_lote(self, lote_id: str):
        if lote_id in self.inicio_lote:
            self.ciclo_lote[lote_id] = round((time.perf_counter() - self.inicio_lote[lote_id]) * 1000, 2)


def tarefa_bpmn(elemento: str):
    """Decorador: a função recebe `obs` e `lote_id` por palavra-chave e é cronometrada."""
    def deco(fn):
        @functools.wraps(fn)
        def envolvido(*args, obs: Observador, lote_id: str | None = None, **kwargs):
            with obs.tarefa(elemento, lote_id):
                return fn(*args, obs=obs, lote_id=lote_id, **kwargs)
        envolvido.elemento_bpmn = elemento
        return envolvido
    return deco


def recursos(caminho: Path) -> dict:
    """Disco livre e memória (psutil, aula rpa_ia_tasks p. 3 a 9)."""
    caminho = Path(caminho)
    alvo = caminho if caminho.exists() else caminho.anchor
    disco = psutil.disk_usage(str(alvo))
    mem = psutil.virtual_memory()
    return {
        "disco_livre_mb": round(disco.free / 1024 / 1024, 1),
        "disco_uso_pct": disco.percent,
        "memoria_disponivel_mb": round(mem.available / 1024 / 1024, 1),
        "memoria_uso_pct": mem.percent,
        "cpu_pct": psutil.cpu_percent(interval=0.1),
    }


def pasta_gravavel(pasta: Path) -> bool:
    try:
        pasta.mkdir(parents=True, exist_ok=True)
        teste = pasta / ".teste_escrita"
        teste.write_text("ok", encoding="utf-8")
        teste.unlink()
        return True
    except OSError:
        return False


def backup_estado(estado_db: Path, pasta_backup: Path, id_execucao: str) -> Path | None:
    """Backup do estado antes de gravar (shutil.make_archive, aula rpa_ia_tasks p. 32)."""
    if not estado_db.exists():
        return None
    pasta_backup.mkdir(parents=True, exist_ok=True)
    base = pasta_backup / f"estado_{id_execucao}"
    return Path(shutil.make_archive(str(base), "zip", root_dir=estado_db.parent, base_dir=estado_db.name))
