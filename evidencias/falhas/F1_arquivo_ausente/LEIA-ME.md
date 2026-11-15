# F1 · arquivo de lotes ausente

Comando: `python executar_robo.py --cenario arquivo_ausente` (código de saída 0). Pasta de trabalho separada `saida/cenarios/arquivo_ausente/`. Dados SIMULADOS; portal SIMULADO.

## Trecho do log

```
2026-11-13 21:52:34,284 | ERROR | EXEC-20261113-215231 | T2 | - | entrada_ausente: lotes_entregues.json não existe; nada a processar
2026-11-13 21:52:34,284 | INFO | EXEC-20261113-215231 | G1 | - | gateway -> nao
```

## Resultado

Nenhum lote processado: [{'falha': 'F1', 'lote_id': None, 'motivo': 'entrada_ausente', 'caminho_seguro': 'nada a processar; relatório explica; código de saída 0'}]

Falhas tratadas registradas no relatório: 1. Execução terminou com relatório (`relatorio_EXEC-20261113-215231.md`).
