# F8 · erro de API (HTTP 500)

Comando: `python executar_robo.py --cenario erro_api` (código de saída 0). Pasta de trabalho separada `saida/cenarios/erro_api/`. Dados SIMULADOS; portal SIMULADO.

## Trecho do log

```
2026-11-13 21:54:31,391 | WARNING | EXEC-20261113-215428 | T9 | LOTE-2026-0002 | API GET /api/lancamentos/LOTE-2026-0002 tentativa 1/3 falhou: HTTPError: HTTP 500
2026-11-13 21:54:33,394 | WARNING | EXEC-20261113-215428 | T9 | LOTE-2026-0002 | API GET /api/lancamentos/LOTE-2026-0002 tentativa 2/3 falhou: HTTPError: HTTP 500
2026-11-13 21:54:37,398 | WARNING | EXEC-20261113-215428 | T9 | LOTE-2026-0002 | API GET /api/lancamentos/LOTE-2026-0002 tentativa 3/3 falhou: HTTPError: HTTP 500
2026-11-13 21:54:37,398 | INFO | EXEC-20261113-215428 | G7 | LOTE-2026-0002 | gateway -> nao
2026-11-13 21:54:37,398 | ERROR | EXEC-20261113-215428 | T9 | LOTE-2026-0002 | falha tratada: confirmacao_api_falhou (3 tentativas esgotadas)
2026-11-13 21:54:37,401 | INFO | EXEC-20261113-215428 | T10 | LOTE-2026-0002 | status falha motivo ['confirmacao_api_falhou']
2026-11-13 21:54:37,444 | WARNING | EXEC-20261113-215428 | T9 | LOTE-2026-0003 | API GET /api/lancamentos/LOTE-2026-0003 tentativa 1/3 falhou: HTTPError: HTTP 500
2026-11-13 21:54:39,472 | WARNING | EXEC-20261113-215428 | T9 | LOTE-2026-0003 | API GET /api/lancamentos/LOTE-2026-0003 tentativa 2/3 falhou: HTTPError: HTTP 500
2026-11-13 21:54:43,498 | WARNING | EXEC-20261113-215428 | T9 | LOTE-2026-0003 | API GET /api/lancamentos/LOTE-2026-0003 tentativa 3/3 falhou: HTTPError: HTTP 500
2026-11-13 21:54:43,499 | INFO | EXEC-20261113-215428 | G7 | LOTE-2026-0003 | gateway -> nao
2026-11-13 21:54:43,499 | ERROR | EXEC-20261113-215428 | T9 | LOTE-2026-0003 | falha tratada: confirmacao_api_falhou (3 tentativas esgotadas)
2026-11-13 21:54:43,506 | INFO | EXEC-20261113-215428 | T10 | LOTE-2026-0003 | status falha motivo ['confirmacao_api_falhou']
```

## Resultado

| lote_id | status | motivo | protocolo |
|---|---|---|---|
| LOTE-2026-0002 | falha | confirmacao_api_falhou |  |
| LOTE-2026-0003 | falha | confirmacao_api_falhou |  |

Falhas tratadas registradas no relatório: 2. Execução terminou com relatório (`relatorio_EXEC-20261113-215428.md`).
