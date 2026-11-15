# F4 · IoT SIMULADA com linha JSON quebrada, valor não mapeado e alerta simulado (execução separada da física)

Comando: `python executar_robo.py --cenario iot_invalido` (código de saída 0). Pasta de trabalho separada `saida/cenarios/iot_invalido/`. Dados SIMULADOS; portal SIMULADO.

## Trecho do log

```
2026-11-13 21:52:49,877 | WARNING | EXEC-20261113-215248 | T2 | - | linha da IoT ignorada (iot_simulado_invalido.log:3, JSONDecodeError)
2026-11-13 21:52:51,424 | WARNING | EXEC-20261113-215248 | T6 | LOTE-2026-0003 | valor IoT não mapeado estado=SENSOR_XYZ evento=normal (iot_simulado_invalido.log:2)
2026-11-13 21:52:51,424 | INFO | EXEC-20261113-215248 | G5 | LOTE-2026-0003 | gateway -> revisao_humana
2026-11-13 21:52:51,427 | INFO | EXEC-20261113-215248 | T10 | LOTE-2026-0003 | status revisao_humana motivo ['evento_iot_desconhecido']
2026-11-13 21:52:51,430 | INFO | EXEC-20261113-215248 | G5 | LOTE-2026-0005 | gateway -> revisao_humana
2026-11-13 21:52:51,433 | INFO | EXEC-20261113-215248 | T10 | LOTE-2026-0005 | status revisao_humana motivo ['alerta_iot_quebra_cadeia_frio']
2026-11-13 21:52:51,435 | INFO | EXEC-20261113-215248 | G5 | LOTE-2026-0006 | gateway -> revisao_humana
2026-11-13 21:52:51,439 | INFO | EXEC-20261113-215248 | T10 | LOTE-2026-0006 | status revisao_humana motivo ['ocorrencia_avaria', 'baixa_confianca']
```

## Resultado

| lote_id | status | motivo | protocolo |
|---|---|---|---|
| LOTE-2026-0003 | revisao_humana | evento_iot_desconhecido |  |
| LOTE-2026-0005 | revisao_humana | alerta_iot_quebra_cadeia_frio |  |
| LOTE-2026-0006 | revisao_humana | ocorrencia_avaria, baixa_confianca |  |

Falhas tratadas registradas no relatório: 1. Execução terminou com relatório (`relatorio_EXEC-20261113-215248.md`).
