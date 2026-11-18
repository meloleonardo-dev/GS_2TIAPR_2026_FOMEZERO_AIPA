"""Integração de _t11 com CT-04 e CT-05, sem portal ou banco real."""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from robo.config import carregar_parametros
from robo.processo import Robo
from robo.saidas import ct04_base


def test_t11_informa_registro_sem_id_no_resumo_da_execucao(tmp_path):
    parametros = carregar_parametros()
    execucao = "TESTE-T11"
    instante = "2026-11-17T00:00:00-03:00"

    def registro(lote_id, status, quantidade=None, pontos=None):
        dado = ct04_base(
            {
                "lote_id": lote_id,
                "doador_id": "DOADOR-TESTE",
            },
            parametros,
            execucao,
            instante,
        )
        dado.update(
            status=status,
            quantidade_recebida_kg=quantidade,
            pontos=pontos,
            motivo=[] if status == "processado" else ["dado_invalido"],
        )
        return dado

    processado = registro("TESTE-VALIDADO", "processado", 10.0, 100)
    falha_identificada = registro("TESTE-INVALIDO", "falha")
    falha_sem_id = registro(None, "falha")

    estado = [
        {"ct04": processado},
        {"ct04": falha_identificada},
    ]

    robo = Robo.__new__(Robo)
    robo.params = parametros
    robo.id_execucao = execucao
    robo.obs = MagicMock()
    robo.cam = SimpleNamespace(sub=lambda nome: tmp_path / nome)
    robo.banco = SimpleNamespace(todos=lambda: estado)
    robo.entradas = {}
    robo._textos = {}
    robo._sem_id = [falha_sem_id]

    resultados = [
        processado,
        falha_identificada,
        falha_sem_id,
        {"status": "duplicado"},
        {"status": "ignorado_nao_entregue"},
    ]

    robo._t11(resultados, {})

    ct04 = json.loads(
        (tmp_path / "ct04" / "ct04_lotes.json").read_text(encoding="utf-8")
    )
    ct05 = json.loads(
        (tmp_path / "ct05" / "indicadores.json").read_text(encoding="utf-8")
    )

    assert sum(lote["status"] == "falha" for lote in ct04["lotes"]) == 2
    assert ct05["lotes"]["falha"] == 1

    assert ct05["execucao"]["contagens"] == {
        "processado": 1,
        "revisao_humana": 0,
        "falha": 2,
        "total_tratados": 3,
        "registros_sem_id": 1,
    }

    assert ct05["execucao"]["id_execucao"] == execucao
    assert ct05["taxa_automacao"] == round(1 / 3, 4)
    assert ct05["taxa_erros"] == round(2 / 3, 4)
    assert ct05["lotes"]["ignorados_nao_entregues"] == 1
    assert ct05["massa_recebida_validada_kg"] == 10.0
    assert (tmp_path / "ct05" / "historico_entregas.csv").is_file()
