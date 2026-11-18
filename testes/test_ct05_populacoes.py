"""Regressão CT-05: estado acumulado e execução são populações distintas."""

import json

from robo.config import carregar_parametros
from robo.saidas import gravar_ct05


def estado_exemplo():
    return [
        {
            "ct04": {
                "lote_id": "TESTE-VALIDADO",
                "doador_id": "DOADOR-TESTE",
                "status": "processado",
                "quantidade_recebida_kg": 10.0,
                "pontos": 100,
                "motivo": [],
            }
        },
        {
            "ct04": {
                "lote_id": "TESTE-INVALIDO",
                "doador_id": "DOADOR-TESTE",
                "status": "falha",
                "quantidade_recebida_kg": None,
                "pontos": None,
                "motivo": ["dado_invalido:quantidade_disponibilizada_kg"],
            }
        },
    ]


def gerar_indicadores(pasta, resumo):
    parametros = carregar_parametros()
    # Parâmetros explícitos para o resultado deste teste.
    parametros["FATOR_CO2_KG_CO2EQ_POR_KG"] = 2.54

    arquivo_json, arquivo_csv = gravar_ct05(
        pasta=pasta,
        lotes_estado=estado_exemplo(),
        resumo_execucao=resumo,
        params=parametros,
        id_execucao="TESTE-CT05",
        agora="2026-11-17T00:00:00-03:00",
        entradas={},
    )

    assert arquivo_csv.is_file()
    return json.loads(arquivo_json.read_text(encoding="utf-8"))


def test_separa_estado_acumulado_dos_registros_da_execucao(tmp_path):
    # O estado tem dois lotes identificados.
    # A execução inclui também um registro inválido sem lote_id.
    resumo = {
        "contagens_execucao": {
            "processado": 1,
            "revisao_humana": 0,
            "falha": 2,
            "total_tratados": 3,
            "registros_sem_id": 1,
        },
        "ignorados_nao_entregues": 0,
        "taxa_automacao": round(1 / 3, 4),
        "taxa_revisao_humana": 0.0,
        "taxa_erros": round(2 / 3, 4),
    }

    dados = gerar_indicadores(tmp_path, resumo)

    assert dados["lotes"]["processado"] == 1
    assert dados["lotes"]["revisao_humana"] == 0
    assert dados["lotes"]["falha"] == 1

    contagens = dados["execucao"]["contagens"]
    assert contagens["falha"] == 2
    assert contagens["registros_sem_id"] == 1
    assert contagens["total_tratados"] == sum(
        contagens[chave]
        for chave in ("processado", "revisao_humana", "falha")
    )

    assert dados["execucao"]["id_execucao"] == "TESTE-CT05"
    assert dados["massa_recebida_validada_kg"] == 10.0
    assert dados["co2_evitado_estimado_kg_co2eq"] == 25.4
    assert dados["ranking_esg"][0]["pontos_acumulados"] == 100
    assert dados["taxa_erros"] == round(2 / 3, 4)
    assert dados["simulado"] is True
    assert dados["nao_calculados"]["refeicoes"] is None


def test_aceita_resumo_sem_o_novo_campo(tmp_path):
    dados = gerar_indicadores(tmp_path, {})

    assert dados["execucao"]["contagens"] is None
    assert dados["lotes"]["falha"] == 1
    assert dados["massa_recebida_validada_kg"] == 10.0
    assert dados["taxa_erros"] is None
