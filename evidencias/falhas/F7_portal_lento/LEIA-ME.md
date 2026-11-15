# F7 · timeout (portal lento)

Comando: `python executar_robo.py --cenario portal_lento` (código de saída 0). Pasta de trabalho separada `saida/cenarios/portal_lento/`. Dados SIMULADOS; portal SIMULADO.

## Trecho do log

```
2026-11-13 21:53:34,081 | WARNING | EXEC-20261113-215326 | T9 | LOTE-2026-0002 | API GET /api/lancamentos/LOTE-2026-0002 tentativa 1/3 falhou: ReadTimeout: HTTPConnectionPool(host='127.0.0.1', port=5050): Read timed out. (read timeout=5)
2026-11-13 21:53:41,105 | WARNING | EXEC-20261113-215326 | T9 | LOTE-2026-0002 | API GET /api/lancamentos/LOTE-2026-0002 tentativa 2/3 falhou: ReadTimeout: HTTPConnectionPool(host='127.0.0.1', port=5050): Read timed out. (read timeout=5)
2026-11-13 21:53:50,110 | WARNING | EXEC-20261113-215326 | T9 | LOTE-2026-0002 | API GET /api/lancamentos/LOTE-2026-0002 tentativa 3/3 falhou: ReadTimeout: HTTPConnectionPool(host='127.0.0.1', port=5050): Read timed out. (read timeout=5)
2026-11-13 21:53:50,110 | INFO | EXEC-20261113-215326 | G7 | LOTE-2026-0002 | gateway -> nao
2026-11-13 21:53:50,110 | ERROR | EXEC-20261113-215326 | T9 | LOTE-2026-0002 | falha tratada: portal_timeout (3 tentativas esgotadas)
2026-11-13 21:53:50,115 | INFO | EXEC-20261113-215326 | T10 | LOTE-2026-0002 | status falha motivo ['portal_timeout']
2026-11-13 21:53:55,149 | WARNING | EXEC-20261113-215326 | T9 | LOTE-2026-0003 | API GET /api/lancamentos/LOTE-2026-0003 tentativa 1/3 falhou: ReadTimeout: HTTPConnectionPool(host='127.0.0.1', port=5050): Read timed out. (read timeout=5)
2026-11-13 21:54:02,158 | WARNING | EXEC-20261113-215326 | T9 | LOTE-2026-0003 | API GET /api/lancamentos/LOTE-2026-0003 tentativa 2/3 falhou: ReadTimeout: HTTPConnectionPool(host='127.0.0.1', port=5050): Read timed out. (read timeout=5)
2026-11-13 21:54:11,171 | WARNING | EXEC-20261113-215326 | T9 | LOTE-2026-0003 | API GET /api/lancamentos/LOTE-2026-0003 tentativa 3/3 falhou: ReadTimeout: HTTPConnectionPool(host='127.0.0.1', port=5050): Read timed out. (read timeout=5)
2026-11-13 21:54:11,171 | INFO | EXEC-20261113-215326 | G7 | LOTE-2026-0003 | gateway -> nao
2026-11-13 21:54:11,171 | ERROR | EXEC-20261113-215326 | T9 | LOTE-2026-0003 | falha tratada: portal_timeout (3 tentativas esgotadas)
2026-11-13 21:54:11,174 | INFO | EXEC-20261113-215326 | T10 | LOTE-2026-0003 | status falha motivo ['portal_timeout']
```

## Resultado

| lote_id | status | motivo | protocolo |
|---|---|---|---|
| LOTE-2026-0002 | falha | portal_timeout |  |
| LOTE-2026-0003 | falha | portal_timeout |  |

Falhas tratadas registradas no relatório: 2. Execução terminou com relatório (`relatorio_EXEC-20261113-215326.md`).

## Retomada (portal normal, mesma pasta)

Comando: `python executar_robo.py --trabalho saida/cenarios/portal_lento`

| lote_id | status | motivo | protocolo |
|---|---|---|---|
| LOTE-2026-0002 | processado |  | SIM-000001 |
| LOTE-2026-0003 | processado |  | SIM-000002 |

```
2026-11-13 21:54:17,112 | INFO | EXEC-20261113-215414 | G4 | LOTE-2026-0002 | gateway -> retomar
2026-11-13 21:54:17,112 | INFO | EXEC-20261113-215414 | T4 | LOTE-2026-0002 | retomando lote pendente da etapa T9 (motivo anterior ['portal_timeout'])
2026-11-13 21:54:20,414 | INFO | EXEC-20261113-215414 | T9 | LOTE-2026-0002 | lançamento confirmado pela API REST (protocolo SIM-000001, meio selenium)
2026-11-13 21:54:20,418 | INFO | EXEC-20261113-215414 | T10 | LOTE-2026-0002 | status processado motivo []
2026-11-13 21:54:20,419 | INFO | EXEC-20261113-215414 | G4 | LOTE-2026-0003 | gateway -> retomar
2026-11-13 21:54:20,419 | INFO | EXEC-20261113-215414 | T4 | LOTE-2026-0003 | retomando lote pendente da etapa T9 (motivo anterior ['portal_timeout'])
2026-11-13 21:54:22,359 | INFO | EXEC-20261113-215414 | T9 | LOTE-2026-0003 | lançamento confirmado pela API REST (protocolo SIM-000002, meio selenium)
2026-11-13 21:54:22,366 | INFO | EXEC-20261113-215414 | T10 | LOTE-2026-0003 | status processado motivo []
```
