"""Teste web (Selenium + pytest, aula 01_hyperautomation p. 17): portal SIMULADO numa porta de teste."""
import os
import subprocess
import sys
import time

import pytest
import requests

from conftest import BASE, SEGREDOS_TESTE
from robo.observabilidade import FalhaTarefa
from robo.portal_api import ClienteAPI
from robo.portal_selenium import LancadorSelenium, NavegadorIndisponivel

PORTA = 5071  # 5060/5061 são portas bloqueadas pelo Chromium (SIP)
URL = f"http://127.0.0.1:{PORTA}"


@pytest.fixture(scope="module")
def portal(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("portal")
    env_arq = pasta / "teste.env"
    env_arq.write_text("\n".join(f"{k}={v}" for k, v in SEGREDOS_TESTE.items()), encoding="utf-8")
    env = dict(os.environ, PORTAL_DB=str(pasta / "p.db"), PORTAL_PORTA=str(PORTA), PORTAL_ENV_ARQUIVO=str(env_arq),
               PORTAL_MODO_FALHA="nenhum")
    proc = subprocess.Popen([sys.executable, str(BASE / "portal_simulado" / "app.py")], env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            if requests.get(f"{URL}/health", timeout=1).ok:
                break
        except requests.RequestException:
            time.sleep(0.3)
    yield pasta
    proc.terminate()
    proc.wait(timeout=5)


def dados(lote):
    return {"lote_id": lote, "doador_id": "DOADOR-T", "kg": "12.00", "co2": "30.48", "pontos": 120, "selo": "Bronze"}


def test_login_lancamento_e_protocolo(portal):
    sel = LancadorSelenium(URL, SEGREDOS_TESTE["PORTAL_USUARIO"], SEGREDOS_TESTE["PORTAL_SENHA"], portal / "prints",
                           timeout=10, headless=True, espera_base=0.1)
    try:
        protocolo = sel.lancar(dados("LOTE-SEL-1"))
    finally:
        sel.fechar()
    assert protocolo.startswith("SIM-")
    api = ClienteAPI(URL, SEGREDOS_TESTE["PORTAL_API_TOKEN"], 5, 2, 0.1)
    c = api.consultar("LOTE-SEL-1")
    assert c["protocolo"] == protocolo and c["pontos"] == 120 and c["meio"] == "selenium"
    assert len(list((portal / "prints").glob("*.png"))) == 3


def test_senha_errada_sem_retry(portal):
    sel = LancadorSelenium(URL, SEGREDOS_TESTE["PORTAL_USUARIO"], "errada", portal / "prints2", headless=True,
                           espera_base=0.1)
    try:
        with pytest.raises(FalhaTarefa) as e:
            sel.lancar(dados("LOTE-SEL-2"))
    finally:
        sel.fechar()
    assert e.value.motivo == "credenciais_invalidas"


def test_api_duplicado_409_e_token_invalido(portal):
    api = ClienteAPI(URL, SEGREDOS_TESTE["PORTAL_API_TOKEN"], 5, 2, 0.1)
    p1 = api.lancar(dados("LOTE-API-1"))
    p2 = api.lancar(dados("LOTE-API-1"))  # 409 -> mesmo protocolo, sem novo registro
    assert p1 == p2
    assert api.resumo()["total_lancamentos"] == 2  # LOTE-SEL-1 + LOTE-API-1
    ruim = ClienteAPI(URL, "token-errado", 5, 2, 0.1)
    with pytest.raises(FalhaTarefa) as e:
        ruim.consultar("LOTE-API-1")
    assert e.value.motivo == "credenciais_invalidas"


def test_navegador_inexistente_vira_contingencia(tmp_path):
    sel = LancadorSelenium(URL, "u", "s", tmp_path / "prints", navegador="C:/nao_existe/msedge.exe")
    with pytest.raises(NavegadorIndisponivel):
        sel.lancar(dados("LOTE-X"))
