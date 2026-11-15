import json
import re
import secrets
import shutil
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from portal_simulado.app import criar_app  # noqa: E402
from robo.config import carregar_parametros  # noqa: E402

# credenciais descartáveis geradas a cada sessão de testes (nenhuma senha fixa no código)
SEGREDOS_TESTE = {"PORTAL_USUARIO": "usuario_teste", "PORTAL_SENHA": secrets.token_urlsafe(12),
                  "PORTAL_API_TOKEN": secrets.token_urlsafe(16), "PORTAL_CHAVE_SESSAO": secrets.token_hex(16)}


@pytest.fixture
def params():
    p = carregar_parametros()
    p["ESPERA_BASE_S"] = 0.01
    return p


class APIFalsa:
    """Mesma interface do ClienteAPI, mas falando com o portal simulado pelo test_client do Flask."""

    def __init__(self, app):
        self.c = app.test_client()
        self.h = {"X-API-Token": SEGREDOS_TESTE["PORTAL_API_TOKEN"]}

    def health(self, *a, **k):
        return self.c.get("/health").status_code == 200

    def consultar(self, lote_id):
        r = self.c.get(f"/api/lancamentos/{lote_id}", headers=self.h)
        return None if r.status_code == 404 else r.get_json()

    def lancar(self, dados):
        return self.c.post("/api/lancamentos", json=dados, headers=self.h).get_json()["protocolo"]

    def resumo(self):
        return self.c.get("/api/resumo", headers=self.h).get_json()


class LancadorFormulario:
    """Preenche o mesmo formulário do portal (sem navegador): login + POST /lancamentos."""

    def __init__(self, app):
        self.c = app.test_client()
        self.c.post("/login", data={"usuario": SEGREDOS_TESTE["PORTAL_USUARIO"], "senha": SEGREDOS_TESTE["PORTAL_SENHA"]})

    def lancar(self, dados):
        html = self.c.post("/lancamentos", data=dados).get_data(as_text=True)
        return re.search(r'textContent = "(SIM-\d+)"', html).group(1)

    def fechar(self):
        pass


@pytest.fixture
def portal_app(tmp_path):
    return criar_app(db=tmp_path / "portal_teste.db", modo_falha="nenhum", segredos=SEGREDOS_TESTE)


@pytest.fixture
def trabalho(tmp_path):
    (tmp_path / "entrada" / "iot").mkdir(parents=True)
    shutil.copy2(BASE / "dados" / "sinteticos" / "lotes_demo.json", tmp_path / "entrada" / "lotes_entregues.json")
    for log in (BASE / "dados" / "iot_fisico").glob("*.log"):
        shutil.copy2(log, tmp_path / "entrada" / "iot" / log.name)
    return tmp_path


def ler_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))
