# F11 · disco abaixo do mínimo

Comando: `python executar_robo.py --cenario disco_cheio` (código de saída 3). Pasta de trabalho separada `saida/cenarios/disco_cheio/`. Dados SIMULADOS; portal SIMULADO.

## Trecho do log

```
2026-11-13 21:55:15,615 | CRITICAL | EXEC-20261113-215515 | T1 | - | disco livre 57115.5 MB < mínimo 999999999 MB
2026-11-13 21:55:15,615 | INFO | EXEC-20261113-215515 | G0 | - | gateway -> nao_ambiente
2026-11-13 21:55:15,615 | CRITICAL | EXEC-20261113-215515 | E-fim | - | execução abortada com segurança antes de gravar qualquer saída de lote
```

## Resultado

Nenhum lote processado: [{'falha': 'F11', 'lote_id': None, 'motivo': 'disco_insuficiente', 'caminho_seguro': 'aborta antes de gravar; relatório explica'}]

Falhas tratadas registradas no relatório: 1. Execução terminou com relatório (`relatorio_EXEC-20261113-215515.md`).
