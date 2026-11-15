# Evidências de validação (geradas por `python gerar_evidencias.py`)

Tudo foi produzido por execução real do robô nesta máquina. Dados de lote SINTÉTICOS (SIMULADO); portal SIMULADO; IoT FÍSICA real (logs de 10 e 11/11/2026) na execução normal e SIMULADA só no cenário F4, em pasta separada. Métricas da IA: `metricas_ia_AAAA-MM-DD.md` (v1 x v2 no teste sintético e no desenvolvimento, gerado por `treinar_modelo.py`), `metricas_cego_v2_AAAA-MM-DD.md` (medição única do cego v2, gerado por `medir_cego_v2.py`; congelamento e hash em `cego_v2_CONGELADO.md`) e `arquivo_v1/` (métricas da v1 publicadas no TAR-012, sem mudança).

| evidência | arquivo | resumo |
|---|---|---|
| Execução normal | `execucao_normal/relatorio_EXEC-20261113-215131.md` | processado=3, revisao_humana=6, falha=2, ignorado_duplicado=1, taxa_erros=0.1818 |
| Idempotência (F5) | `idempotencia/LEIA-ME.md` | processado=0, revisao_humana=0, falha=0, ignorado_duplicado=12, taxa_erros=None |
| Revisão humana | `revisao_humana/LEIA-ME.md` | processado=2, revisao_humana=1, falha=0, ignorado_duplicado=9, taxa_erros=0.0 |
| F1 arquivo de lotes ausente | `falhas/F1_arquivo_ausente/LEIA-ME.md` | processado=0, revisao_humana=0, falha=0, ignorado_duplicado=0, taxa_erros=None |
| F2 fonte da IoT ausente | `falhas/F2_iot_ausente/LEIA-ME.md` | processado=0, revisao_humana=9, falha=2, ignorado_duplicado=1, taxa_erros=0.1818 |
| F3 modelo de IA ausente | `falhas/F3_modelo_ausente/LEIA-ME.md` | processado=0, revisao_humana=9, falha=2, ignorado_duplicado=1, taxa_erros=0.1818 |
| F4 IoT SIMULADA com linha JSON quebrada, valor não mapeado e alerta simulado (execução separada da física) | `falhas/F4_iot_invalido/LEIA-ME.md` | processado=0, revisao_humana=3, falha=0, ignorado_duplicado=0, taxa_erros=0.0 |
| F6 portal fora do ar | `falhas/F6_portal_fora/LEIA-ME.md` | processado=0, revisao_humana=0, falha=2, ignorado_duplicado=0, taxa_erros=1.0 |
| F7 timeout (portal lento) | `falhas/F7_portal_lento/LEIA-ME.md` | processado=0, revisao_humana=0, falha=2, ignorado_duplicado=0, taxa_erros=1.0 |
| F8 erro de API (HTTP 500) | `falhas/F8_erro_api/LEIA-ME.md` | processado=0, revisao_humana=0, falha=2, ignorado_duplicado=0, taxa_erros=1.0 |
| F8b erro de API (JSON inválido) | `falhas/F8b_json_invalido/LEIA-ME.md` | processado=0, revisao_humana=0, falha=1, ignorado_duplicado=0, taxa_erros=1.0 |
| F9 senha errada no login do portal | `falhas/F9_credencial_invalida/LEIA-ME.md` | processado=0, revisao_humana=0, falha=2, ignorado_duplicado=0, taxa_erros=1.0 |
| F10 navegador/WebDriver não inicia -> contingência API | `falhas/F10_navegador_indisponivel/LEIA-ME.md` | processado=2, revisao_humana=0, falha=0, ignorado_duplicado=0, taxa_erros=0.0 |
| F11 disco abaixo do mínimo | `falhas/F11_disco_cheio/LEIA-ME.md` | processado=0, revisao_humana=0, falha=0, ignorado_duplicado=0, taxa_erros=None |
| Agendamento (schedule, 2 ciclos de 15 s) | `agendamento/console.txt` |  |
| pytest | `pytest/saida_pytest.txt` | resultado============================== 58 passed in 13.25s ============================= |
