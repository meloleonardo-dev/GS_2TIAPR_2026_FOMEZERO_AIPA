# F8b · erro de API (JSON inválido)

Comando: `python executar_robo.py --cenario json_invalido` (código de saída 0). Pasta de trabalho separada `saida/cenarios/json_invalido/`. Dados SIMULADOS; portal SIMULADO.

## Trecho do log

```
2026-11-13 21:54:49,566 | WARNING | EXEC-20261113-215446 | T9 | LOTE-2026-0002 | API GET /api/lancamentos/LOTE-2026-0002 tentativa 1/3 falhou: HTTPError: JSON inválido na resposta
2026-11-13 21:54:51,570 | WARNING | EXEC-20261113-215446 | T9 | LOTE-2026-0002 | API GET /api/lancamentos/LOTE-2026-0002 tentativa 2/3 falhou: HTTPError: JSON inválido na resposta
2026-11-13 21:54:55,593 | WARNING | EXEC-20261113-215446 | T9 | LOTE-2026-0002 | API GET /api/lancamentos/LOTE-2026-0002 tentativa 3/3 falhou: HTTPError: JSON inválido na resposta
2026-11-13 21:54:55,594 | INFO | EXEC-20261113-215446 | G7 | LOTE-2026-0002 | gateway -> nao
2026-11-13 21:54:55,594 | ERROR | EXEC-20261113-215446 | T9 | LOTE-2026-0002 | falha tratada: confirmacao_api_falhou (3 tentativas esgotadas)
2026-11-13 21:54:55,596 | INFO | EXEC-20261113-215446 | T10 | LOTE-2026-0002 | status falha motivo ['confirmacao_api_falhou']
```

## Resultado

| lote_id | status | motivo | protocolo |
|---|---|---|---|
| LOTE-2026-0002 | falha | confirmacao_api_falhou |  |

Falhas tratadas registradas no relatório: 1. Execução terminou com relatório (`relatorio_EXEC-20261113-215446.md`).
