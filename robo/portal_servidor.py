"""Sobe e derruba o portal SIMULADO num subprocesso (o README roda com um comando só)."""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import requests

from .config import BASE


def no_ar(url: str, timeout: float = 1.0) -> bool:
    try:
        return requests.get(f"{url.rstrip('/')}/health", timeout=timeout).status_code == 200
    except requests.RequestException:
        return False


def iniciar(url: str, porta: int, db: Path, modo_falha: str = "nenhum", log: Path | None = None,
            espera_max_s: float = 15) -> subprocess.Popen | None:
    env = dict(os.environ)
    env.update({"PORTAL_DB": str(db), "PORTAL_MODO_FALHA": modo_falha, "PORTAL_PORTA": str(porta),
                "PORTAL_ENV_ARQUIVO": str(BASE / ".env")})
    saida = open(log, "a", encoding="utf-8") if log else subprocess.DEVNULL
    proc = subprocess.Popen([sys.executable, str(BASE / "portal_simulado" / "app.py")], env=env, stdout=saida,
                            stderr=subprocess.STDOUT, cwd=str(BASE))
    t0 = time.time()
    while time.time() - t0 < espera_max_s:
        if proc.poll() is not None:
            return None
        if no_ar(url):
            return proc
        time.sleep(0.3)
    parar(proc)
    return None


def parar(proc: subprocess.Popen | None):
    if proc and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
