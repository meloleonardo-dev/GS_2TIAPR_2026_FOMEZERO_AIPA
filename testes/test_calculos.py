from robo import calculos


def test_co2_estimativa(params):
    assert calculos.co2_evitado(12.0, params) == 30.48
    assert calculos.co2_evitado(None, params) is None  # indisponível = None, nunca 0


def test_pontos_arredonda_para_baixo(params):
    assert calculos.pontos(12.0, params) == 120
    assert calculos.pontos(2.55, params) == 25
    assert calculos.pontos(None, params) is None


def test_selo_por_acumulado(params):
    assert calculos.selo(49.9, params) == (None, "abaixo_do_minimo")
    assert calculos.selo(50, params) == ("Bronze", "concedido")
    assert calculos.selo(200, params) == ("Prata", "concedido")
    assert calculos.selo(500, params) == ("Ouro", "concedido")


def test_tolerancia(params):
    assert calculos.tolerancia_kg(100, params) == 5.0
    assert calculos.tolerancia_kg(2, params) == 0.5


def test_metodologia_sempre_estimativa(params):
    m = calculos.metodologia(params)
    assert m["tipo"] == "estimativa" and m["fator_kg_co2eq_por_kg"] == 2.54 and "F-026" in m["fonte"]
