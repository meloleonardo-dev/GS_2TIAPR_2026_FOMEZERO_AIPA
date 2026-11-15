# Métricas da IA da AIPA (2026-11-13)

> Geradas por `python treinar_modelo.py` (execução real). **Dados SINTÉTICOS, rotulados por gerador/IA, sem revisão humana.** Conjuntos SINTÉTICOS: os 300 textos têm rótulo por construção do gerador e os 30 'fora do molde' foram escritos e rotulados pelo agente de IA da AIPA; nenhum texto teve revisão humana (DEC-044). Os moldes são poucos e o vocabulário é pequeno, então as métricas do teste tendem a ser otimistas; o conjunto 'fora do molde' mede um pouco da generalização, com n = 30. Não há texto real de beneficiário.

- Modelo: `ocorrencia-v1` (TF-IDF (1-2 gramas, tokenizador spaCy pt, sem acento, números -> numtok) + LogisticRegression (class_weight=balanced, C=10.0)); semente 42.
- Conjunto: 300 sintéticos (60 por classe), divisão 75/25 estratificada: treino 225, teste 75; mais 30 'fora do molde' (6 por classe), só para teste.
- LIMIAR_CONFIANCA usado: **0.7** (partida 0,70; calibrado só no treino com validação cruzada de 5 partes).
- "Falso automático" = texto com ocorrência real (classe diferente de sem_ocorrencia) que seguiria sem revisão humana pelas regras de texto R4 a R7 (classe, confiança, kg extraído x cadastrado). Meta: 0. No robô, as regras de IoT (R1 a R3) ainda se somam a estas.

## Calibração do limiar (só treino, fora da dobra)

| limiar | falso automático (só classificador) | seguiriam automático | n |
|---|---|---|---|
| 0.7 | 0 | 30 | 225 |
| 0.75 | 0 | 26 | 225 |
| 0.8 | 0 | 20 | 225 |
| 0.85 | 0 | 11 | 225 |
| 0.9 | 0 | 3 | 225 |
| 0.95 | 0 | 0 | 225 |

## Conjunto de teste (sintético)

**n = 75** (sem_ocorrencia: 15, avaria: 15, divergencia_quantidade: 15, problema_temperatura: 15, ilegivel_outro: 15)

| métrica | ML (TF-IDF + regressão logística) | linha de base (palavras-chave) |
|---|---|---|
| acurácia | 0.9867 | 0.92 |
| F1 macro | 0.9867 | 0.9208 |
| falso automático (roteamento R4 a R7) | 0 | 1 |
| seguiriam automático | 10 de 75 | 15 de 75 |
| sem_ocorrencia que seguiriam automático | 10 de 15 | 14 de 15 |

Por classe (ML):

| classe | precisão | revocação | F1 | suporte |
|---|---|---|---|---|
| sem_ocorrencia | 1.0 | 1.0 | 1.0 | 15 |
| avaria | 0.9375 | 1.0 | 0.9677 | 15 |
| divergencia_quantidade | 1.0 | 0.9333 | 0.9655 | 15 |
| problema_temperatura | 1.0 | 1.0 | 1.0 | 15 |
| ilegivel_outro | 1.0 | 1.0 | 1.0 | 15 |

Matriz de confusão (ML):

| real \ previsto | sem_ocorrencia | avaria | divergencia_quantidade | problema_temperatura | ilegivel_outro |
|---|---|---|---|---|---|
| sem_ocorrencia | 15 | 0 | 0 | 0 | 0 |
| avaria | 0 | 15 | 0 | 0 | 0 |
| divergencia_quantidade | 0 | 1 | 14 | 0 | 0 |
| problema_temperatura | 0 | 0 | 0 | 15 | 0 |
| ilegivel_outro | 0 | 0 | 0 | 0 | 15 |

Matriz de confusão (linha de base):

| real \ previsto | sem_ocorrencia | avaria | divergencia_quantidade | problema_temperatura | ilegivel_outro |
|---|---|---|---|---|---|
| sem_ocorrencia | 14 | 0 | 1 | 0 | 0 |
| avaria | 1 | 14 | 0 | 0 | 0 |
| divergencia_quantidade | 4 | 0 | 11 | 0 | 0 |
| problema_temperatura | 0 | 0 | 0 | 15 | 0 |
| ilegivel_outro | 0 | 0 | 0 | 0 | 15 |

Extração do kg recebido (spaCy): acerto exato (±0,01 kg, inclusive 'sem kg' = 'sem kg') **75 de 75 (1.0)**; dos 59 textos com kg no gabarito, 0 não encontrados e 0 com valor errado; 0 textos sem kg no gabarito receberam um kg.

## Conjunto fora do molde

**n = 30** (sem_ocorrencia: 6, avaria: 6, divergencia_quantidade: 6, problema_temperatura: 6, ilegivel_outro: 6)

| métrica | ML (TF-IDF + regressão logística) | linha de base (palavras-chave) |
|---|---|---|
| acurácia | 0.4667 | 0.4 |
| F1 macro | 0.4612 | 0.2523 |
| falso automático (roteamento R4 a R7) | 0 | 10 |
| seguiriam automático | 0 de 30 | 16 de 30 |
| sem_ocorrencia que seguiriam automático | 0 de 6 | 6 de 6 |

Por classe (ML):

| classe | precisão | revocação | F1 | suporte |
|---|---|---|---|---|
| sem_ocorrencia | 0.25 | 0.1667 | 0.2 | 6 |
| avaria | 0.3333 | 0.3333 | 0.3333 | 6 |
| divergencia_quantidade | 0.4 | 0.6667 | 0.5 | 6 |
| problema_temperatura | 0.6 | 0.5 | 0.5455 | 6 |
| ilegivel_outro | 0.8 | 0.6667 | 0.7273 | 6 |

Matriz de confusão (ML):

| real \ previsto | sem_ocorrencia | avaria | divergencia_quantidade | problema_temperatura | ilegivel_outro |
|---|---|---|---|---|---|
| sem_ocorrencia | 1 | 1 | 3 | 0 | 1 |
| avaria | 2 | 2 | 2 | 0 | 0 |
| divergencia_quantidade | 1 | 1 | 4 | 0 | 0 |
| problema_temperatura | 0 | 2 | 1 | 3 | 0 |
| ilegivel_outro | 0 | 0 | 0 | 2 | 4 |

Matriz de confusão (linha de base):

| real \ previsto | sem_ocorrencia | avaria | divergencia_quantidade | problema_temperatura | ilegivel_outro |
|---|---|---|---|---|---|
| sem_ocorrencia | 6 | 0 | 0 | 0 | 0 |
| avaria | 3 | 0 | 1 | 0 | 2 |
| divergencia_quantidade | 5 | 0 | 0 | 0 | 1 |
| problema_temperatura | 6 | 0 | 0 | 0 | 0 |
| ilegivel_outro | 0 | 0 | 0 | 0 | 6 |

Extração do kg recebido (spaCy): acerto exato (±0,01 kg, inclusive 'sem kg' = 'sem kg') **26 de 30 (0.8667)**; dos 22 textos com kg no gabarito, 1 não encontrados e 3 com valor errado; 0 textos sem kg no gabarito receberam um kg.

## Análise de erros de classificação (ML): 17

A causa é uma heurística automática (proporção de palavras fora do vocabulário do treino), não um julgamento humano.

| conjunto | id | texto | real | previsto | confiança | causa provável (heurística) |
|---|---|---|---|---|---|---|
| teste | SIN-0128 | recebi 53,5 kg de maçã, faltando 22 kilos | divergencia_quantidade | avaria | 0.4269 | palavras compartilhadas entre classes nos moldes |
| fora_do_molde | FM-01 | show, os 8 quilo de banana tão aqui na mesa | sem_ocorrencia | ilegivel_outro | 0.3734 | vocabulário não visto no treino (5/9 palavras: show, os, tao, aqui, mesa) |
| fora_do_molde | FM-02 | valeu demais!!! 15kg de arroz já na despensa da cozinha | sem_ocorrencia | avaria | 0.2584 | vocabulário não visto no treino (5/10 palavras: valeu, demais, ja, despensa, cozinha) |
| fora_do_molde | FM-03 | Pessoal, passando pra avisar que a doação de hoje (doze quilos de laranja) foi guardada e a criançada vai adorar, gratidão | sem_ocorrencia | divergencia_quantidade | 0.3343 | palavras compartilhadas entre classes nos moldes |
| fora_do_molde | FM-04 | beleza, 3,5 kg de pão de forma guardados | sem_ocorrencia | divergencia_quantidade | 0.4601 | palavras compartilhadas entre classes nos moldes |
| fora_do_molde | FM-05 | a moça do mercado deixou 40 kilos de batata, conferido e guardado | sem_ocorrencia | divergencia_quantidade | 0.5882 | palavras compartilhadas entre classes nos moldes |
| fora_do_molde | FM-07 | 6 kg de maçã aqui, mas metade tá machucada e pisada | avaria | sem_ocorrencia | 0.3317 | vocabulário não visto no treino (5/10 palavras: aqui, metade, ta, machucada, pisada) |
| fora_do_molde | FM-08 | o saco do arroz abriu no caminho e espalhou grão pelo carro todo, sobrou uns 9 kg | avaria | divergencia_quantidade | 0.5668 | vocabulário não visto no treino (11/16 palavras: saco, abriu, no, caminho, espalhou) |
| fora_do_molde | FM-10 | pão veio todo esmagado, deu pra aproveitar pouco dos 5 kg | avaria | divergencia_quantidade | 0.6658 | vocabulário não visto no treino (6/10 palavras: todo, esmagado, deu, pra, aproveitar) |
| fora_do_molde | FM-11 | banana preta e melando, bicho em volta, 7 kg | avaria | sem_ocorrencia | 0.3046 | vocabulário não visto no treino (4/8 palavras: preta, melando, bicho, volta) |
| fora_do_molde | FM-13 | pediram vinte, vieram doze quilos | divergencia_quantidade | sem_ocorrencia | 0.3157 | nenhuma palavra de ocorrência conhecida pelo modelo |
| fora_do_molde | FM-15 | no app tava 25 kg mas na balança deu 18 | divergencia_quantidade | avaria | 0.3853 | vocabulário não visto no treino (5/8 palavras: no, app, tava, balanca, deu) |
| fora_do_molde | FM-19 | o iogurte tava suando e mole, parece que ficou no sol, 6 kg | problema_temperatura | divergencia_quantidade | 0.4037 | vocabulário não visto no treino (7/12 palavras: tava, suando, mole, parece, ficou) |
| fora_do_molde | FM-23 | carne moída veio pingando água e com cheiro forte, 5 kg | problema_temperatura | avaria | 0.3766 | palavras compartilhadas entre classes nos moldes |
| fora_do_molde | FM-24 | o motorista disse que o carro ficou parado no calor por duas horas com o presunto dentro, recebemos 4 kg | problema_temperatura | avaria | 0.2949 | vocabulário não visto no treino (11/19 palavras: motorista, disse, carro, ficou, parado) |
| fora_do_molde | FM-27 | manda o comprovante no zap | ilegivel_outro | problema_temperatura | 0.3015 | vocabulário não visto no treino (4/5 palavras: manda, comprovante, no, zap) |
| fora_do_molde | FM-30 | esse número é da ong? | ilegivel_outro | problema_temperatura | 0.5189 | vocabulário não visto no treino (3/5 palavras: esse, numero, ong) |

## Erros de extração do kg: 4

| conjunto | id | texto | kg gabarito | kg extraído |
|---|---|---|---|---|
| fora_do_molde | FM-10 | pão veio todo esmagado, deu pra aproveitar pouco dos 5 kg | 5.0 | None |
| fora_do_molde | FM-12 | as bandejas de ovos chegaram com várias trincadas, mais ou menos dois quilos perdidos de dez | 10.0 | 2.0 |
| fora_do_molde | FM-15 | no app tava 25 kg mas na balança deu 18 | 18.0 | 25.0 |
| fora_do_molde | FM-17 | tinha que ser 40 kilos de laranja, mas o motorista trouxe 32 | 32.0 | 40.0 |

## Palavras de maior peso por classe (interpretabilidade)

| classe | palavras/bigramas |
|---|---|
| avaria | com, amassados, unidades, estavam, vieram amassados, recebi, recebemos, podres |
| divergencia_quantidade | faltaram, faltando, mas o, recebidos, quilos, uma caixa, apenas, uma |
| ilegivel_outro | xpto, xpto numtok, entregue, foi, confirmo, boa, favor, pode |
| problema_temperatura | quente, chegou, temperatura, morno, gelo, estava, peixe, da refrigeracao |
| sem_ocorrencia | tudo, chegou certinho, certinho, certo, tudo certo, confirmada, entrega confirmada, entrega |

## Limites

- Conjuntos SINTÉTICOS: os 300 textos têm rótulo por construção do gerador e os 30 'fora do molde' foram escritos e rotulados pelo agente de IA da AIPA; nenhum texto teve revisão humana (DEC-044). Os moldes são poucos e o vocabulário é pequeno, então as métricas do teste tendem a ser otimistas; o conjunto 'fora do molde' mede um pouco da generalização, com n = 30. Não há texto real de beneficiário.
- O kg extraído só é usado se bater com o cadastrado (tolerância 5% ou 0,5 kg); se não bater ou faltar, o lote vai para revisão humana. Nenhuma saída da IA diz se o alimento é seguro para consumo.
