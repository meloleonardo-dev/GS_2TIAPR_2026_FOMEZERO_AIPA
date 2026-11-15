# Conjunto cego v2: medição única (2026-11-13)

> Conjunto cego v2: 60 textos SINTÉTICOS (12 por classe), escritos e rotulados pelo agente de IA da AIPA, congelados (SHA-256 registrado) antes de qualquer mudança no modelo e medidos uma única vez no fim do TAR-013; sem revisão humana (DEC-044). O mesmo agente escreveu o cego e depois ajustou o gerador v2: o modelo não viu o cego, mas o autor sim (limite registrado). n = 60 é pequeno.

- Arquivo `dados/sinteticos/ocorrencias_cego_v2.csv`, SHA-256 `BB432927BCCB1F27586DB9EDB5702F2397EF21C33A2F12D94E0EF85AD698FF89`: **igual ao congelado** (`cego_v2_CONGELADO.md`), conferido pelo script antes de qualquer predição.
- Medido em 2026-11-13T21:48:44 com os modelos salvos por `treinar_modelo.py` (sem treino nem ajuste aqui).
- Linha de base: palavras-chave + extração do kg v1 (a mesma do TAR-012).

## Resultado

**n = 60** (sem_ocorrencia: 12, avaria: 12, divergencia_quantidade: 12, problema_temperatura: 12, ilegivel_outro: 12)

| métrica | ocorrencia-v1 | ocorrencia-v2 | linha de base (palavras-chave) |
|---|---|---|---|
| acurácia | 0.65 | 0.7333 | 0.4833 |
| F1 macro | 0.64 | 0.7339 | 0.4873 |
| falso automático (roteamento R4 a R7) | 1 | 0 | 13 |
| seguiriam automático | 2 de 60 | 4 de 60 | 18 de 60 |
| sem_ocorrencia que seguiriam automático | 1 de 12 | 4 de 12 | 5 de 12 |
| kg recebido exato (±0,01 kg) | 50 de 60 | 51 de 60 | (extração v1) |
| limiar de confiança | 0.7 | 0.7 | não se aplica |

Por classe (ocorrencia-v1):

| classe | precisão | revocação | F1 | suporte |
|---|---|---|---|---|
| sem_ocorrencia | 0.8333 | 0.4167 | 0.5556 | 12 |
| avaria | 0.5556 | 0.4167 | 0.4762 | 12 |
| divergencia_quantidade | 0.5294 | 0.75 | 0.6207 | 12 |
| problema_temperatura | 0.625 | 0.8333 | 0.7143 | 12 |
| ilegivel_outro | 0.8333 | 0.8333 | 0.8333 | 12 |

Matriz de confusão (ocorrencia-v1):

| real \ previsto | sem_ocorrencia | avaria | divergencia_quantidade | problema_temperatura | ilegivel_outro |
|---|---|---|---|---|---|
| sem_ocorrencia | 5 | 1 | 3 | 1 | 2 |
| avaria | 1 | 5 | 4 | 2 | 0 |
| divergencia_quantidade | 0 | 2 | 9 | 1 | 0 |
| problema_temperatura | 0 | 1 | 1 | 10 | 0 |
| ilegivel_outro | 0 | 0 | 0 | 2 | 10 |

Extração do kg (ocorrencia-v1, extração v1): 50 de 60 exatos; dos 48 com kg no gabarito, 5 não encontrados e 5 com valor errado; 0 sem kg no gabarito receberam um kg.

Por classe (ocorrencia-v2):

| classe | precisão | revocação | F1 | suporte |
|---|---|---|---|---|
| sem_ocorrencia | 0.6667 | 0.6667 | 0.6667 | 12 |
| avaria | 0.6923 | 0.75 | 0.72 | 12 |
| divergencia_quantidade | 0.5833 | 0.5833 | 0.5833 | 12 |
| problema_temperatura | 0.8182 | 0.75 | 0.7826 | 12 |
| ilegivel_outro | 0.9167 | 0.9167 | 0.9167 | 12 |

Matriz de confusão (ocorrencia-v2):

| real \ previsto | sem_ocorrencia | avaria | divergencia_quantidade | problema_temperatura | ilegivel_outro |
|---|---|---|---|---|---|
| sem_ocorrencia | 8 | 2 | 1 | 0 | 1 |
| avaria | 1 | 9 | 1 | 1 | 0 |
| divergencia_quantidade | 2 | 2 | 7 | 1 | 0 |
| problema_temperatura | 1 | 0 | 2 | 9 | 0 |
| ilegivel_outro | 0 | 0 | 1 | 0 | 11 |

Extração do kg (ocorrencia-v2, extração v2): 51 de 60 exatos; dos 48 com kg no gabarito, 3 não encontrados e 6 com valor errado; 0 sem kg no gabarito receberam um kg.

Matriz de confusão (linha de base):

| real \ previsto | sem_ocorrencia | avaria | divergencia_quantidade | problema_temperatura | ilegivel_outro |
|---|---|---|---|---|---|
| sem_ocorrencia | 6 | 2 | 2 | 2 | 0 |
| avaria | 8 | 2 | 1 | 0 | 1 |
| divergencia_quantidade | 8 | 0 | 4 | 0 | 0 |
| problema_temperatura | 6 | 0 | 1 | 5 | 0 |
| ilegivel_outro | 0 | 0 | 0 | 0 | 12 |

## Erros de classificação (ocorrencia-v1): 21

| id | texto | real | previsto | confiança | falso automático | causa (heurística) |
|---|---|---|---|---|---|---|
| CV2-03 | blz, 22kg de feijao preto na mão. nenhum pacote furado nem nada | sem_ocorrencia | avaria | 0.522 | não | vocabulário não visto no treino (8/12 palavras: blz, preto, mao, nenhum, pacote) |
| CV2-04 | Conferimos na balança: 14,5 kg de queijo minas, bem gelado, sem nenhum problema. Obrigada à equipe! | sem_ocorrencia | problema_temperatura | 0.4913 | não | vocabulário não visto no treino (8/15 palavras: conferimos, balanca, minas, bem, nenhum) |
| CV2-05 | rcbd 9 kg tomate td ok vlw | sem_ocorrencia | divergencia_quantidade | 0.2976 | não | vocabulário não visto no treino (3/6 palavras: rcbd, td, vlw) |
| CV2-06 | nao faltou nada, os quarenta e cinco quilos de batata doce bateram com o que tava no app | sem_ocorrencia | divergencia_quantidade | 0.5932 | não | palavras compartilhadas entre classes no treino |
| CV2-08 | chegô os seis kilo de laranja q vcs mandaram, as criança amaram kkk | sem_ocorrencia | ilegivel_outro | 0.3649 | não | vocabulário não visto no treino (10/13 palavras: chego, os, kilo, q, vcs) |
| CV2-09 | pode dar baixa aí, onze quilos e meio de pão doce entregue aqui na creche, nada amassado | sem_ocorrencia | ilegivel_outro | 0.4777 | não | vocabulário não visto no treino (10/17 palavras: dar, baixa, ai, onze, meio) |
| CV2-11 | a van passou aqui umas 10h e deixou 16 kg de frango congelado, durinho ainda, ja foi pro freezer | sem_ocorrencia | divergencia_quantidade | 0.2864 | não | vocabulário não visto no treino (12/18 palavras: van, passou, aqui, umas, h) |
| CV2-14 | o pacote de açúcar rasgou na descida da van, perdemos uns 2kg dos 25 que vieram | avaria | divergencia_quantidade | 0.5563 | não | palavras compartilhadas entre classes no treino |
| CV2-15 | chegou as melancia mas duas tavam rachada e vazando, 30 kg ao todo | avaria | problema_temperatura | 0.3927 | não | vocabulário não visto no treino (8/12 palavras: as, melancia, duas, tavam, rachada) |
| CV2-16 | Infelizmente parte das alfaces veio murcha e com folha apodrecida, mais ou menos metade dos 8 kg | avaria | divergencia_quantidade | 0.5353 | não | vocabulário não visto no treino (9/16 palavras: infelizmente, das, alfaces, murcha, folha) |
| CV2-20 | garrafa de óleo veio trincada e melou tudo, 18 kg de mantimento | avaria | sem_ocorrencia | 0.8205 | sim | nenhuma palavra de ocorrência conhecida pelo modelo |
| CV2-21 | boa tarde! recebemos sim a doação de 40 kg de batata, mas uns 5 kg estavam brotados e com bicho, separamos pra descartar. o resto ja foi pras famílias | avaria | divergencia_quantidade | 0.3668 | não | palavras compartilhadas entre classes no treino |
| CV2-22 | biscoito todo esfarelado, os pacotes chegaram esmagados embaixo das caixas de leite, nove quilos | avaria | divergencia_quantidade | 0.463 | não | vocabulário não visto no treino (9/14 palavras: biscoito, todo, esfarelado, os, pacotes) |
| CV2-24 | uva toda espremida e azeda dentro da caixa, foram 6 kg | avaria | problema_temperatura | 0.508 | não | vocabulário não visto no treino (6/10 palavras: uva, toda, espremida, azeda, dentro) |
| CV2-28 | Recebemos 12 kg de carne, mas não os 16 que estavam previstos. | divergencia_quantidade | avaria | 0.4821 | não | palavras compartilhadas entre classes no treino |
| CV2-31 | Bom dia. A doação chegou, porém incompleta: das quatro caixas de banana anunciadas recebemos três, aproximadamente 21 kg. | divergencia_quantidade | avaria | 0.3485 | não | palavras compartilhadas entre classes no treino |
| CV2-32 | tá errado o peso, chegou 5,5 kg de peixe e no app aparece 9 | divergencia_quantidade | problema_temperatura | 0.6121 | não | vocabulário não visto no treino (6/12 palavras: ta, errado, peso, no, app) |
| CV2-39 | sorvete virou sopa kkk, 6kg | problema_temperatura | avaria | 0.4134 | não | vocabulário não visto no treino (4/5 palavras: sorvete, virou, sopa, kkk) |
| CV2-45 | o freezer do carro deu pau no meio do caminho e a polpa de fruta descongelou, 8 kg | problema_temperatura | divergencia_quantidade | 0.5917 | não | vocabulário não visto no treino (10/17 palavras: freezer, carro, deu, pau, no) |
| CV2-51 | aaaaaa errei o grupo desculpa | ilegivel_outro | problema_temperatura | 0.3015 | não | vocabulário não visto no treino (4/5 palavras: aaaaaa, errei, grupo, desculpa) |
| CV2-58 | segue o print da tela | ilegivel_outro | problema_temperatura | 0.5586 | não | vocabulário não visto no treino (3/5 palavras: segue, print, tela) |

Erros de extração do kg (ocorrencia-v1): 10

| id | texto | kg gabarito | kg extraído |
|---|---|---|---|
| CV2-01 | oi gente aqui é da cozinha da vila, passando só pra dizer q chegou a doação, eram uns dezoito quilos de mandioca e já tá tudo lavado na geladeira, deus abençoe | 18.0 | None |
| CV2-12 | Obg pela força!! sete kg de uva e 3 kg de morango, tudo bonito | 10.0 | 7.0 |
| CV2-13 | [áudio transcrito] oi então os ovos chegaram né mas umas três bandejas vieram tudo quebrada escorrendo na caixa, no total era vinte quilos | 20.0 | None |
| CV2-14 | o pacote de açúcar rasgou na descida da van, perdemos uns 2kg dos 25 que vieram | 25.0 | 2.0 |
| CV2-16 | Infelizmente parte das alfaces veio murcha e com folha apodrecida, mais ou menos metade dos 8 kg | 8.0 | None |
| CV2-19 | a caixa desmontou no caminho e os pães caíram no chão do caminhão, ficaram sujos, eram 10 quilos | 10.0 | None |
| CV2-23 | tem saco de feijao com caruncho, uns dois de cinco quilos cada, total recebido 20kg | 20.0 | 5.0 |
| CV2-25 | [áudio transcrito] oi, aqui chegou só uma parte né, era pra ser trinta quilo de arroz e veio uns vinte, o rapaz falou que o resto vem semana que vem | 20.0 | None |
| CV2-26 | contei 3 sacos de 5kg, mas no sistema tá 25 kg | 15.0 | 5.0 |
| CV2-27 | no papel do motorista constava 50 kg de laranja, pesamos aqui e deu quarenta e um | 41.0 | 50.0 |

## Erros de classificação (ocorrencia-v2): 16

| id | texto | real | previsto | confiança | falso automático | causa (heurística) |
|---|---|---|---|---|---|---|
| CV2-03 | blz, 22kg de feijao preto na mão. nenhum pacote furado nem nada | sem_ocorrencia | avaria | 0.6404 | não | palavras compartilhadas entre classes no treino |
| CV2-06 | nao faltou nada, os quarenta e cinco quilos de batata doce bateram com o que tava no app | sem_ocorrencia | divergencia_quantidade | 0.8836 | não | palavras compartilhadas entre classes no treino |
| CV2-08 | chegô os seis kilo de laranja q vcs mandaram, as criança amaram kkk | sem_ocorrencia | ilegivel_outro | 0.3701 | não | palavras compartilhadas entre classes no treino |
| CV2-09 | pode dar baixa aí, onze quilos e meio de pão doce entregue aqui na creche, nada amassado | sem_ocorrencia | avaria | 0.3484 | não | palavras compartilhadas entre classes no treino |
| CV2-19 | a caixa desmontou no caminho e os pães caíram no chão do caminhão, ficaram sujos, eram 10 quilos | avaria | divergencia_quantidade | 0.5877 | não | palavras compartilhadas entre classes no treino |
| CV2-20 | garrafa de óleo veio trincada e melou tudo, 18 kg de mantimento | avaria | sem_ocorrencia | 0.6807 | não | nenhuma palavra de ocorrência conhecida pelo modelo |
| CV2-24 | uva toda espremida e azeda dentro da caixa, foram 6 kg | avaria | problema_temperatura | 0.5241 | não | vocabulário não visto no treino (5/10 palavras: uva, toda, espremida, azeda, foram) |
| CV2-28 | Recebemos 12 kg de carne, mas não os 16 que estavam previstos. | divergencia_quantidade | avaria | 0.6486 | não | palavras compartilhadas entre classes no treino |
| CV2-30 | pessoal da logística, só pra registrar: o lote veio menor, 7 kg de cenoura em vez de 10 | divergencia_quantidade | sem_ocorrencia | 0.4768 | não | nenhuma palavra de ocorrência conhecida pelo modelo |
| CV2-31 | Bom dia. A doação chegou, porém incompleta: das quatro caixas de banana anunciadas recebemos três, aproximadamente 21 kg. | divergencia_quantidade | avaria | 0.5174 | não | palavras compartilhadas entre classes no treino |
| CV2-32 | tá errado o peso, chegou 5,5 kg de peixe e no app aparece 9 | divergencia_quantidade | problema_temperatura | 0.5477 | não | palavras compartilhadas entre classes no treino |
| CV2-35 | conferi e deu trinta e cinco quilos de macarrão, a doação anunciada era de cinquenta, ninguém avisou da diferença | divergencia_quantidade | sem_ocorrencia | 0.559 | não | nenhuma palavra de ocorrência conhecida pelo modelo |
| CV2-39 | sorvete virou sopa kkk, 6kg | problema_temperatura | divergencia_quantidade | 0.395 | não | vocabulário não visto no treino (4/5 palavras: sorvete, virou, sopa, kkk) |
| CV2-41 | a entrega atrasou e os 9 kg de presunto passaram a tarde no porta-malas, chegou abafado | problema_temperatura | sem_ocorrencia | 0.5336 | não | nenhuma palavra de ocorrência conhecida pelo modelo |
| CV2-46 | Recebemos as 30 marmitas (uns 15 kg) mas já chegaram frias e sem o aquecimento que foi combinado, ficaram mais de 4 h fora | problema_temperatura | divergencia_quantidade | 0.6826 | não | palavras compartilhadas entre classes no treino |
| CV2-55 | deixa no portão 2, do lado da farmácia | ilegivel_outro | divergencia_quantidade | 0.4243 | não | vocabulário não visto no treino (4/7 palavras: deixa, portao, lado, farmacia) |

Erros de extração do kg (ocorrencia-v2): 9

| id | texto | kg gabarito | kg extraído |
|---|---|---|---|
| CV2-01 | oi gente aqui é da cozinha da vila, passando só pra dizer q chegou a doação, eram uns dezoito quilos de mandioca e já tá tudo lavado na geladeira, deus abençoe | 18.0 | None |
| CV2-12 | Obg pela força!! sete kg de uva e 3 kg de morango, tudo bonito | 10.0 | 7.0 |
| CV2-13 | [áudio transcrito] oi então os ovos chegaram né mas umas três bandejas vieram tudo quebrada escorrendo na caixa, no total era vinte quilos | 20.0 | None |
| CV2-14 | o pacote de açúcar rasgou na descida da van, perdemos uns 2kg dos 25 que vieram | 25.0 | 2.0 |
| CV2-19 | a caixa desmontou no caminho e os pães caíram no chão do caminhão, ficaram sujos, eram 10 quilos | 10.0 | None |
| CV2-23 | tem saco de feijao com caruncho, uns dois de cinco quilos cada, total recebido 20kg | 20.0 | 5.0 |
| CV2-26 | contei 3 sacos de 5kg, mas no sistema tá 25 kg | 15.0 | 5.0 |
| CV2-27 | no papel do motorista constava 50 kg de laranja, pesamos aqui e deu quarenta e um | 41.0 | 50.0 |
| CV2-31 | Bom dia. A doação chegou, porém incompleta: das quatro caixas de banana anunciadas recebemos três, aproximadamente 21 kg. | 21.0 | 3.0 |

## Cobertura de vocabulário (palavras inteiras, sem números)

| item | valor |
|---|---|
| palavras distintas no cego | 370 |
| conhecidas pelo vocabulário de palavras da v1 | 93 |
| conhecidas pelo vocabulário de palavras da v2 | 186 |
| palavras do cego que só o gerador v2 trouxe (não estão no treino v1 nem no desenvolvimento) | ai, amassada, amassado, bonito, caminhao, creche, deus, dezoito, distribuicao, entao, entendi, falo, familias, fruta, furado, geladeira, gente, h, h., kilo, manha, meio, ne, nenhum, obrigada, onze, pacote, pacotes, pegou, pela, perdemos, pesamos, pro, q, quase, quebrada, rapaz, rasgou, resto, sacos, semana, separamos, sistema, tem, tipo, total, treze, vazando, vcs, vou |

## Regra de decisão (registrada antes da medição)

- v2 só entra no robô se o falso automático dela não for maior que o da v1 em nenhum conjunto (registrada em cego_v2_CONGELADO.md antes da medição).
- Falso automático no cego: v1 = 1, v2 = 0.
