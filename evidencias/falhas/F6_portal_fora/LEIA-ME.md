# F6 · portal fora do ar

Comando: `python executar_robo.py --cenario portal_fora` (código de saída 0). Pasta de trabalho separada `saida/cenarios/portal_fora/`. Dados SIMULADOS; portal SIMULADO.

## Trecho do log

```
2026-11-13 21:52:56,948 | WARNING | EXEC-20261113-215254 | T1 | - | health tentativa 1/3 falhou: ConnectionError
2026-11-13 21:53:00,989 | WARNING | EXEC-20261113-215254 | T1 | - | health tentativa 2/3 falhou: ConnectionError
2026-11-13 21:53:07,034 | WARNING | EXEC-20261113-215254 | T1 | - | health tentativa 3/3 falhou: ConnectionError
2026-11-13 21:53:07,036 | ERROR | EXEC-20261113-215254 | T1 | - | portal SIMULADO fora do ar após as tentativas; lotes válidos ficam em falha portal_indisponivel e são retomados na próxima execução
2026-11-13 21:53:08,706 | INFO | EXEC-20261113-215254 | G7 | LOTE-2026-0002 | gateway -> nao
2026-11-13 21:53:08,706 | ERROR | EXEC-20261113-215254 | T9 | LOTE-2026-0002 | falha tratada: portal_indisponivel (health falhou no T1)
2026-11-13 21:53:08,711 | INFO | EXEC-20261113-215254 | T10 | LOTE-2026-0002 | status falha motivo ['portal_indisponivel']
2026-11-13 21:53:08,740 | INFO | EXEC-20261113-215254 | G7 | LOTE-2026-0003 | gateway -> nao
2026-11-13 21:53:08,740 | ERROR | EXEC-20261113-215254 | T9 | LOTE-2026-0003 | falha tratada: portal_indisponivel (health falhou no T1)
2026-11-13 21:53:08,744 | INFO | EXEC-20261113-215254 | T10 | LOTE-2026-0003 | status falha motivo ['portal_indisponivel']
```

## Resultado

| lote_id | status | motivo | protocolo |
|---|---|---|---|
| LOTE-2026-0002 | falha | portal_indisponivel |  |
| LOTE-2026-0003 | falha | portal_indisponivel |  |

Falhas tratadas registradas no relatório: 3. Execução terminou com relatório (`relatorio_EXEC-20261113-215254.md`).

## Retomada (portal normal, mesma pasta)

Comando: `python executar_robo.py --trabalho saida/cenarios/portal_fora`

| lote_id | status | motivo | protocolo |
|---|---|---|---|
| LOTE-2026-0002 | processado |  | SIM-000001 |
| LOTE-2026-0003 | processado |  | SIM-000002 |

```
2026-11-13 21:53:15,400 | INFO | EXEC-20261113-215312 | G4 | LOTE-2026-0002 | gateway -> retomar
2026-11-13 21:53:15,400 | INFO | EXEC-20261113-215312 | T4 | LOTE-2026-0002 | retomando lote pendente da etapa T9 (motivo anterior ['portal_indisponivel'])
2026-11-13 21:53:18,747 | INFO | EXEC-20261113-215312 | T9 | LOTE-2026-0002 | lançamento confirmado pela API REST (protocolo SIM-000001, meio selenium)
2026-11-13 21:53:18,753 | INFO | EXEC-20261113-215312 | T10 | LOTE-2026-0002 | status processado motivo []
2026-11-13 21:53:18,753 | INFO | EXEC-20261113-215312 | G4 | LOTE-2026-0003 | gateway -> retomar
2026-11-13 21:53:18,753 | INFO | EXEC-20261113-215312 | T4 | LOTE-2026-0003 | retomando lote pendente da etapa T9 (motivo anterior ['portal_indisponivel'])
2026-11-13 21:53:20,717 | INFO | EXEC-20261113-215312 | T9 | LOTE-2026-0003 | lançamento confirmado pela API REST (protocolo SIM-000002, meio selenium)
2026-11-13 21:53:20,724 | INFO | EXEC-20261113-215312 | T10 | LOTE-2026-0003 | status processado motivo []
```
