# F10 · navegador/WebDriver não inicia -> contingência API

Comando: `python executar_robo.py --cenario navegador_indisponivel` (código de saída 0). Pasta de trabalho separada `saida/cenarios/navegador_indisponivel/`. Dados SIMULADOS; portal SIMULADO.

## Trecho do log

```
2026-11-13 21:55:12,053 | ERROR | EXEC-20261113-215509 | T9 | LOTE-2026-0002 | navegador não iniciou (NoSuchDriverException: Message: Unable to obtain driver for MicrosoftEdge; For documentation on this error, please visit: https://www.selenium.dev/documentation/webdriver/troubleshoot); contingência pela API REST
2026-11-13 21:55:12,094 | INFO | EXEC-20261113-215509 | T9 | LOTE-2026-0002 | lançamento confirmado pela API REST (protocolo SIM-000001, meio api_contingencia)
2026-11-13 21:55:12,099 | INFO | EXEC-20261113-215509 | T10 | LOTE-2026-0002 | status processado motivo []
2026-11-13 21:55:12,191 | ERROR | EXEC-20261113-215509 | T9 | LOTE-2026-0003 | navegador não iniciou (NoSuchDriverException: Message: Unable to obtain driver for MicrosoftEdge; For documentation on this error, please visit: https://www.selenium.dev/documentation/webdriver/troubleshoot); contingência pela API REST
2026-11-13 21:55:12,236 | INFO | EXEC-20261113-215509 | T9 | LOTE-2026-0003 | lançamento confirmado pela API REST (protocolo SIM-000002, meio api_contingencia)
2026-11-13 21:55:12,241 | INFO | EXEC-20261113-215509 | T10 | LOTE-2026-0003 | status processado motivo []
```

## Resultado

| lote_id | status | motivo | protocolo |
|---|---|---|---|
| LOTE-2026-0002 | processado |  | SIM-000001 |
| LOTE-2026-0003 | processado |  | SIM-000002 |

Falhas tratadas registradas no relatório: 2. Execução terminou com relatório (`relatorio_EXEC-20261113-215509.md`).
