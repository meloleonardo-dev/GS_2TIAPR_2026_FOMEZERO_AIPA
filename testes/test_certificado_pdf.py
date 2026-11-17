import pytest

from robo import certificado_pdf
from robo.banco import Banco


def ct04(lote_id, doador, kg, status="processado", pontos=None):
    return {"lote_id": lote_id, "doador_id": doador, "status": status, "motivo": [], "quantidade_recebida_kg": kg,
            "origem_quantidade": "confirmacao_beneficiario", "revisao": None, "id_execucao": "EXEC-T",
            "pontos": pontos if pontos is not None else int(kg * 10)}


@pytest.fixture
def banco(tmp_path):
    b = Banco(tmp_path / "estado.db")
    yield b
    b.fechar()


def test_sem_selo_abaixo_do_bronze(banco, params):
    banco.gravar_lote(ct04("L1", "D1", 30.0), "h1", "T10", "2026-11-17")
    with pytest.raises(certificado_pdf.SemSelo):
        certificado_pdf.dados_do_doador(banco, "D1", params, "Padaria", "2026-11-17T10:00:00-03:00")


def test_so_lotes_processados_contam(banco, params):
    banco.gravar_lote(ct04("L1", "D1", 40.0), "h1", "T10", "2026-11-17")
    banco.gravar_lote(ct04("L2", "D1", 40.0, status="revisao_humana", pontos=0), "h2", "T6", "2026-11-17")
    with pytest.raises(certificado_pdf.SemSelo):
        certificado_pdf.dados_do_doador(banco, "D1", params, None, "2026-11-17T10:00:00-03:00")


def test_certificado_bronze_gerado_e_conferido(banco, params, tmp_path):
    banco.gravar_lote(ct04("L1", "D1", 30.0), "h1", "T10", "2026-11-17")
    banco.gravar_lote(ct04("L2", "D1", 25.0), "h2", "T10", "2026-11-17")
    banco.gravar_lote(ct04("L3", "OUTRO", 500.0), "h3", "T10", "2026-11-17")
    d = certificado_pdf.dados_do_doador(banco, "D1", params, "Padaria (SIMULADO)", "2026-11-17T10:00:00-03:00")
    assert d["selo"] == "Bronze" and d["kg_acumulado"] == 55.0 and d["n_lotes"] == 2 and d["pontos"] == 550
    pdf = certificado_pdf.gerar(d, tmp_path / "c.pdf")
    ok, det = certificado_pdf.conferir(pdf, "Bronze", d["codigo"])
    assert ok, det


def test_conferencia_detecta_nivel_errado(banco, params, tmp_path):
    banco.gravar_lote(ct04("L1", "D1", 210.0), "h1", "T10", "2026-11-17")
    d = certificado_pdf.dados_do_doador(banco, "D1", params, None, "2026-11-17T10:00:00-03:00")
    assert d["selo"] == "Prata"
    pdf = certificado_pdf.gerar(d, tmp_path / "c.pdf")
    assert certificado_pdf.conferir(pdf, "Ouro", d["codigo"])[0] is False


def test_certificado_nunca_diz_seguro_nem_certificado_oficial(banco, params, tmp_path):
    banco.gravar_lote(ct04("L1", "D1", 600.0), "h1", "T10", "2026-11-17")
    d = certificado_pdf.dados_do_doador(banco, "D1", params, None, "2026-11-17T10:00:00-03:00")
    pdf = certificado_pdf.gerar(d, tmp_path / "c.pdf")
    from pypdf import PdfReader
    texto = " ".join("".join(p.extract_text() or "" for p in PdfReader(str(pdf)).pages).split())
    assert "Não é certificação" in texto and "Não atesta que o alimento é seguro" in texto
