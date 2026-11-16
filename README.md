# FOMEZERO · Robô pós-entrega (AI for Robotic Process Automation)

Global Solution 2026.2 · FIAP · Tecnólogo em Inteligência Artificial · tema CitizenTech.

> **Protótipo acadêmico. Dados SIMULADOS (sintéticos) e portal do parceiro SIMULADO.** Nenhum módulo declara que um alimento é seguro para consumo. CO₂ evitado é **estimativa**; pontos e Selo Verde ESG são **regra de demonstração**, não certificação.

## Integrantes
| Nome | RM |
|---|---|
| Erick Miguel | 564896 |
| Leonardo Melo | 567097 |
| Luna Oliveira | 564215 |

## Problema
O FOMEZERO liga quem tem excedente de alimento (o **doador**: mercado, padaria, restaurante) a quem precisa (o **beneficiário**: ONG, cozinha comunitária, cidadão), para reduzir o desperdício e a insegurança alimentar. Depois que o **lote de doação** é entregue, alguém precisa conferir o que o beneficiário confirmou, registrar o impacto, emitir o **Termo de Doação** e lançar o reconhecimento do doador (pontos e **Selo Verde ESG**) no sistema da prefeitura ou da empresa parceira. Feito à mão, isso é repetitivo, sujeito a erro e pode premiar um lote com problema (avaria, divergência de quantidade, quebra da cadeia de frio).

**Público e papel no fluxo:** o **doador** recebe pontos, Selo Verde ESG e o Termo; o **beneficiário** escreve a confirmação de entrega (é a entrada da IA; aparece só por código); a prefeitura ou empresa parceira tem o portal (aqui **simulado**); o operador do FOMEZERO decide os casos da fila de revisão humana.

## O que o robô faz (entrada → IA → saída)
`python executar_robo.py` executa, numa execução contínua, o processo modelado em BPMN (T1 a T12):
1. confere disco, memória e pastas (psutil) e sobe o portal SIMULADO se ele não estiver no ar;
2. lê os lotes de doação entregues (`entrada/lotes_entregues.json`, formato proposto do módulo FEMD) e as mensagens da IoT (`entrada/iot/*.log`, capturas `mosquitto_sub`; os dois logs de 10 e 11/11/2026 são **dado físico real** do ESP32 do grupo);
3. valida e manda o inválido para a quarentena; descarta duplicados (SQLite);
4. **IA:** spaCy extrai o kg recebido do texto do beneficiário e um classificador (TF-IDF de palavras e de pedaços de palavra + regressão logística, scikit-learn) diz se houve ocorrência (avaria, divergência, temperatura, texto ilegível), com uma confiança;
5. **regras inteligentes (R1 a R11):** ocorrência, baixa confiança, kg que não bate (cadastrado × informado × escrito no texto), alerta `quebra_cadeia_frio` da IoT, triagem por foto que pediu avaliação ou viu deterioração, ou problema marcado pelo beneficiário → **revisão humana**, sem pontos;
6. lote validado: calcula o **CO₂ evitado (kg CO₂eq)** = kg recebido validado × 2,54 (estimativa; FAO 2013), os **pontos** (10 por kg) e o **Selo Verde ESG** do doador pelo acumulado (Bronze 50 kg, Prata 200 kg, Ouro 500 kg);
7. gera o **Termo de Doação** em PDF e confere o PDF;
8. lança no portal SIMULADO com **Selenium** e confirma pela **API REST**;
9. grava o CT-04 (para o FEMD), o CT-05 (indicadores para o GABA e histórico para o CQIA), a fila de revisão, o log e o relatório de execução com tempo de ciclo e taxa de erros por tarefa.

Os temas da disciplina e onde cada um entra estão no [QUADRO_DE_TEMAS.md](QUADRO_DE_TEMAS.md).

## Como executar
Pré-requisitos: Windows, Linux ou macOS com **Python 3.14** (testado com 3.14.4 em 2026-11-15; também foi executado com 3.13.5 em 2026-11-13, com os mesmos resultados) e **Microsoft Edge** (ou Chrome, com `--param NAVEGADOR=chrome`). Na primeira execução o Selenium Manager baixa o driver do navegador (precisa de internet).

```powershell
# 1. ambiente (dentro desta pasta)
py -3.14 -m venv .venv              # Linux/macOS: python3.14 -m venv .venv
.\.venv\Scripts\activate             # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

# 2. chaves (ver a seção abaixo)
copy .env.exemplo .env               # Linux/macOS: cp .env.exemplo .env

# 3. dados sintéticos, modelo e robô
python gerar_dados_sinteticos.py     # 300 + 500 textos rotulados, 12 lotes de demonstração, prepara entrada/
python treinar_modelo.py             # treina e mede v1 e v2 -> modelos/ e evidencias/metricas_ia_AAAA-MM-DD.md (cerca de 1 min)
python executar_robo.py              # PONTO DE ENTRADA: roda o robô do início ao fim
```

Opcional: `python medir_cego_v2.py` mede de novo o conjunto cego v2 (confere o SHA-256 antes; os modelos são determinísticos, então sai o mesmo número publicado). No Windows, se o console mostrar acentos trocados, rode antes `$env:PYTHONIOENCODING="utf-8"` (só afeta a tela; os arquivos são gravados em UTF-8). O robô não precisa baixar modelo do spaCy (usa só o tokenizador do português que vem no pacote).

**Se aparecer `ImportError: DLL load failed ... Uma política de Controle de Aplicativo bloqueou este arquivo`:** é o Smart App Control do Windows bloqueando um arquivo compilado de uma biblioteca (aconteceu nesta máquina com o spaCy no Python 3.13). Não é preciso desligar nenhuma proteção: apague a pasta `.venv` e crie de novo com o Python 3.14 (`py -3.14 -m venv .venv`), que foi a versão testada. Registro em `evidencias/ambiente_python314_2026-11-15.md`.

Saídas em `saida/`: `termos/` (PDF), `ct04/`, `ct05/`, `revisao/fila_revisao.csv`, `relatorios/` (MD e JSON), `logs/`, `prints/` (telas do Selenium), `quarentena/`, `backup/`. O portal SIMULADO sobe sozinho em `http://127.0.0.1:5050` e é encerrado no fim (para abrir à mão: `python portal_simulado/app.py`).

Outras opções:
| Comando | O que faz |
|---|---|
| `python executar_robo.py --limpar` | apaga as saídas e o banco do portal antes (execução limpa) |
| `python executar_robo.py --headful` | mostra o navegador (para gravar a demonstração) |
| `python executar_robo.py --cenario portal_fora` | demonstra uma falha (cenários: `arquivo_ausente`, `iot_ausente`, `modelo_ausente`, `iot_invalido`, `portal_fora`, `portal_lento`, `erro_api`, `json_invalido`, `credencial_invalida`, `navegador_indisponivel`, `disco_cheio`), numa pasta separada `saida/cenarios/<nome>/` |
| `python -m pytest testes -v` | testes automáticos (extração, regras, cálculos, adaptadores, idempotência, contrato JSON, Selenium) |
| `python gerar_evidencias.py` | regenera todas as evidências em `evidencias/` executando o robô de verdade (cerca de 4 min) |

**Revisão humana.** Lotes retidos vão para `saida/revisao/fila_revisao.csv` (abre no Excel; há uma cópia de leitura em `fila_revisao.xlsx`). O operador preenche `decisao` (`aprovado` ou `reprovado`), `kg_aprovado` e `revisor` (código, não nome) e salva como `entrada/decisoes_revisao.csv`; a próxima execução lê o arquivo: aprovado segue para cálculo, Termo e lançamento; reprovado fica sem pontos. O robô nunca diz se o alimento é "seguro" ou "impróprio": quem decide é a pessoa.

## Serviço local para o portal FOMEZERO (confirmação automática)
O portal do FOMEZERO (módulo FEMD) pode chamar o robô na hora em que o beneficiário confirma a entrega, sem exportar e importar arquivos:
```
python servico_aipa.py            # http://127.0.0.1:5070, só neste computador (Ctrl+C para parar)
python servico_aipa.py --limpar   # começa do zero (apaga servico_dados/)
```
O frontend envia o lote entregue (CT-03, com `quantidade_recebida_kg`, `divergencias_informadas` e o resumo `triagem_visual` da VCIA) para `POST /api/lotes`; o serviço guarda o lote em `servico_dados/entrada/` e executa **o mesmo robô** (validação, idempotência, IA, regras, CO₂, pontos, selo, Termo em PDF, Selenium + API no portal SIMULADO) e devolve o CT-04 em cerca de 8 s. `GET /api/resultados` devolve todos os CT-04 e `GET /api/termos/<lote_id>` o Termo de Doação em PDF. A revisão humana também passa pelo serviço: `GET /api/revisao` lista a fila (texto já mascarado) e `POST /api/revisao/<lote_id>` com `decisao` (`aprovado` ou `reprovado`), `kg_aprovado` e `revisor` (código, nunca nome) grava a decisão no mesmo `entrada/decisoes_revisao.csv` e roda o robô: aprovado segue para cálculo, Termo e lançamento; reprovado fica sem pontos. Opções: `--porta`, `--trabalho` (outra pasta de estado) e `--portal-porta`. Aceita chamadas só de `localhost`/`127.0.0.1`; a IoT lida é a física versionada (`dados/iot_fisico/`). O estado fica em `servico_dados/` (fora do repositório). Porta 5060 não serve: o Chrome a bloqueia.

## Agendamento (execução automática, sem intervenção)
- Pelo próprio robô (biblioteca `schedule`): `python executar_robo.py --agendar 10` roda agora e a cada 10 minutos (Ctrl+C para parar).
- Windows (Agendador de Tarefas): `schtasks /Create /SC MINUTE /MO 10 /TN FOMEZERO_AIPA /TR "C:\caminho\AIPA\.venv\Scripts\python.exe C:\caminho\AIPA\executar_robo.py"`.
- Linux (cron): `*/10 * * * * cd /caminho/AIPA && .venv/bin/python executar_robo.py >> saida/cron.log 2>&1`.

A cada execução o robô só trata o que é novo: lote já processado é ignorado (idempotência), lote que falhou por causa do portal é retomado.

## Como configurar as chaves
O robô não usa chave de serviço externo. As únicas credenciais são as do **portal SIMULADO** local (usuário e senha do login, token da API e chave de sessão), lidas de um arquivo `.env` que **não vai para o repositório** (está no `.gitignore`):
1. copie `.env.exemplo` para `.env`;
2. troque os valores de exemplo (`PORTAL_USUARIO`, `PORTAL_SENHA`, `PORTAL_API_TOKEN`, `PORTAL_CHAVE_SESSAO`) por valores seus. O robô e o portal simulado leem o mesmo `.env`, então qualquer valor funciona desde que esteja nele.

Nenhuma senha ou token aparece no código ou no log. Sem o `.env`, o robô avisa no log e marca os lançamentos como `falha: credenciais_invalidas` (nada é lançado).

## Evidências de validação
Tudo em [`evidencias/`](evidencias/LEIA-ME.md), gerado por execução real:
- **IA**, dados **sintéticos, rotulados por gerador/IA, sem revisão humana**. O robô usa o modelo `ocorrencia-v2` (TF-IDF de palavras e de pedaços de palavra, `char_wb` 3 a 5, + regressão logística; treino com os 225 textos da v1 + 500 sintéticos mais variados do gerador v2; extração do kg v2). A `ocorrencia-v1` (TAR-012) continua salva para comparação. Três conjuntos:

  | conjunto | n | acurácia v1 / v2 / palavras-chave | F1 macro v1 / v2 / palavras-chave | falso automático v1 / v2 / palavras-chave | seguiriam automático v1 / v2 | kg exato v1 / v2 |
  |---|---|---|---|---|---|---|
  | teste sintético (25% dos 300 da v1) | 75 | 0,987 / 1,000 / 0,920 | 0,987 / 1,000 / 0,921 | 0 / 0 / 1 | 10 / 13 | 75 / 75 |
  | desenvolvimento (30 "fora do molde") | 30 | 0,467 / 1,000 / 0,400 | 0,461 / 1,000 / 0,252 | 0 / 0 / 10 | 0 / 6 | 26 / 30 |
  | **cego v2 (medição única)** | 60 | **0,650 / 0,733 / 0,483** | **0,640 / 0,734 / 0,487** | **1 / 0 / 13** | 2 / 4 | 50 / 51 |

  "Falso automático" = texto com ocorrência real que seguiria sem revisão humana (meta 0). **Como ler:** o teste sintético sai dos mesmos moldes do treino e é otimista. Os 30 "fora do molde" foram usados para ajustar o gerador e a extração da v2, então o 1,000 da v2 neles **não mede generalização** (só mostra que os erros vistos foram corrigidos). Quem mede é o **cego v2**: 60 textos novos (áudio transcrito, WhatsApp, abreviações, erros, gírias, números por extenso, frases longas, negações), escritos e congelados com SHA-256 **antes** de qualquer mudança no modelo e medidos uma única vez no fim (`evidencias/cego_v2_CONGELADO.md`, `evidencias/metricas_cego_v2_2026-11-13.md`). Nele a v2 acerta 44 de 60 (a v1 39, as palavras-chave 29) e nenhum texto com ocorrência seguiria sozinho; a v1 deixaria passar 1 (CV2-20, "garrafa de óleo veio trincada e melou tudo, 18 kg", previsto `sem_ocorrencia` com confiança 0,82). Pela regra fixada antes da medição (a v2 só entra se não aumentar o falso automático em nenhum conjunto), o robô usa a v2.

  **Análise dos erros do cego (v2, 16 de 60).** Acertos por classe: sem_ocorrencia 8 de 12, avaria 9 de 12, divergência 7 de 12, temperatura 9 de 12, ilegível 11 de 12. O que ainda erra: **negações** ("nenhum pacote furado nem nada" → avaria; "nao faltou nada" → divergência com confiança 0,88; "nada amassado" → avaria), porque o modelo pesa a palavra do problema e não entende o "não"; **divergência dita sem palavra de falta** ("veio menor, 7 kg em vez de 10", "anunciada era de cinquenta") → `sem_ocorrencia`; **temperatura dita por consequência** ("passaram a tarde no porta-malas, chegou abafado" → `sem_ocorrencia`; "sorvete virou sopa"). Esses três erros perigosos (ocorrência prevista como `sem_ocorrencia`: CV2-30, 35, 41) e o CV2-20 tiveram confiança 0,48 a 0,68, abaixo do limiar 0,70, e iriam para revisão humana: a margem do CV2-20 (0,68) é pequena. Extração do kg: 51 de 60 (nenhum kg inventado em texto sem kg); erra soma de dois produtos ("sete kg de uva e 3 kg de morango"), conta ("3 sacos de 5kg"), "perdemos uns 2kg dos 25 que vieram", "eram 10 quilos" e "no total era vinte quilos" (o "era" é lido como valor de referência), "constava 50 kg… deu quarenta e um" (fica o primeiro valor) e "recebemos três, aproximadamente 21 kg" (a v2 pegou o 3; a v1 acertava este). Esses erros não foram corrigidos de propósito: corrigir olhando o cego o deixaria de ser cego. **Limites:** n = 60 é pequeno; o cego foi escrito pelo mesmo agente de IA que depois ajustou o gerador (o modelo não viu o cego, mas o autor sim; as palavras do cego que só o gerador v2 trouxe estão listadas no arquivo de métricas). Com linguagem real o robô ainda funciona mais como triagem (4 de 60 seguiriam sozinhos) do que como automação. Tabelas completas em `evidencias/metricas_ia_2026-11-13.md` (v1 x v2), `evidencias/metricas_cego_v2_2026-11-13.md` (cego) e `evidencias/arquivo_v1/` (o que foi publicado no TAR-012).
- **Processo** (`evidencias/execucao_normal/relatorio_EXEC-20261113-215131.md`, com a `ocorrencia-v2`): 13 registros (12 lotes de demonstração + 1 em transporte) em 13,3 s; 3 processados (Termo de Doação em PDF, lançamento pelo Selenium e confirmação pela API; o DOADOR-001 chega a 57 kg e ganha o Selo Verde ESG Bronze), 6 em revisão humana, 2 inválidos em quarentena, 1 duplicado ignorado. **Conferência com o gabarito: 12 de 13 registros (11 de 12 lotes de demonstração)**, igual à v1. O erro: o LOTE-2026-0006 ("recebemos 6 kg de refeição pronta, muito obrigado") foi classificado como avaria com confiança 0,63 (na v1, 0,32) e foi para revisão humana em vez de seguir sozinho, um erro conservador (nenhum lote com problema passou sem revisão); não foi ajustado no modelo para não treinar no caso de teste. O LOTE-2026-0001, sintético e cruzado com o alerta **físico real** `quebra_cadeia_frio` do log de 11/11/2026 (ativação às 13:32:35Z, depois de uma normalização), foi para revisão humana como esperado (texto "chegaram 8 kg de iogurte": `sem_ocorrencia` com confiança 0,32, baixa; o alerta já bastava). Tempo de ciclo por lote: média 484 ms, máximo 2,9 s; a tarefa mais lenta é o lançamento no portal (T9, média 2,8 s).
- **Falhas tratadas e demonstradas:** F1 a F11 em `evidencias/falhas/` (comando, trecho do log e resultado de cada uma), idempotência em `evidencias/idempotencia/`, revisão humana em `evidencias/revisao_humana/`, agendamento em `evidencias/agendamento/`, pytest em `evidencias/pytest/`.

**Limites:** os textos de confirmação são sintéticos (não existe ainda o campo no app do grupo) e ninguém do grupo revisou os rótulos; o vocabulário é pequeno; os nomes dos campos do lote são uma proposta do módulo FEMD ainda não confirmada (o robô usa um mapa de campos em `config/` para trocar sem mexer no código); as chaves das mensagens da IoT são as observadas nos logs, com confirmação pendente; o fator de CO₂ e as regras de pontos e selo ainda não foram aceitos pelo grupo; o custo por processo não é medido.

## Proteção de dados, ética e ODS
O robô usa só dados sintéticos identificados como SIMULADO e os logs reais do sensor da caixa térmica, que não têm dado pessoal; doador e beneficiário aparecem por código, o texto livre do beneficiário não sai do robô (nem para o portal, nem para outros módulos), passa por máscara de telefone, e-mail e CPF antes de ir para a fila de revisão, e senhas e tokens ficam fora do código, no `.env`. Do ponto de vista ético, a IA não decide sobre a segurança do alimento: ela só separa o que pode seguir sozinho do que precisa de uma pessoa, e qualquer ocorrência, dúvida ou alerta de quebra da cadeia de frio vai para revisão humana, sem premiar o doador; o CO₂ evitado é publicado como estimativa com a metodologia junto, e pontos e Selo Verde ESG são reconhecimento interno de demonstração (não é o "Selo Doador de Alimentos" da Lei 15.224/2025). O protótipo se liga ao **ODS 2** (Fome Zero), ao **ODS 12**, meta **12.3** (reduzir pela metade o desperdício de alimentos), ao registrar e reconhecer a doação que chegou de fato, e ao **ODS 13** (ação climática), ao estimar as emissões associadas ao alimento que deixou de ser descartado, sem afirmar impacto medido.

## Ferramentas (todas gratuitas)
Python 3.14 (testado também com 3.13) e bibliotecas de código aberto, com a licença declarada nos metadados do pacote instalado (conferido em 2026-11-13): selenium 4.52.0 (Apache-2.0), flask 3.1.3 (BSD-3-Clause), spacy 3.8.18 (MIT), scikit-learn 1.9.1 (BSD-3-Clause), pandas 3.1.1 (BSD-3-Clause), openpyxl 3.1.5 (MIT), pypdf 7.1.0 (BSD-3-Clause), fpdf2 2.9.0 (LGPL-3.0-only), requests 2.34.2 (Apache-2.0), schedule 1.2.2 (MIT), psutil 7.2.2 (BSD-3-Clause), pytest 9.2.0 (MIT), python-dotenv 1.2.4 (BSD-3-Clause), joblib 1.6.0 (BSD-3-Clause), tzdata 2026.6 (Apache-2.0). Navegador Microsoft Edge (gratuito) com o driver baixado pelo Selenium Manager. Nenhum serviço pago e nenhuma API externa.

## Estrutura
```
executar_robo.py           PONTO DE ENTRADA
servico_aipa.py            serviço local (Flask) para o portal FOMEZERO chamar o robô na confirmação da entrega
gerar_dados_sinteticos.py  dados sintéticos e entrada/
treinar_modelo.py          treino e métricas da IA (v1 e v2)
medir_cego_v2.py           medição do conjunto cego v2 (confere o hash; opcional)
gerar_evidencias.py        regenera evidencias/ (opcional)
config/                    parametros.json, mapas de campos (CT-03 e IoT)
robo/                      processo.py (BPMN), nlp_ocorrencia.py, regras.py, calculos.py, termo_pdf.py,
                           portal_selenium.py, portal_api.py, banco.py, saidas.py, relatorio.py,
                           observabilidade.py, adaptadores/, cenarios.py
portal_simulado/           portal SIMULADO (Flask) com banco próprio e modos de falha
dados/                     sinteticos/, iot_fisico/ (logs reais, origem: repositório da IoT, commit 4b09c42), cenarios/
modelos/                   ocorrencia-v1.joblib e ocorrencia-v2.joblib (gerados), metadados_v1.json, metadados_v2.json
testes/                    pytest
evidencias/                evidências de validação
contrato/                  proposta dos contratos CT-03, CT-04, CT-05 e IoT
```

## Outros módulos do FOMEZERO (mesmo grupo)
- PLN: Fábrica de Corpus (corpus de documentos oficiais sobre doação segura de alimentos): https://github.com/meloleonardo-dev/GS_2TIAPR_2026_FOMEZERO_PLN
- GENAI: assistente de consulta para doadores (RAG sobre o corpus da PLN): https://github.com/meloleonardo-dev/GS_2TIAPR_2026_FOMEZERO_GENAI
