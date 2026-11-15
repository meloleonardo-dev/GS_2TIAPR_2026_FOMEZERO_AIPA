import pytest

from robo.nlp_ocorrencia import classificar_palavras_chave, extrair_kg
from robo.observabilidade import mascarar


@pytest.mark.parametrize("texto,esperado", [
    ("recebemos 12 kg de pão, tudo certo", 12.0),
    ("recebemos 12 kg de pão, 2 kg amassados", 12.0),
    ("dos 15 kg combinados só chegaram 9 kg de batata", 9.0),
    ("a doação era de 20 kg mas vieram 14 kg", 14.0),
    ("chegaram 10 kg de tomate amassado", 10.0),
    ("12kg de pão", 12.0),
    ("12,5 kgs de leite", 12.5),
    ("vinte e cinco quilos de arroz", 25.0),
    ("dois quilos e meio de banana", 2.5),
    ("meio quilo de manteiga", 0.5),
    ("faltaram 3 kg de batata", None),
    ("ok, valeu", None),
    ("", None),
    (None, None),
])
def test_kg_extraido(texto, esperado):
    assert extrair_kg(texto)["kg_extraido"] == esperado


@pytest.mark.parametrize("texto,v1,v2", [
    # casos do conjunto de desenvolvimento (FM-10, FM-12, FM-15, FM-17): v1 errava, v2 acerta
    ("pão veio todo esmagado, deu pra aproveitar pouco dos 5 kg", None, 5.0),
    ("as bandejas de ovos chegaram com várias trincadas, mais ou menos dois quilos perdidos de dez", 2.0, 10.0),
    ("no app tava 25 kg mas na balança deu 18", 25.0, 18.0),
    ("tinha que ser 40 kilos de laranja, mas o motorista trouxe 32", 40.0, 32.0),
    # número sem unidade que NÃO é kg
    ("recebemos 12 kg, vieram 3 caixas", 12.0, 12.0),
    ("chegaram 8 kg e o termômetro deu 15 graus", 8.0, 8.0),
    ("contei aqui e sumiram umas 3 caixas", None, None),
    ("cheeeegou 8 quilos de macarrão", 8.0, 8.0),
])
def test_extracao_v1_x_v2(texto, v1, v2):
    assert extrair_kg(texto, versao=1)["kg_extraido"] == v1
    assert extrair_kg(texto, versao=2)["kg_extraido"] == v2


def test_kg_ocorrencia_separado_do_recebido():
    r = extrair_kg("recebemos 12 kg de pão, 2 kg amassados")
    assert r["kg_ocorrencia"] == 2.0
    assert [q["papel"] for q in r["quantidades"]] == ["recebido", "ocorrencia"]


def test_numero_sem_unidade_nao_vira_kg():
    assert extrair_kg("o termômetro marcava 12 graus")["kg_extraido"] is None


def test_linha_de_base():
    assert classificar_palavras_chave("recebemos 5 kg de queijo mas chegou quente") == "problema_temperatura"
    assert classificar_palavras_chave("recebemos 5 kg, 1 kg amassado") == "avaria"
    assert classificar_palavras_chave("faltaram 3 kg") == "divergencia_quantidade"
    assert classificar_palavras_chave("ok") == "ilegivel_outro"
    assert classificar_palavras_chave("recebemos 5 kg de pão") == "sem_ocorrencia"


def test_mascara_dados_pessoais():
    t = mascarar("me liga 11 98765-4321 ou fulano@exemplo.com, cpf 123.456.789-09, recebi 12 kg")
    assert "98765" not in t and "@" not in t and "123.456" not in t and "12 kg" in t
