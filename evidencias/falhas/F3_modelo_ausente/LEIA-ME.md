# F3 · modelo de IA ausente

Comando: `python executar_robo.py --cenario modelo_ausente` (código de saída 0). Pasta de trabalho separada `saida/cenarios/modelo_ausente/`. Dados SIMULADOS; portal SIMULADO.

## Trecho do log

```
2026-11-13 21:52:44,640 | ERROR | EXEC-20261113-215242 | T2 | - | modelo indisponível (FileNotFoundError: inexistente-v0.joblib): todos os lotes vão para revisão humana
2026-11-13 21:52:44,726 | INFO | EXEC-20261113-215242 | G5 | LOTE-2026-0001 | gateway -> revisao_humana
2026-11-13 21:52:44,729 | INFO | EXEC-20261113-215242 | T10 | LOTE-2026-0001 | status revisao_humana motivo ['alerta_iot_quebra_cadeia_frio', 'modelo_indisponivel']
2026-11-13 21:52:44,730 | INFO | EXEC-20261113-215242 | G5 | LOTE-2026-0002 | gateway -> revisao_humana
2026-11-13 21:52:44,733 | INFO | EXEC-20261113-215242 | T10 | LOTE-2026-0002 | status revisao_humana motivo ['modelo_indisponivel']
2026-11-13 21:52:44,734 | INFO | EXEC-20261113-215242 | G5 | LOTE-2026-0003 | gateway -> revisao_humana
2026-11-13 21:52:44,737 | INFO | EXEC-20261113-215242 | T10 | LOTE-2026-0003 | status revisao_humana motivo ['modelo_indisponivel']
2026-11-13 21:52:44,738 | INFO | EXEC-20261113-215242 | G5 | LOTE-2026-0005 | gateway -> revisao_humana
2026-11-13 21:52:44,740 | INFO | EXEC-20261113-215242 | T10 | LOTE-2026-0005 | status revisao_humana motivo ['modelo_indisponivel']
2026-11-13 21:52:44,741 | INFO | EXEC-20261113-215242 | G5 | LOTE-2026-0006 | gateway -> revisao_humana
2026-11-13 21:52:44,744 | INFO | EXEC-20261113-215242 | T10 | LOTE-2026-0006 | status revisao_humana motivo ['modelo_indisponivel']
2026-11-13 21:52:44,745 | INFO | EXEC-20261113-215242 | G5 | LOTE-2026-0007 | gateway -> revisao_humana
2026-11-13 21:52:44,748 | INFO | EXEC-20261113-215242 | T10 | LOTE-2026-0007 | status revisao_humana motivo ['modelo_indisponivel']
2026-11-13 21:52:44,748 | INFO | EXEC-20261113-215242 | G5 | LOTE-2026-0008 | gateway -> revisao_humana
2026-11-13 21:52:44,751 | INFO | EXEC-20261113-215242 | T10 | LOTE-2026-0008 | status revisao_humana motivo ['modelo_indisponivel', 'divergencia_kg']
2026-11-13 21:52:44,752 | INFO | EXEC-20261113-215242 | G5 | LOTE-2026-0009 | gateway -> revisao_humana
2026-11-13 21:52:44,755 | INFO | EXEC-20261113-215242 | T10 | LOTE-2026-0009 | status revisao_humana motivo ['modelo_indisponivel']
2026-11-13 21:52:44,755 | INFO | EXEC-20261113-215242 | G5 | LOTE-2026-0010 | gateway -> revisao_humana
2026-11-13 21:52:44,760 | INFO | EXEC-20261113-215242 | T10 | LOTE-2026-0010 | status revisao_humana motivo ['modelo_indisponivel', 'sem_confirmacao']
2026-11-13 21:52:44,760 | INFO | EXEC-20261113-215242 | G3 | LOTE-2026-0011 | gateway -> nao
2026-11-13 21:52:44,763 | WARNING | EXEC-20261113-215242 | T3 | LOTE-2026-0011 | campo inválido: quantidade_disponibilizada_kg
2026-11-13 21:52:44,766 | INFO | EXEC-20261113-215242 | T10 | LOTE-2026-0011 | status falha motivo ['dado_invalido:quantidade_disponibilizada_kg']
2026-11-13 21:52:44,767 | INFO | EXEC-20261113-215242 | G3 | indice10 | gateway -> nao
2026-11-13 21:52:44,769 | WARNING | EXEC-20261113-215242 | T3 | indice10 | campo inválido: lote_id
2026-11-13 21:52:44,770 | INFO | EXEC-20261113-215242 | T10 | indice10 | status falha motivo ['dado_invalido:lote_id']
2026-11-13 21:52:44,770 | INFO | EXEC-20261113-215242 | G4 | LOTE-2026-0002 | gateway -> duplicado
2026-11-13 21:52:44,770 | INFO | EXEC-20261113-215242 | G2 | LOTE-2026-0004 | gateway -> nao (em_transporte)
```

## Resultado

| lote_id | status | motivo | protocolo |
|---|---|---|---|
| LOTE-2026-0001 | revisao_humana | alerta_iot_quebra_cadeia_frio, modelo_indisponivel |  |
| LOTE-2026-0002 | revisao_humana | modelo_indisponivel |  |
| LOTE-2026-0003 | revisao_humana | modelo_indisponivel |  |
| LOTE-2026-0005 | revisao_humana | modelo_indisponivel |  |
| LOTE-2026-0006 | revisao_humana | modelo_indisponivel |  |
| LOTE-2026-0007 | revisao_humana | modelo_indisponivel |  |
| LOTE-2026-0008 | revisao_humana | modelo_indisponivel, divergencia_kg |  |
| LOTE-2026-0009 | revisao_humana | modelo_indisponivel |  |
| LOTE-2026-0010 | revisao_humana | modelo_indisponivel, sem_confirmacao |  |
| LOTE-2026-0011 | falha | dado_invalido:quantidade_disponibilizada_kg |  |
| (vazio) | falha | dado_invalido:lote_id |  |
| LOTE-2026-0002 | ignorado_duplicado |  |  |
| LOTE-2026-0004 | ignorado_nao_entregue |  |  |

Falhas tratadas registradas no relatório: 13. Execução terminou com relatório (`relatorio_EXEC-20261113-215242.md`).
