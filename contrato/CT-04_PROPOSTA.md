---
id: CT-AIPA-PROPOSTA
dono: disc-aipa
versao_contrato: ct04-v0 / ct05-v0 / ct03-provisorio (modelo do Erick v1.0) / iot-observado (commit 4b09c42, PC-012)
status: RASCUNHO (proposta do Design TAR-011, 2026-11-13; nada acordado com o Erick)
---
# Contratos da AIPA: proposta (CT-03 entrada, CT-04 saída para a FEMD, CT-05 saída para GABA e CQIA, alerta da IoT)

> **Proposta, não contrato acordado.** O contrato oficial fica em `03_INTEGRACAO/CONTRATOS.md` (dono: ORQUESTRADOR). Os nomes de campo seguem o **"modelo de aplicação" proposto pelo Erick, v1.0 (11/11/2026), não confirmado** (`04_REFERENCIAS/contexto_grupo/2026-11-13_FEMD_GABA/FOMEZERO_PARAMETROS_FEMD_GABA.md`, §9). O próprio Erick o chama de proposta, por isso o robô mantém um **adaptador** com mapa de campos: se os nomes mudarem, só o mapa muda. Os campos que a AIPA precisa e que não estão nesse modelo estão marcados **"acréscimo proposto pela AIPA"**. Todos os valores dos exemplos são **SIMULADOS**.
>
> **Regras comuns:**
> 1. Nenhum campo diz que um alimento é seguro para consumo (o Erick também pede: nunca marcar `apto_para_doacao` automaticamente, §9).
> 2. **`null` = indisponível ou não calculado; nunca zero** (§9 e §11 do arquivo do Erick). Ex.: lote em revisão humana sai com `pontos: null`, `selo_verde_esg: null`, `co2_evitado_kg_co2eq: null` e o `motivo`.
> 3. Nenhum dado pessoal real. O texto livre do beneficiário **não sai** da AIPA (nem para o portal, nem para a FEMD), só a classificação.
> 4. **CO₂ evitado (kg CO₂eq) é estimativa**, sempre com `metodologia_carbono` (§3.3). **Pontos e Selo Verde ESG** seguem **regra de demonstração do FOMEZERO proposta pela AIPA** (DEC-043), **ainda não aprovada pelo grupo** (o Erick registra os critérios como pendentes, §12).

Exemplos em JSON (validáveis com `python -m json.tool`) na pasta `exemplos/`:

| Arquivo | O que é |
|---|---|
| `exemplos/ct03_lote_entregue_PROVISORIO.json` | entrada: lotes de doação entregues |
| `exemplos/iot_mensagens_OBSERVADAS.json` | entrada da IoT depois do adaptador: duas mensagens **reais** do log de 11/11/2026 (ativação e normalização), com valor bruto e origem preservados |
| `exemplos/ct04_lote_processado.json` | CT-04: lote processado (pontos e Selo Verde ESG lançados) |
| `exemplos/ct04_lote_revisao_humana.json` | CT-04: lote retido para revisão humana (`null` + motivo) |
| `exemplos/ct04_lote_falha.json` | CT-04: falha tratada (portal fora do ar) |
| `exemplos/ct05_indicadores_gaba.json` | CT-05 para a GABA |
| `exemplos/ct05_historico_entregas_cqia.csv` | CT-05 para a CQIA |

---

## 1. CT-03 (FEMD → AIPA): lote de doação entregue (ENTRADA)

**Status:** nomes = proposta do Erick v1.0, não confirmada `[PENDENTE: PEN-001, confirmação do Erick]`. O robô processa só lotes com `status_logistico = "entregue"` (estados sugeridos pelo Erick: `cadastrado`, `em_transporte`, `entregue`, `cancelado`); os outros são ignorados e contados no relatório.

### 1.1 Como o lote chega `[PENDENTE: Erick]`
A FEMD guarda dados no navegador (IDEIA_VIGENTE). Proposta mais simples: a FEMD **exporta** os lotes num arquivo JSON, que o robô lê de `entrada/`. Alternativa: o app chama a API do portal simulado. Decisão do Erick (P-AIPA-L05).

### 1.2 Campos que o robô lê
| Campo (modelo do Erick) | Tipo | Obrigatório para a AIPA | Uso no robô |
|---|---|---|---|
| `lote_id` | texto (ex.: `LOTE-2026-0002`; padrão do lote demonstrativo `LOTE-2026-0001`) | sim | idempotência; nome do Termo; chave do CT-04 |
| `doador_id` | texto (código, ex.: `DOADOR-001`) | sim | acumulado do doador → Selo Verde ESG |
| `beneficiario_id` | texto (código, ex.: `BENEF-003`) | sim | Termo e histórico; **nunca nome de pessoa** |
| `alimento_descricao` | texto | sim | Termo; contexto da IA |
| `quantidade_disponibilizada_kg` | número > 0 | sim | quantidade cadastrada pelo doador; **não** é base do CO₂ |
| `quantidade_recebida_kg` | número ≥ 0 ou `null` | não | se vier preenchida, é comparada com o kg extraído do texto do beneficiário (divergência → revisão humana) |
| `quantidade_aproveitada_kg` | número ou `null` | não | o robô **não** preenche nem infere (precisa de registro posterior, §11 do Erick) |
| `status_logistico` | `cadastrado` \| `em_transporte` \| `entregue` \| `cancelado` | sim | só `entregue` entra |
| `estado_termico` | texto bruto ou `null` | não | preservado como veio; mapeado no adaptador (ex.: `ALERTA`); **não** é decisão sanitária |
| `evento_atual` | texto bruto ou `null` | não | se mapear para `quebra_cadeia_frio`, conta como alerta da IoT |
| `entrega_confirmada_em` | data/hora ISO 8601 | sim | Termo; histórico |
| `confirmacao_entrega_texto` | texto livre do beneficiário | sim (sem ele: revisão humana, motivo `sem_confirmacao`) | **entrada da IA** (NLP + ML). **Acréscimo proposto pela AIPA**: não está no modelo do Erick; pedido de uma caixa de texto "confirmação de entrega" no app |
| `doador_nome_ficticio` | texto | não | só no Termo, marcado SIMULADO. **Acréscimo proposto pela AIPA** (opcional) |
| `beneficiario_tipo` | `ONG` \| `cozinha_comunitaria` \| `cidadao` | não | Termo e indicadores. **Acréscimo proposto pela AIPA** (opcional) |
| `simulado` | booleano | sim | `true` em toda a GS. **Acréscimo proposto pela AIPA** |

Campos do modelo do Erick que o robô **não usa**: `dispositivo_id`, `temperatura_c`, `umidade_pct`, `distancia_cm`, `caixa_presente`, `ultima_leitura_em`, `recebido_em` (são leituras da IoT; o robô não julga temperatura nem presença).

### 1.3 Adaptador
- `robo/adaptadores/ct03.py` + `config/mapa_campos_ct03.json` (`{"nome_interno": "nome_no_arquivo"}`). Hoje o mapa é identidade (nomes do Erick v1.0); se mudar, só o mapa muda.
- Converte tipos (vírgula decimal, datas); **mantém `null` como `null`**.
- Campo obrigatório ausente ou inválido → quarentena, status `falha`, motivo `dado_invalido:<campo>`; os outros lotes continuam.
- Teste automático: o mapa cobre todos os campos obrigatórios.

---

## 2. Alerta da IoT (IOT → AIPA): ENTRADA, contrato observado

**Status:** chaves **observadas nos logs `mosquitto_sub` de 10 e 11/11/2026 do repositório da IoT (commit `4b09c42`)**, copiados em `04_REFERENCIAS/contexto_grupo/2026-11-13_IOT/repo_amostras_4b09c42/` e resumidos em `CONTRATO_MQTT_OBSERVADO.md`. **Confirmação do Erick pendente (PC-012).** É o que foi publicado nessas capturas, não uma especificação: campos podem faltar em outras mensagens, e o adaptador trata a ausência.

### 2.1 O que foi observado
Prefixo `fomezero/gs2026/<rm>/lote/<lote_id>/` (no log: lote `LOTE-2026-0001`, dispositivo `esp32-caixa-01`).

| Tópico | `schema` | Chaves observadas que o robô usa |
|---|---|---|
| `telemetria` | `fomezero.telemetria.v1` | `lote_id`, `device_id`, `seq`, `ts` (ISO 8601 UTC, ex. `2026-11-11T01:14:40Z`), `ts_valido`, `temp_c`, `limite_c`, `evento` (`normal` \| `quebra_cadeia_frio`), `estado` (`FRIO_OK` \| `ALERTA`, em maiúsculas), `origem` (`fisico`). Também existem `umid_pct`, `caixa_presente`, `distancia_cm`, `uptime_ms`, que o robô guarda no bruto mas não usa |
| `alerta`, **ativação** | `fomezero.alerta.v1` | `lote_id`, `device_id`, `seq`, `ts`, `evento` (`quebra_cadeia_frio`), `temp_c`, `limite_c`, `duracao_acima_s`, `severidade` (`alta`), `acao`, `origem` |
| `alerta`, **normalização** | `fomezero.alerta.v1` | `lote_id`, `device_id`, `seq`, `ts`, `evento` (**também** `quebra_cadeia_frio`), `estado` (`normalizado`), `temp_c`; **sem** `origem`, `limite_c`, `severidade` |
| `status`, `comando` | `fomezero.status.v1`, `fomezero.ack.v1` | ignorados pelo robô (contados no relatório) |

Origens possíveis: `fisico` (ESP32 real), `wokwi`, `simulador` (`device_id` `esp32-simulado-01`), segundo `CONTRATO_MQTT_OBSERVADO.md`.

**Atenção:** a normalização chega com `evento = "quebra_cadeia_frio"`. Por isso o robô **não** classifica pelo campo `evento` sozinho: ativação e normalização são distinguidas pela presença de `estado = "normalizado"` (normalização) ou de `duracao_acima_s`/`severidade` (ativação).

### 2.2 Como o alerta chega (duas fontes aceitas, sem mexer no módulo IoT)
1. **Log do `mosquitto_sub`** (`entrada/iot/*.log`): uma linha = tópico + espaço + JSON. Os logs reais de 10 e 11/11/2026 são **dado FÍSICO real** e servem de entrada de teste do robô, citando a origem (repositório da IoT, commit `4b09c42`).
2. **Opcional:** tabelas `alerta` e `leitura` do SQLite do consumidor Python do Erick (`backend/schema.sql`: `alerta(lote_id, device_id, seq, ts, evento, temp_c, limite_c, duracao_acima_s, severidade, estado, recebido_em)`; `leitura(..., evento, estado, origem, payload_raw, ...)`). A tabela `alerta` não tem coluna `origem`: o adaptador busca a origem em `leitura` pelo mesmo `device_id`, e na falta grava `origem = null` (não infere). O banco que está no repositório tem só leituras `wokwi` e `simulador` (não físicas), segundo o mesmo arquivo.
3. **Cenários de teste SIMULADOS** (alerta ausente, valor desconhecido, ts inválido): arquivos gerados pelo gerador de dados com `origem = "simulador"`, sempre separados dos físicos.

Também é considerado, se vier, o `evento_atual`/`estado_termico` do próprio lote (CT-03), com valor bruto preservado.

### 2.3 Formato interno (depois do adaptador)
| Campo interno | Origem |
|---|---|
| `lote_id`, `device_id`, `seq`, `ts`, `ts_valido`, `temp_c`, `limite_c`, `duracao_acima_s`, `severidade` | chaves observadas, copiadas como vieram (`null` se ausentes) |
| `tipo_mensagem` | `telemetria` \| `alerta_ativacao` \| `alerta_normalizacao` \| `status` \| `ack` \| `desconhecido` (pelo sufixo do tópico e pelas regras de 2.1) |
| `evento_bruto`, `estado_bruto` | valores exatamente como vieram (ex.: `ALERTA`, `normalizado`) |
| `situacao_termica` | mapeada: `ativacao` \| `normalizacao` \| `normal` \| `desconhecido` |
| `origem` | `fisico` \| `wokwi` \| `simulador` \| `null` (como veio; nunca inferida) |
| `fonte_arquivo`, `linha`, `payload_raw` | rastreabilidade para auditoria |

O mapeamento fica em `config/mapa_campos_iot.json` (nomes das chaves e tabela de valores, comparação sem diferenciar maiúsculas: `ALERTA` → `ativacao`, `FRIO_OK` → `normal`, `normalizado` → `normalizacao`). Se o Erick confirmar outros nomes (PC-012), só o mapa muda.

### 2.4 Regra inteligente com a IoT
- **Lote com pelo menos uma ativação de `quebra_cadeia_frio` com `origem = "fisico"` no período do transporte → revisão humana** (motivo `alerta_iot_quebra_cadeia_frio`). Conta como ativação: mensagem de `alerta` de ativação, ou `telemetria` com `estado` `ALERTA`/`evento` `quebra_cadeia_frio`. **Uma normalização posterior não apaga o histórico.**
- **Período do transporte:** do início do transporte até `entrega_confirmada_em`. O modelo do Erick não tem campo de início do transporte `[PENDENTE: Erick]`; até lá, o robô usa a janela `JANELA_TRANSPORTE_HORAS` antes da entrega (parâmetro, `[HIPÓTESE]` 24 h). Mensagem com `ts_valido = false` ou `ts` ilegível conta como dentro do período (lado seguro).
- **Não misturar simulado com físico:** o parâmetro `ORIGENS_IOT_ACEITAS` define o modo da execução. Na execução de evidência física vale `["fisico"]`; mensagens `wokwi`/`simulador` são registradas no log como ignoradas. Os cenários simulados rodam em execução separada, com `["simulador"]`, e o relatório e o CT-04 saem marcados SIMULADO.
- **Fonte ausente ou ilegível** (nenhum log, nenhum banco) → o robô não sabe se houve quebra da cadeia de frio → **todos** os lotes vão para revisão humana (motivo `dados_iot_indisponiveis`).
- Linha com JSON inválido → registrada no log e ignorada, sem parar a leitura. Valor não mapeado → `desconhecido` → revisão humana (motivo `evento_iot_desconhecido`).
- Fonte presente e nenhuma ativação física para o lote no período → `alerta_iot: "sem_alerta_registrado"` (nunca "temperatura ok" nem "alimento seguro"). Lote sem nenhuma mensagem da IoT também sai como `sem_alerta_registrado`, com `iot_monitorado: false` no CT-04 (o robô não conclui nada da ausência de monitoramento).
- O robô **não** aplica limite de temperatura próprio (PEN-002) e não usa `temp_c` para decidir: só o evento da IoT. As regras da IoT (>5 °C por 30 s; recuperação <4,5 °C por 60 s) são demonstração do firmware, não norma sanitária.
- Nenhuma senha ou token do repositório da IoT é copiado ou usado.

---

## 3. CT-04 (AIPA → FEMD): pontos e Selo Verde ESG por lote (SAÍDA, `ct04-v0`)

### 3.1 Entrega
Um arquivo por lote, `saida/ct04/<lote_id>.json`, e o agregado `saida/ct04/ct04_lotes.json`. Opcional: `GET /api/ct04/<lote_id>` no portal simulado. Forma de consumo pela FEMD `[PENDENTE: Erick]`.

### 3.2 Campos
Os campos com nome do modelo do Erick estão em **negrito**; os demais são acréscimos propostos pela AIPA.

| Campo | Tipo | Regra |
|---|---|---|
| `versao_contrato` | texto | `"ct04-v0"` |
| `simulado` | booleano | sempre `true` |
| **`lote_id`**, **`doador_id`** | texto | os do CT-03 |
| `status` | `processado` \| `revisao_humana` \| `falha` | §3.4 |
| `motivo` | lista | vazia se `processado`; códigos de §3.5 |
| `revisao` | objeto ou `null` | `{"situacao": "pendente"\|"aprovado"\|"reprovado", "decidido_em": ...}`; aprovado vira `processado` na execução seguinte |
| **`quantidade_recebida_kg`** | número ou `null` | kg recebido **validado** (texto do beneficiário coerente com o cadastro, ou aprovado na revisão humana); `null` se não validado |
| `origem_quantidade` | `confirmacao_beneficiario` \| `revisao_humana` \| `null` | de onde veio a quantidade validada |
| **`co2_evitado_kg_co2eq`** | número ou `null` | **estimativa** = `quantidade_recebida_kg` validada × fator; 2 casas; `null` se não `processado` |
| **`metodologia_carbono`** | objeto | §3.3; sempre presente, mesmo quando o CO₂ é `null` |
| **`pontos`** | inteiro ou `null` | `floor(quantidade_recebida_kg × 10)` se `processado`; senão `null` |
| `kg_acumulado_doador`, `pontos_acumulados_doador` | número | soma só dos lotes `processado` do doador (valor calculado; pode ser 0 de verdade) |
| **`selo_verde_esg`** | `"Bronze"` \| `"Prata"` \| `"Ouro"` \| `null` | pelo acumulado: ≥50 Bronze, ≥200 Prata, ≥500 Ouro |
| `selo_situacao` | `concedido` \| `abaixo_do_minimo` \| `nao_calculado` | separa "calculado e sem selo" (`abaixo_do_minimo`) de "não calculado" (lote não processado) |
| `regras_recompensa` | objeto | parâmetros usados e o aviso "regra de demonstração do FOMEZERO proposta pela AIPA (DEC-043), não aprovada pelo grupo, não norma" |
| **`termo_doacao_id`** | texto ou `null` | `TERMO-<lote_id>`; só existe para `processado` (ou falha posterior ao Termo) |
| `termo_doacao_arquivo` | texto ou `null` | `saida/termos/TERMO_<lote_id>.pdf` |
| `portal` | objeto | `{"lancado", "protocolo", "confirmado_api", "meio": "selenium"\|"api_contingencia"\|null}`; portal **SIMULADO** |
| `ia` | objeto | `{"ocorrencia", "confianca", "kg_extraido", "alerta_iot": "quebra_cadeia_frio"\|"sem_alerta_registrado"\|"desconhecido", "iot_monitorado": bool, "iot_origem": "fisico"\|"wokwi"\|"simulador"\|null, "modelo"}`; **sem texto livre** |
| `aviso` | texto | fixo: "Dados simulados. Não atesta que o alimento é seguro para consumo. CO₂ evitado é estimativa. Pontos e Selo Verde ESG: regra de demonstração, reconhecimento interno, não certificação." |
| `processado_em`, `id_execucao` | texto | data ISO 8601 (America/Sao_Paulo); liga ao log e ao relatório |

### 3.3 `metodologia_carbono` (estimativa)
O fator da FAO é uma **pegada média do alimento desperdiçado**, não uma redução medida causada pela doação. O Erick pede para não confundir as duas coisas (§3 e §12 do arquivo dele). Por isso:

```json
{
  "tipo": "estimativa",
  "fator_kg_co2eq_por_kg": 2.54,
  "fonte": "FAO (2013). Food wastage footprint: Impacts on natural resources. Summary report, ISBN 978-92-5-107752-8, p. 7 e 18 (F-026)",
  "calculo_do_fator": "3,3 Gt CO2eq / 1,3 Gt de alimento comestível desperdiçado (cálculo do grupo; não é número publicado pela FAO)",
  "ano_referencia": 2007,
  "escopo": "média global, toda a cadeia (produção até a perda), sem mudança de uso da terra; não específico do alimento",
  "cenario_referencia": "hipótese: sem a doação, o alimento teria sido descartado",
  "massa_elegivel": "quantidade_recebida_kg validada (não a quantidade cadastrada)",
  "nao_inclui": "emissões de transporte e refrigeração da doação; destino evitado específico",
  "aprovacao_grupo": "pendente (PC-011)"
}
```

### 3.4 Status
| Status | Quando | `pontos` / `selo_verde_esg` / `co2_evitado_kg_co2eq` | Termo |
|---|---|---|---|
| `processado` | sem ocorrência, confiança ≥ limiar, sem alerta da IoT, sem divergência de kg, Termo conferido, lançamento confirmado pela API do portal; ou aprovado na revisão humana e depois lançado | calculados | gerado |
| `revisao_humana` | alguma regra de revisão disparou; ou reprovado na revisão (`revisao.situacao = "reprovado"`, final) | `null` (+ `motivo`) | não gerado |
| `falha` | erro técnico tratado; se transitório, o robô tenta de novo na próxima execução | `pontos` e `selo` `null` até o lançamento ser confirmado; `co2` pode estar calculado (é estimativa do lote, não depende do portal) | pode existir |

### 3.5 Códigos de `motivo`
- Revisão: `alerta_iot_quebra_cadeia_frio`, `dados_iot_indisponiveis`, `evento_iot_desconhecido`, `ocorrencia_avaria`, `ocorrencia_divergencia_quantidade`, `ocorrencia_problema_temperatura`, `ocorrencia_ilegivel_outro`, `baixa_confianca`, `divergencia_kg`, `sem_confirmacao`, `modelo_indisponivel`, `lote_alterado_apos_processamento`, `reprovado_na_revisao`.
- Falha: `dado_invalido:<campo>`, `portal_indisponivel`, `portal_timeout`, `credenciais_invalidas`, `confirmacao_api_falhou`, `termo_invalido`.

### 3.6 Exemplo: ver `exemplos/ct04_lote_processado.json` (valores ilustrativos, não resultado de execução).

---

## 4. CT-05 (AIPA → GABA e CQIA): SAÍDA, `ct05-v0`

### 4.1 GABA: `saida/ct05/indicadores.json`
| Campo | Regra |
|---|---|
| `versao_contrato`, `simulado`, `gerado_em`, `id_execucao` | como no CT-04 |
| `massa_recebida_validada_kg` | soma de `quantidade_recebida_kg` dos lotes `processado` |
| `co2_evitado_estimado_kg_co2eq` | soma, com o mesmo `metodologia_carbono`; `null` se nenhum lote processado |
| `lotes` | contagem por status (`processado`, `revisao_humana`, `falha`) e `ignorados_nao_entregues` |
| `taxa_automacao`, `taxa_revisao_humana`, `taxa_erros` | proporções desta execução, do relatório BPMN; `null` se não houve lote |
| `ranking_esg` | por doador: `doador_id`, `kg_acumulado`, `pontos_acumulados`, `selo_verde_esg`, `selo_situacao` |
| `aviso` | o mesmo do CT-04 |

Não calculados (sem base, §11 do Erick): massa aproveitada, beneficiários atendidos, refeições, desperdício evitado. Saem como `null` com nota.

### 4.2 CQIA: `saida/ct05/historico_entregas.csv` (`;`, UTF-8)
Colunas: `lote_id;doador_id;beneficiario_id;beneficiario_tipo;entrega_confirmada_em;quantidade_disponibilizada_kg;quantidade_recebida_kg;status;motivo`. Vazio = `null`.
A CQIA trata o gargalo de roteamento e precisaria de **região** do doador e do beneficiário, que o lote não tem; o Erick também avisa que rota não tem fonte (§9) `[PENDENTE: Erick]`. Não inventamos localização.

---

## 5. CT-06 (IA → AIPA)
Proposta: a IA do robô é **própria da AIPA** (NLP + ML sobre a confirmação de entrega e regras inteligentes com o alerta da IoT, DEC-043). O CT-06 não cria dependência de outra matéria (resposta proposta à PEN-013, P-AIPA-L03).

## 6. Versionamento
Mudança de nome no CT-03 ou na IoT: só o mapa do adaptador. Mudança no CT-04/CT-05: sobe `versao_contrato` (`ct04-v1`), registrada em `03_INTEGRACAO/CONTRATOS.md` pelo ORQUESTRADOR.

## 7. O que a implementação acrescentou (TAR-012, 2026-11-13; DL-AIPA-28)
Campos **aditivos** no CT-04 gerado pelo robô (continua `ct04-v0`: nenhum campo da §3.2 mudou de nome, tipo ou regra; quem lê só os campos da §3.2 não quebra). Exemplo real: `evidencias/execucao_normal/ct04/`.

| Campo | Tipo | Regra |
|---|---|---|
| `ia.iot_ativacoes_no_periodo` | inteiro | quantas ativações de `quebra_cadeia_frio` (origem aceita) caíram na janela do transporte |
| `ia.iot_ativacao_referencia` | objeto ou `null` | a ativação usada como referência (prioriza mensagem `alerta` de ativação): `tipo_mensagem`, `seq`, `ts`, `origem`, `estado_bruto`, `fonte_arquivo`, `linha`. No LOTE-2026-0001: seq 630, `2026-11-11T13:32:35Z`, `fisico`, `mqtt-20261111-102301.log` linha 107 |
| `ia.alerta_ct03` | booleano | `true` se o próprio lote (CT-03) vier com `evento_atual = quebra_cadeia_frio` ou `estado_termico = ALERTA`; também dispara a regra R1 |
| `ia.limiar_confianca` | número | limiar usado na decisão (o calibrado no treino, gravado em `modelos/metadados_v2.json` desde o TAR-013; `ia.modelo` passa a ser `ocorrencia-v2`) |
| `revisao.revisor` | texto | código do revisor (nunca nome) quando há decisão humana |
| `revisao.motivos_originais` | lista | motivos que levaram o lote à revisão, guardados quando ele é aprovado (o `motivo` fica vazio) |
| motivo `erro_inesperado` | código | exceção não prevista num lote; status `falha`, retomado na execução seguinte |

Além disso: `ia.alerta_iot` pode valer `desconhecido` também quando a fonte da IoT está ausente; a fila de revisão sai em `saida/revisao/fila_revisao.csv` e numa cópia `fila_revisao.xlsx`. Os nomes do CT-03 e da IoT continuam **não confirmados** (PEN-001, PC-012).
