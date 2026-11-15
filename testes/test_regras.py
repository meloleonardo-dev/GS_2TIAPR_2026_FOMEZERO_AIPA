from robo.regras import EntradaRegras, avaliar


def base(**kw):
    d = dict(texto_presente=True, modelo_disponivel=True, classe="sem_ocorrencia", confianca=0.95, limiar=0.7,
             kg_extraido=12.0, kg_cadastrado=12.0)
    d.update(kw)
    return EntradaRegras(**d)


def test_lote_limpo_segue_automatico(params):
    assert avaliar(base(), params) == []


def test_r1_alerta_iot(params):
    assert "alerta_iot_quebra_cadeia_frio" in avaliar(base(iot_ativacao_aceita=True), params)


def test_r2_iot_indisponivel(params):
    assert "dados_iot_indisponiveis" in avaliar(base(iot_fonte_disponivel=False), params)


def test_r3_iot_desconhecido(params):
    assert "evento_iot_desconhecido" in avaliar(base(iot_desconhecido=True), params)


def test_r4_ocorrencia(params):
    assert avaliar(base(classe="avaria"), params) == ["ocorrencia_avaria"]


def test_r5_baixa_confianca(params):
    assert avaliar(base(confianca=0.69), params) == ["baixa_confianca"]


def test_r6_divergencia_com_tolerancia(params):
    # tolerância = max(5% de 12 = 0,6; 0,5) = 0,6 kg
    assert avaliar(base(kg_extraido=11.5), params) == []
    assert avaliar(base(kg_extraido=11.3), params) == ["divergencia_kg"]
    # tolerância mínima 0,5 kg para lote pequeno
    assert avaliar(base(kg_extraido=2.6, kg_cadastrado=2.0), params) == ["divergencia_kg"]
    assert avaliar(base(kg_recebido_informado=8.0), params) == ["divergencia_kg"]


def test_r7_sem_confirmacao(params):
    assert "sem_confirmacao" in avaliar(base(texto_presente=False, kg_extraido=None, classe=None, confianca=None), params)
    assert "sem_confirmacao" in avaliar(base(kg_extraido=None), params)


def test_r8_modelo_indisponivel(params):
    m = avaliar(base(modelo_disponivel=False, classe=None, confianca=None), params)
    assert m == ["modelo_indisponivel"]


def test_r9_lote_alterado(params):
    assert "lote_alterado_apos_processamento" in avaliar(base(lote_alterado=True), params)


def test_nenhuma_regra_declara_seguro(params):
    # a saída é só uma lista de motivos de revisão; não existe motivo/valor "seguro"
    for m in avaliar(base(iot_ativacao_aceita=True, classe="problema_temperatura"), params):
        assert "segur" not in m and "apto" not in m
