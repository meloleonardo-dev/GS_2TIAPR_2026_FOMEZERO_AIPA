# Idempotência (rodar duas vezes não lança de novo)

Comandos: `python executar_robo.py --limpar` (1ª) e depois `python executar_robo.py` (2ª), mesma pasta e mesmo banco do portal SIMULADO. Contagem lida da API do portal (`GET /api/resumo`) no fim de cada execução.

| execução | lançamentos no portal (total) | processados nesta execução | duplicados ignorados |
|---|---|---|---|
| 1ª EXEC-20261113-215131 | 3 | 3 | 1 |
| 2ª EXEC-20261113-215150 | 3 | 0 | 12 |

Trecho do log da 2ª execução:

```
2026-11-13 21:51:54,099 | INFO | EXEC-20261113-215150 | G4 | LOTE-2026-0001 | gateway -> duplicado
2026-11-13 21:51:54,101 | INFO | EXEC-20261113-215150 | G4 | LOTE-2026-0002 | gateway -> duplicado
2026-11-13 21:51:54,102 | INFO | EXEC-20261113-215150 | G4 | LOTE-2026-0003 | gateway -> duplicado
2026-11-13 21:51:54,103 | INFO | EXEC-20261113-215150 | G4 | LOTE-2026-0005 | gateway -> duplicado
2026-11-13 21:51:54,103 | INFO | EXEC-20261113-215150 | G4 | LOTE-2026-0006 | gateway -> duplicado
2026-11-13 21:51:54,104 | INFO | EXEC-20261113-215150 | G4 | LOTE-2026-0007 | gateway -> duplicado
2026-11-13 21:51:54,105 | INFO | EXEC-20261113-215150 | G4 | LOTE-2026-0008 | gateway -> duplicado
2026-11-13 21:51:54,106 | INFO | EXEC-20261113-215150 | G4 | LOTE-2026-0009 | gateway -> duplicado
2026-11-13 21:51:54,106 | INFO | EXEC-20261113-215150 | G4 | LOTE-2026-0010 | gateway -> duplicado
2026-11-13 21:51:54,107 | INFO | EXEC-20261113-215150 | G3 | LOTE-2026-0011 | gateway -> nao
2026-11-13 21:51:54,107 | INFO | EXEC-20261113-215150 | G4 | LOTE-2026-0011 | gateway -> duplicado
2026-11-13 21:51:54,108 | INFO | EXEC-20261113-215150 | G3 | indice10 | gateway -> nao
2026-11-13 21:51:54,108 | INFO | EXEC-20261113-215150 | G4 | indice10 | gateway -> duplicado
2026-11-13 21:51:54,109 | INFO | EXEC-20261113-215150 | G4 | LOTE-2026-0002 | gateway -> duplicado
2026-11-13 21:51:54,109 | INFO | EXEC-20261113-215150 | G2 | LOTE-2026-0004 | gateway -> nao (em_transporte)
```
