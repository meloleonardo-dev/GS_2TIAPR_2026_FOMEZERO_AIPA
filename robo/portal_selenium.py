"""Automação web com Selenium (tema C): login e lançamento no portal SIMULADO.

Espera explícita (WebDriverWait) pelo protocolo, que aparece por JavaScript depois de um atraso.
Print de cada tela como evidência. Senha só do .env; nunca no log.
"""
from __future__ import annotations

import time
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .observabilidade import FalhaTarefa


class NavegadorIndisponivel(Exception):
    pass


class LancadorSelenium:
    def __init__(self, url, usuario, senha, pasta_prints: Path, timeout=10, headless=True, navegador="edge",
                 tentativas=3, espera_base=2, obs=None):
        self.url = url.rstrip("/")
        self._usuario = usuario
        self._senha = senha
        self.pasta_prints = Path(pasta_prints)
        self.timeout = timeout
        self.headless = headless
        self.navegador = navegador
        self.tentativas = tentativas
        self.espera_base = espera_base
        self.obs = obs
        self.driver = None
        self.logado = False
        self.credencial_recusada = False
        self.prints: list[str] = []

    def _iniciar(self):
        if self.driver:
            return
        try:
            if self.navegador == "chrome":
                op = webdriver.ChromeOptions()
            else:
                op = webdriver.EdgeOptions()
                if self.navegador not in ("edge",):
                    # cenário F10: navegador configurado não existe -> exceção real do Selenium
                    op.binary_location = str(Path(self.navegador))
            if self.headless:
                op.add_argument("--headless=new")
            op.add_argument("--window-size=1100,900")
            self.driver = webdriver.Chrome(options=op) if self.navegador == "chrome" else webdriver.Edge(options=op)
            self.driver.set_page_load_timeout(self.timeout)
        except WebDriverException as e:
            raise NavegadorIndisponivel(f"{type(e).__name__}: {str(e).splitlines()[0][:160]}") from e

    def _print(self, nome: str):
        self.pasta_prints.mkdir(parents=True, exist_ok=True)
        caminho = self.pasta_prints / f"{nome}.png"
        self.driver.save_screenshot(str(caminho))
        self.prints.append(str(caminho))

    def _login(self, lote_id: str):
        d = self.driver
        d.get(f"{self.url}/login")
        WebDriverWait(d, self.timeout).until(EC.presence_of_element_located((By.ID, "usuario")))
        d.find_element(By.ID, "usuario").send_keys(self._usuario)
        d.find_element(By.ID, "senha").send_keys(self._senha)
        self._print(f"{lote_id}_01_login")
        d.find_element(By.ID, "entrar").click()
        WebDriverWait(d, self.timeout).until(
            lambda drv: drv.find_elements(By.ID, "erro-login") or drv.find_elements(By.ID, "form-lancamento"))
        if d.find_elements(By.ID, "erro-login"):
            self._print(f"{lote_id}_01b_login_recusado")
            self.credencial_recusada = True
            raise FalhaTarefa("credenciais_invalidas", "login recusado pelo portal (sem retry)")
        self.logado = True

    def _uma_tentativa(self, dados: dict) -> str:
        d = self.driver
        if not self.logado:
            self._login(dados["lote_id"])
        d.get(f"{self.url}/lancamentos/novo")
        if not d.find_elements(By.ID, "form-lancamento"):  # sessão expirou
            self.logado = False
            self._login(dados["lote_id"])
            d.get(f"{self.url}/lancamentos/novo")
        WebDriverWait(d, self.timeout).until(EC.presence_of_element_located((By.ID, "form-lancamento")))
        for campo in ("lote_id", "doador_id", "kg", "co2", "pontos"):
            el = d.find_element(By.ID, campo)
            el.clear()
            el.send_keys(str(dados[campo]))
        from selenium.webdriver.support.ui import Select
        Select(d.find_element(By.ID, "selo")).select_by_value(dados.get("selo") or "")
        self._print(f"{dados['lote_id']}_02_formulario")
        d.find_element(By.ID, "enviar").click()
        el = WebDriverWait(d, self.timeout).until(
            lambda drv: (e := drv.find_element(By.ID, "protocolo")) and e.text.strip() and e)
        protocolo = el.text.strip()
        self._print(f"{dados['lote_id']}_03_protocolo")
        return protocolo

    def lancar(self, dados: dict) -> str:
        if self.credencial_recusada:
            raise FalhaTarefa("credenciais_invalidas", "login já recusado nesta execução")
        self._iniciar()
        ultimo = None
        for i in range(self.tentativas):
            try:
                return self._uma_tentativa(dados)
            except FalhaTarefa:
                raise
            except TimeoutException as e:
                ultimo = ("portal_timeout", e)
            except WebDriverException as e:
                ultimo = ("portal_indisponivel", e)
            if self.obs:
                self.obs.aviso("T9", dados["lote_id"], f"Selenium tentativa {i + 1}/{self.tentativas} falhou: "
                                                       f"{type(ultimo[1]).__name__}")
            if i < self.tentativas - 1:
                time.sleep(self.espera_base * (2 ** i))
        raise FalhaTarefa(ultimo[0], "tentativas do Selenium esgotadas")

    def fechar(self):
        if self.driver:
            try:
                self.driver.quit()
            finally:
                self.driver = None
