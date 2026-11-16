import json
from datetime import datetime

from conftest import BASE
from robo.adaptadores import ct03, iot
from robo.config import carregar_json
from robo.validacao import validar

MAPA_CT03 = carregar_json(BASE / "config" / "mapa_campos_ct03.json")
MAPA_IOT = carregar_json(BASE / "config" / "mapa_campos_iot.json")


def test_mapa_ct03_cobre_obrigatorios():
    assert set(MAPA_CT03["obrigatorios"]) <= set(MAPA_CT03["campos"])


def test_adaptar_virgula_decimal_e_null():
    lote, erros = ct03.adaptar({"lote_id": "L1", "quantidade_disponibilizada_kg": "12,5",
                                "quantidade_recebida_kg": None, "entrega_confirmada_em": "2026-11-16T10:00:00-03:00"},
                               MAPA_CT03)
    assert lote["quantidade_disponibilizada_kg"] == 12.5 and lote["quantidade_recebida_kg"] is None and not erros


def test_validacao_aponta_campos():
    lote, erros = ct03.adaptar({"lote_id": "", "doador_id": "D", "beneficiario_id": "B", "alimento_descricao": "x",
                                "quantidade_disponibilizada_kg": -3, "status_logistico": "entregue",
                                "entrega_confirmada_em": "nao-e-data", "simulado": True}, MAPA_CT03)
    inval = validar(lote, erros, MAPA_CT03["obrigatorios"])
    assert {"lote_id", "quantidade_disponibilizada_kg", "entrega_confirmada_em"} <= set(inval)


def test_dois_formatos_de_alerta_e_maiusculas(tmp_path):
    (tmp_path / "a.log").write_text(
        't/alerta {"lote_id":"L","seq":1,"ts":"2026-11-11T13:24:39Z","evento":"quebra_cadeia_frio","estado":"normalizado","temp_c":4.0}\n'
        't/alerta {"lote_id":"L","seq":2,"ts":"2026-11-11T13:32:35Z","evento":"quebra_cadeia_frio","temp_c":8.2,"limite_c":5.0,"duracao_acima_s":31,"severidade":"alta","origem":"fisico"}\n'
        't/telemetria {"lote_id":"L","seq":3,"ts":"2026-11-11T13:33:00Z","evento":"quebra_cadeia_frio","estado":"ALERTA","origem":"fisico"}\n'
        't/telemetria {"lote_id":"L","seq":4,"ts":"2026-11-11T13:34:00Z","evento":"normal","estado":"frio_ok","origem":"fisico"}\n'
        't/telemetria {"lote_id":"L","seq":5,"ts":"2026-11-11T13:35:00Z"\n', encoding="utf-8")
    f = iot.ler_pasta(tmp_path, MAPA_IOT)
    tipos = [m["tipo_mensagem"] for m in f["mensagens"]]
    assert tipos == ["alerta_normalizacao", "alerta_ativacao", "telemetria", "telemetria"]
    assert [m["situacao_termica"] for m in f["mensagens"]] == ["normalizacao", "ativacao", "ativacao", "normal"]
    assert f["mensagens"][2]["estado_bruto"] == "ALERTA"  # valor bruto preservado
    assert f["mensagens"][0]["origem"] is None  # normalização sem origem: não inferida
    assert len(f["linhas_invalidas"]) == 1  # linha quebrada ignorada sem parar a leitura


def test_log_fisico_real_gera_ativacao_para_lote_0001():
    f = iot.ler_pasta(BASE / "dados" / "iot_fisico", MAPA_IOT)
    entrega = datetime.fromisoformat("2026-11-11T11:00:00-03:00")
    r = iot.avaliar_lote("LOTE-2026-0001", entrega, f, ["fisico"], 24)
    assert r["ativacao_aceita"] and r["origem"] == "fisico"
    alertas = [a for a in r["ativacoes"] if a["tipo_mensagem"] == "alerta_ativacao"]
    assert alertas and alertas[0]["ts"] == "2026-11-11T13:32:35Z" and alertas[0]["linha"] == 107
    # fora da janela (entrega 2 dias depois) não conta
    assert not iot.avaliar_lote("LOTE-2026-0001", datetime.fromisoformat("2026-11-14T11:00:00-03:00"), f,
                                ["fisico"], 24)["ativacao_aceita"]
    # origem não aceita (modo simulado) não conta: físico e simulado não se misturam
    assert not iot.avaliar_lote("LOTE-2026-0001", entrega, f, ["simulador"], 24)["ativacao_aceita"]


def test_ct03_ausente_e_ilegivel(tmp_path):
    import pytest
    with pytest.raises(FileNotFoundError):
        ct03.ler_arquivo(tmp_path / "nao_existe.json")
    (tmp_path / "q.json").write_text("{quebrado", encoding="utf-8")
    with pytest.raises(ct03.EntradaIlegivel):
        ct03.ler_arquivo(tmp_path / "q.json")


def test_ct03_acrescimos_femd():
    import json
    from robo.adaptadores.ct03 import adaptar
    from robo.config import BASE
    mapa = json.loads((BASE / "config" / "mapa_campos_ct03.json").read_text(encoding="utf-8"))
    reg = {"lote_id": "L1", "divergencias_informadas": [" falta_quantidade ", ""], "triagem_visual": {"inconclusivo": True}}
    lote, erros = adaptar(reg, mapa)
    assert lote["divergencias_informadas"] == ["falta_quantidade"] and lote["triagem_visual"] == {"inconclusivo": True}
    assert "divergencias_informadas" not in erros and "triagem_visual" not in erros
    lote, erros = adaptar({"lote_id": "L2", "divergencias_informadas": "texto", "triagem_visual": 3}, mapa)
    assert "divergencias_informadas" in erros and "triagem_visual" in erros
    lote, erros = adaptar({"lote_id": "L3"}, mapa)
    assert lote["divergencias_informadas"] == [] and lote["triagem_visual"] is None
