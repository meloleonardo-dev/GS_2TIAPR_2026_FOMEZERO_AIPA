# Conjunto cego v2 — CONGELADO (TAR-013, passo 1)

| item | valor |
|---|---|
| arquivo | `dados/sinteticos/ocorrencias_cego_v2.csv` |
| SHA-256 | `BB432927BCCB1F27586DB9EDB5702F2397EF21C33A2F12D94E0EF85AD698FF89` |
| congelado em | 2026-11-13 21:35:31 -03:00 (hora local da máquina, `Get-Date`) |
| tamanho | 60 textos, 12 por classe (sem_ocorrencia, avaria, divergencia_quantidade, problema_temperatura, ilegivel_outro) |
| colunas | id; texto; classe; kg_recebido_gabarito; kg_cadastrado; origem; rotulado_por; revisao_humana |

**Origem: SINTÉTICO, escrito e rotulado pelo agente de IA da AIPA, sem revisão humana.** Nenhum texto é de beneficiário real; nenhum dado pessoal.

## Regras do congelamento
1. O arquivo foi escrito e o hash registrado **antes** de qualquer mudança no gerador, na extração do kg ou no modelo (passo 2 do TAR-013).
2. Até a medição única (passo 5), nenhum modelo, extrator ou linha de base roda sobre ele. A única checagem feita foi estrutural (60 linhas, 12 por classe, 8 colunas, 60 textos distintos), sem nenhuma predição.
3. O ajuste (passo 2) usa só o treino sintético e os 30 "fora do molde" (agora conjunto de desenvolvimento).
4. Antes de medir, o hash é conferido; se não bater, a medição não vale e isso é registrado.
5. O resultado é publicado como sair, inclusive se for pior.

## Como os textos foram escritos
- Estilos variados: áudio transcrito (`[áudio transcrito]`), WhatsApp, abreviações (`rcbd`, `td`, `vlw`, `kd`), erros (`chegô`, `faltano`), gírias (`deu pau`, `virou sopa`), números por extenso (`trinta e dois quilos`, `onze quilos e meio`), frases longas com mais de um fato, negações (`nenhum pacote furado`, `nao faltou nada`, `não veio refrigerado`).
- Sem copiar os moldes de `gerar_dados_sinteticos.py` nem os 30 "fora do molde".
- `kg_recebido_gabarito` = massa que chegou ao beneficiário segundo o texto (na avaria, o total recebido, inclusive a parte danificada; na divergência, o que de fato chegou). Vazio quando o texto não informa kg. Em CV2-12 o gabarito é a soma (7 + 3 = 10). Em CV2-26 é 3 × 5 = 15.
- `kg_cadastrado`: igual ao recebido quando não há divergência; na divergência, o valor que o texto indica como esperado (CV2-31: 4 caixas de cerca de 7 kg = 28, valor suposto pelo agente; CV2-36: 3 caixas de 8 kg = 24). Nos ilegíveis, 10 (valor neutro, como no "fora do molde").
- Casos de rótulo discutível ficaram com a classe do problema principal: CV2-18 (mamão mole e manchado) = avaria; CV2-41 (presunto no porta-malas a tarde toda) e CV2-46 (marmitas que chegaram frias) = problema_temperatura; CV2-54 (ainda não chegou nada) = ilegivel_outro.

## Regra de decisão registrada ANTES da medição (2026-11-13, depois do passo 2 e antes do passo 5)
- Candidato: `ocorrencia-v2` = TF-IDF de palavras (1-2) + TF-IDF de caracteres `char_wb` (3-5) + regressão logística (C = 10, `class_weight="balanced"`), treinado com os 225 de treino da v1 + 500 sintéticos extra do gerador v2; extração do kg v2. Limiar calibrado só no treino.
- O robô passa a usar a v2 **só se** o falso automático da v2 não for maior que o da v1 em nenhum conjunto (teste sintético, desenvolvimento e cego v2). Se for maior em qualquer um, o robô continua com a v1 (as duas ficam salvas).
- Acurácia e F1 macro do cego não mudam essa regra nem levam a novo ajuste: o resultado é publicado como sair.

## Conferência do hash antes da medição (passo 5)
- 2026-11-13 21:48:41: `Get-FileHash` = `BB432927BCCB1F27586DB9EDB5702F2397EF21C33A2F12D94E0EF85AD698FF89` (igual).
- 2026-11-13 21:48:44: `python medir_cego_v2.py` conferiu de novo (SHA-256 atual = registrado neste arquivo = constante do script) e só então mediu. Saída: "hash conferido: OK".
- Resultado publicado como saiu em `metricas_cego_v2_2026-11-13.md`: acurácia v1 0,650, v2 0,733, palavras-chave 0,483; falso automático v1 1, v2 0, palavras-chave 13. Pela regra acima, o robô passou a usar a v2.
- Rodar `medir_cego_v2.py` de novo reproduz os mesmos números (modelos determinísticos); nenhum ajuste foi feito depois da medição.
