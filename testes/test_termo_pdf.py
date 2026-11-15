from robo import calculos, termo_pdf


def dados(params):
    return {"lote_id": "LOTE-TESTE-1", "doador_id": "DOADOR-T", "doador_nome_ficticio": "Exemplo (SIMULADO)",
            "beneficiario_id": "BENEF-T", "beneficiario_tipo": "ONG", "alimento_descricao": "pão",
            "quantidade_disponibilizada_kg": 12.0, "quantidade_recebida_kg": 12.0,
            "origem_quantidade": "confirmacao_beneficiario", "entrega_confirmada_em": "2026-11-16T10:00:00-03:00",
            "co2_evitado_kg_co2eq": 30.48, "metodologia_carbono": calculos.metodologia(params), "pontos": 120,
            "selo_verde_esg": None, "selo_situacao": "abaixo_do_minimo", "kg_acumulado_doador": 12.0,
            "termo_doacao_id": "TERMO-LOTE-TESTE-1", "id_execucao": "EXEC-TESTE", "emitido_em": "2026-11-13"}


def test_termo_gerado_e_conferido(tmp_path, params):
    pdf = termo_pdf.gerar(dados(params), tmp_path / "t.pdf")
    ok, det = termo_pdf.conferir(pdf, "LOTE-TESTE-1", 30.48)
    assert ok, det


def test_conferencia_detecta_valor_errado(tmp_path, params):
    pdf = termo_pdf.gerar(dados(params), tmp_path / "t.pdf")
    ok, det = termo_pdf.conferir(pdf, "LOTE-TESTE-1", 99.99)
    assert not ok and "co2" in det


def test_conferencia_detecta_pdf_quebrado(tmp_path):
    (tmp_path / "x.pdf").write_bytes(b"nao e pdf")
    assert termo_pdf.conferir(tmp_path / "x.pdf", "L", 1.0)[0] is False
