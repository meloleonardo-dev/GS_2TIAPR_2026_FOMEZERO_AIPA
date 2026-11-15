# Revisão humana (raia do Operador no BPMN)

1ª execução gera `fila_revisao_gerada.csv`. As decisões em `decisoes_revisao_SIMULADAS.csv` foram escritas **pelo script de demonstração** (revisor `OP-DEMO`), no lugar do operador; **não são revisão humana real**. A 2ª execução lê o arquivo (H1) e: aprovado -> T7 em diante com `origem_quantidade = revisao_humana`; reprovado -> continua `revisao_humana` com `revisao.situacao = reprovado` (final), sem pontos.

Resultado da 2ª execução (EXEC-20261113-215215):

| lote_id | status | motivo | protocolo |
|---|---|---|---|
| LOTE-2026-0001 | revisao_humana | alerta_iot_quebra_cadeia_frio, baixa_confianca, reprovado_na_revisao |  |
| LOTE-2026-0002 | ignorado_duplicado |  |  |
| LOTE-2026-0003 | ignorado_duplicado |  |  |
| LOTE-2026-0005 | ignorado_duplicado |  |  |
| LOTE-2026-0006 | processado |  | SIM-000004 |
| LOTE-2026-0007 | processado |  | SIM-000005 |
| LOTE-2026-0008 | ignorado_duplicado |  |  |
| LOTE-2026-0009 | ignorado_duplicado |  |  |
| LOTE-2026-0010 | ignorado_duplicado |  |  |
| LOTE-2026-0011 | ignorado_duplicado |  |  |
| (vazio) | ignorado_duplicado |  |  |
| LOTE-2026-0002 | ignorado_duplicado |  |  |
| LOTE-2026-0004 | ignorado_nao_entregue |  |  |

Trecho do log:

```
2026-11-13 21:52:20,311 | INFO | EXEC-20261113-215215 | T10 | LOTE-2026-0001 | status revisao_humana motivo ['alerta_iot_quebra_cadeia_frio', 'baixa_confianca', 'reprovado_na_revisao']
2026-11-13 21:52:20,312 | INFO | EXEC-20261113-215215 | G4 | LOTE-2026-0002 | gateway -> duplicado
2026-11-13 21:52:20,312 | INFO | EXEC-20261113-215215 | G4 | LOTE-2026-0003 | gateway -> duplicado
2026-11-13 21:52:20,313 | INFO | EXEC-20261113-215215 | G4 | LOTE-2026-0005 | gateway -> duplicado
2026-11-13 21:52:23,930 | INFO | EXEC-20261113-215215 | T9 | LOTE-2026-0006 | lançamento confirmado pela API REST (protocolo SIM-000004, meio selenium)
2026-11-13 21:52:23,937 | INFO | EXEC-20261113-215215 | T10 | LOTE-2026-0006 | status processado motivo []
2026-11-13 21:52:25,944 | INFO | EXEC-20261113-215215 | T9 | LOTE-2026-0007 | lançamento confirmado pela API REST (protocolo SIM-000005, meio selenium)
2026-11-13 21:52:25,953 | INFO | EXEC-20261113-215215 | T10 | LOTE-2026-0007 | status processado motivo []
2026-11-13 21:52:25,954 | INFO | EXEC-20261113-215215 | G4 | LOTE-2026-0008 | gateway -> duplicado
2026-11-13 21:52:25,954 | INFO | EXEC-20261113-215215 | G4 | LOTE-2026-0009 | gateway -> duplicado
2026-11-13 21:52:25,955 | INFO | EXEC-20261113-215215 | G4 | LOTE-2026-0010 | gateway -> duplicado
2026-11-13 21:52:25,956 | INFO | EXEC-20261113-215215 | G3 | LOTE-2026-0011 | gateway -> nao
2026-11-13 21:52:25,956 | INFO | EXEC-20261113-215215 | G4 | LOTE-2026-0011 | gateway -> duplicado
2026-11-13 21:52:25,956 | INFO | EXEC-20261113-215215 | G3 | indice10 | gateway -> nao
2026-11-13 21:52:25,957 | INFO | EXEC-20261113-215215 | G4 | indice10 | gateway -> duplicado
2026-11-13 21:52:25,957 | INFO | EXEC-20261113-215215 | G4 | LOTE-2026-0002 | gateway -> duplicado
2026-11-13 21:52:25,957 | INFO | EXEC-20261113-215215 | G2 | LOTE-2026-0004 | gateway -> nao (em_transporte)
```
