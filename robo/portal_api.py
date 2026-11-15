"""Webservice REST do portal SIMULADO (tema F, requests): health, confirmação e contingência.

Timeout em toda chamada; retry com espera exponencial só para erro transitório (conexão, timeout, 5xx,
JSON inválido); nunca para 4xx. O token vem do .env e nunca vai para o log.
"""
from __future__ import annotations

import time

import requests

from .observabilidade import FalhaTarefa


class ClienteAPI:
    def __init__(self, url: str, token: str, timeout: float, tentativas: int, espera_base: float, obs=None):
        self.url = url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self.tentativas = tentativas
        self.espera_base = espera_base
        self.obs = obs
        self.esperas_feitas: list[float] = []

    def _log(self, nivel, lote_id, msg):
        if self.obs:
            getattr(self.obs, nivel)("T9", lote_id, msg)

    def health(self, tentativas: int | None = None, elemento: str = "T1") -> bool:
        n = tentativas or self.tentativas
        for i in range(n):
            try:
                r = requests.get(f"{self.url}/health", timeout=self.timeout)
                if r.status_code == 200 and r.json().get("status") == "ok":
                    return True
            except (requests.RequestException, ValueError) as e:
                if self.obs:
                    self.obs.aviso(elemento, None, f"health tentativa {i + 1}/{n} falhou: {type(e).__name__}")
            if i < n - 1:
                espera = self.espera_base * (2 ** i)
                self.esperas_feitas.append(espera)
                time.sleep(espera)
        return False

    def _chamar(self, metodo: str, caminho: str, lote_id: str, motivo_esgotado: str, **kw):
        ultimo = None
        for i in range(self.tentativas):
            try:
                r = requests.request(metodo, f"{self.url}{caminho}", timeout=self.timeout,
                                     headers={"X-API-Token": self.token}, **kw)
                if r.status_code >= 500:
                    raise requests.HTTPError(f"HTTP {r.status_code}")
                if r.status_code in (401, 403):
                    raise FalhaTarefa("credenciais_invalidas", "token da API recusado")
                try:
                    corpo = r.json()
                except ValueError:
                    raise requests.HTTPError("JSON inválido na resposta")
                return r.status_code, corpo
            except requests.Timeout as e:
                ultimo = ("portal_timeout", e)
            except requests.ConnectionError as e:
                ultimo = ("portal_indisponivel", e)
            except requests.HTTPError as e:
                ultimo = (motivo_esgotado, e)
            self._log("aviso", lote_id, f"API {metodo} {caminho} tentativa {i + 1}/{self.tentativas} falhou: "
                                        f"{type(ultimo[1]).__name__}: {ultimo[1]}"[:200])
            if i < self.tentativas - 1:
                espera = self.espera_base * (2 ** i)
                self.esperas_feitas.append(espera)
                time.sleep(espera)
        raise FalhaTarefa(ultimo[0], f"{self.tentativas} tentativas esgotadas")

    def consultar(self, lote_id: str) -> dict | None:
        """Confirmação do lançamento. None se o portal não tem o lote (404)."""
        st, corpo = self._chamar("GET", f"/api/lancamentos/{lote_id}", lote_id, "confirmacao_api_falhou")
        if st == 404:
            return None
        return corpo

    def lancar(self, dados: dict) -> str:
        """Contingência (F10): lança por API quando o navegador não inicia. 409 = já lançado."""
        st, corpo = self._chamar("POST", "/api/lancamentos", dados["lote_id"], "confirmacao_api_falhou", json=dados)
        if st in (200, 201, 409):
            return corpo["protocolo"]
        raise FalhaTarefa("confirmacao_api_falhou", f"HTTP {st}")

    def resumo(self) -> dict:
        st, corpo = self._chamar("GET", "/api/resumo", None, "confirmacao_api_falhou")
        return corpo
