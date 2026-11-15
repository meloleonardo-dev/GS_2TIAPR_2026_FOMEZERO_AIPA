"""Processo inteiro (sem navegador) duas vezes na mesma pasta: um lançamento por lote, contrato CT-04 e BPMN."""
import pytest

from conftest import BASE, SEGREDOS_TESTE, APIFalsa, LancadorFormulario, ler_json
from robo.processo import Robo

pytestmark = pytest.mark.skipif(not (BASE / "modelos" / "ocorrencia-v2.joblib").exists(),
                                reason="rode treinar_modelo.py antes")

CAMPOS_CT04 = {"versao_contrato", "simulado", "lote_id", "doador_id", "status", "motivo", "revisao",
               "quantidade_recebida_kg", "origem_quantidade", "co2_evitado_kg_co2eq", "metodologia_carbono", "pontos",
               "kg_acumulado_doador", "pontos_acumulados_doador", "selo_verde_esg", "selo_situacao",
               "regras_recompensa", "termo_doacao_id", "termo_doacao_arquivo", "portal", "ia", "aviso",
               "processado_em", "id_execucao"}


def rodar(trabalho, params, portal_app):
    r = Robo(trabalho, params, SEGREDOS_TESTE, api=APIFalsa(portal_app), lancador=LancadorFormulario(portal_app))
    return r.executar()


def test_duas_execucoes_um_lancamento(trabalho, params, portal_app):
    rel1 = rodar(trabalho, params, portal_app)
    n1 = APIFalsa(portal_app).resumo()["total_lancamentos"]
    proc1 = rel1["resumo"]["processado"]
    assert n1 == proc1 >= 1
    rel2 = rodar(trabalho, params, portal_app)
    assert APIFalsa(portal_app).resumo()["total_lancamentos"] == n1  # nada lançado de novo
    assert rel2["resumo"]["processado"] == 0
    assert rel2["resumo"]["ignorado_duplicado"] >= proc1
    assert rel2["resumo"]["falha"] == 0  # inválido idêntico já em quarentena não conta como falha nova


def test_contrato_ct04_e_regra_do_null(trabalho, params, portal_app):
    rodar(trabalho, params, portal_app)
    for arq in (trabalho / "saida" / "ct04").glob("LOTE-*.json"):
        c = ler_json(arq)
        assert CAMPOS_CT04 <= set(c), arq.name
        assert c["simulado"] is True and c["metodologia_carbono"]["tipo"] == "estimativa"
        assert "seguro" in c["aviso"]  # o aviso diz que NÃO atesta segurança
        if c["status"] == "processado":
            assert c["pontos"] is not None and c["co2_evitado_kg_co2eq"] is not None and c["portal"]["confirmado_api"]
        else:
            assert c["pontos"] is None and c["selo_verde_esg"] is None and c["motivo"]
        if c["status"] == "revisao_humana":
            assert c["co2_evitado_kg_co2eq"] is None and c["termo_doacao_id"] is None
        assert "confirmacao_entrega_texto" not in str(c["ia"])  # texto livre não sai da AIPA


def test_caminho_bpmn_dos_lotes_de_demonstracao(trabalho, params, portal_app):
    rel = rodar(trabalho, params, portal_app)
    t = rel["trilhas_bpmn"]
    assert t["LOTE-2026-0002"][:4] == ["G2:sim", "T3", "G3:sim", "T4"]
    i = t["LOTE-2026-0002"].index("T7")
    assert t["LOTE-2026-0002"][i:i + 6] == ["T7", "T8", "G6:sim", "T9", "G7:sim", "T10"]
    assert "G5:revisao_humana" in t["LOTE-2026-0001"] and "T7" not in t["LOTE-2026-0001"]
    assert "G3:nao" in t["LOTE-2026-0011"] and "T5" not in t["LOTE-2026-0011"]
    assert any(x == "G4:duplicado" for x in t["LOTE-2026-0002"])
    assert rel["resultados"][0]["motivo"][0] == "alerta_iot_quebra_cadeia_frio"
