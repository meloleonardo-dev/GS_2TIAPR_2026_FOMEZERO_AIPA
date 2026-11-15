# F9 · senha errada no login do portal

Comando: `python executar_robo.py --cenario credencial_invalida` (código de saída 0). Pasta de trabalho separada `saida/cenarios/credencial_invalida/`. Dados SIMULADOS; portal SIMULADO.

## Trecho do log

```
2026-11-13 21:55:03,650 | INFO | EXEC-20261113-215458 | G7 | LOTE-2026-0002 | gateway -> nao
2026-11-13 21:55:03,650 | ERROR | EXEC-20261113-215458 | T9 | LOTE-2026-0002 | falha tratada: credenciais_invalidas (login recusado pelo portal (sem retry))
2026-11-13 21:55:03,654 | INFO | EXEC-20261113-215458 | T10 | LOTE-2026-0002 | status falha motivo ['credenciais_invalidas']
2026-11-13 21:55:03,695 | INFO | EXEC-20261113-215458 | G7 | LOTE-2026-0003 | gateway -> nao
2026-11-13 21:55:03,695 | ERROR | EXEC-20261113-215458 | T9 | LOTE-2026-0003 | falha tratada: credenciais_invalidas (login já recusado nesta execução)
2026-11-13 21:55:03,699 | INFO | EXEC-20261113-215458 | T10 | LOTE-2026-0003 | status falha motivo ['credenciais_invalidas']
```

## Resultado

| lote_id | status | motivo | protocolo |
|---|---|---|---|
| LOTE-2026-0002 | falha | credenciais_invalidas |  |
| LOTE-2026-0003 | falha | credenciais_invalidas |  |

Falhas tratadas registradas no relatório: 2. Execução terminou com relatório (`relatorio_EXEC-20261113-215458.md`).
