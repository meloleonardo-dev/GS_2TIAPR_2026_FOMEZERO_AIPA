# F2 · fonte da IoT ausente

Comando: `python executar_robo.py --cenario iot_ausente` (código de saída 0). Pasta de trabalho separada `saida/cenarios/iot_ausente/`. Dados SIMULADOS; portal SIMULADO.

## Trecho do log

```
2026-11-13 21:52:38,739 | WARNING | EXEC-20261113-215237 | T2 | - | fonte da IoT ausente (iot/*.log): todos os lotes vão para revisão humana (dados_iot_indisponiveis)
2026-11-13 21:52:39,943 | INFO | EXEC-20261113-215237 | G5 | LOTE-2026-0001 | gateway -> revisao_humana
2026-11-13 21:52:39,945 | INFO | EXEC-20261113-215237 | T10 | LOTE-2026-0001 | status revisao_humana motivo ['alerta_iot_quebra_cadeia_frio', 'dados_iot_indisponiveis', 'baixa_confianca']
2026-11-13 21:52:39,948 | INFO | EXEC-20261113-215237 | G5 | LOTE-2026-0002 | gateway -> revisao_humana
2026-11-13 21:52:39,950 | INFO | EXEC-20261113-215237 | T10 | LOTE-2026-0002 | status revisao_humana motivo ['dados_iot_indisponiveis']
2026-11-13 21:52:39,953 | INFO | EXEC-20261113-215237 | G5 | LOTE-2026-0003 | gateway -> revisao_humana
2026-11-13 21:52:39,957 | INFO | EXEC-20261113-215237 | T10 | LOTE-2026-0003 | status revisao_humana motivo ['dados_iot_indisponiveis']
2026-11-13 21:52:39,959 | INFO | EXEC-20261113-215237 | G5 | LOTE-2026-0005 | gateway -> revisao_humana
2026-11-13 21:52:39,962 | INFO | EXEC-20261113-215237 | T10 | LOTE-2026-0005 | status revisao_humana motivo ['dados_iot_indisponiveis']
2026-11-13 21:52:39,964 | INFO | EXEC-20261113-215237 | G5 | LOTE-2026-0006 | gateway -> revisao_humana
2026-11-13 21:52:39,967 | INFO | EXEC-20261113-215237 | T10 | LOTE-2026-0006 | status revisao_humana motivo ['dados_iot_indisponiveis', 'ocorrencia_avaria', 'baixa_confianca']
2026-11-13 21:52:39,969 | INFO | EXEC-20261113-215237 | G5 | LOTE-2026-0007 | gateway -> revisao_humana
2026-11-13 21:52:39,972 | INFO | EXEC-20261113-215237 | T10 | LOTE-2026-0007 | status revisao_humana motivo ['dados_iot_indisponiveis', 'ocorrencia_avaria']
2026-11-13 21:52:39,975 | INFO | EXEC-20261113-215237 | G5 | LOTE-2026-0008 | gateway -> revisao_humana
2026-11-13 21:52:39,979 | INFO | EXEC-20261113-215237 | T10 | LOTE-2026-0008 | status revisao_humana motivo ['dados_iot_indisponiveis', 'ocorrencia_divergencia_quantidade', 'divergencia_kg']
2026-11-13 21:52:39,981 | INFO | EXEC-20261113-215237 | G5 | LOTE-2026-0009 | gateway -> revisao_humana
2026-11-13 21:52:39,984 | INFO | EXEC-20261113-215237 | T10 | LOTE-2026-0009 | status revisao_humana motivo ['dados_iot_indisponiveis', 'ocorrencia_problema_temperatura']
2026-11-13 21:52:39,986 | INFO | EXEC-20261113-215237 | G5 | LOTE-2026-0010 | gateway -> revisao_humana
2026-11-13 21:52:39,989 | INFO | EXEC-20261113-215237 | T10 | LOTE-2026-0010 | status revisao_humana motivo ['dados_iot_indisponiveis', 'ocorrencia_ilegivel_outro', 'sem_confirmacao']
2026-11-13 21:52:39,989 | INFO | EXEC-20261113-215237 | G3 | LOTE-2026-0011 | gateway -> nao
2026-11-13 21:52:39,992 | WARNING | EXEC-20261113-215237 | T3 | LOTE-2026-0011 | campo inválido: quantidade_disponibilizada_kg
2026-11-13 21:52:39,994 | INFO | EXEC-20261113-215237 | T10 | LOTE-2026-0011 | status falha motivo ['dado_invalido:quantidade_disponibilizada_kg']
2026-11-13 21:52:39,995 | INFO | EXEC-20261113-215237 | G3 | indice10 | gateway -> nao
2026-11-13 21:52:39,998 | WARNING | EXEC-20261113-215237 | T3 | indice10 | campo inválido: lote_id
2026-11-13 21:52:39,999 | INFO | EXEC-20261113-215237 | T10 | indice10 | status falha motivo ['dado_invalido:lote_id']
2026-11-13 21:52:39,999 | INFO | EXEC-20261113-215237 | G4 | LOTE-2026-0002 | gateway -> duplicado
2026-11-13 21:52:39,999 | INFO | EXEC-20261113-215237 | G2 | LOTE-2026-0004 | gateway -> nao (em_transporte)
```

## Resultado

| lote_id | status | motivo | protocolo |
|---|---|---|---|
| LOTE-2026-0001 | revisao_humana | alerta_iot_quebra_cadeia_frio, dados_iot_indisponiveis, baixa_confianca |  |
| LOTE-2026-0002 | revisao_humana | dados_iot_indisponiveis |  |
| LOTE-2026-0003 | revisao_humana | dados_iot_indisponiveis |  |
| LOTE-2026-0005 | revisao_humana | dados_iot_indisponiveis |  |
| LOTE-2026-0006 | revisao_humana | dados_iot_indisponiveis, ocorrencia_avaria, baixa_confianca |  |
| LOTE-2026-0007 | revisao_humana | dados_iot_indisponiveis, ocorrencia_avaria |  |
| LOTE-2026-0008 | revisao_humana | dados_iot_indisponiveis, ocorrencia_divergencia_quantidade, divergencia_kg |  |
| LOTE-2026-0009 | revisao_humana | dados_iot_indisponiveis, ocorrencia_problema_temperatura |  |
| LOTE-2026-0010 | revisao_humana | dados_iot_indisponiveis, ocorrencia_ilegivel_outro, sem_confirmacao |  |
| LOTE-2026-0011 | falha | dado_invalido:quantidade_disponibilizada_kg |  |
| (vazio) | falha | dado_invalido:lote_id |  |
| LOTE-2026-0002 | ignorado_duplicado |  |  |
| LOTE-2026-0004 | ignorado_nao_entregue |  |  |

Falhas tratadas registradas no relatório: 13. Execução terminou com relatório (`relatorio_EXEC-20261113-215237.md`).
