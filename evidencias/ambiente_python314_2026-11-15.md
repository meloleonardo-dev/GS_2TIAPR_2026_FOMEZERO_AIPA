# Teste de ambiente com Python 3.14 (2026-11-15, ORQUESTRADOR)

Motivo: com o Smart App Control do Windows ligado, o arquivo spacy/pipeline/multitask.cp313-win_amd64.pyd (SHA-256 CE0A1D0470BCA806...) passou a ser bloqueado nesta máquina (ImportError: Uma política de Controle de Aplicativo bloqueou este arquivo), inclusive na .venv original. A mesma versão do spaCy (3.8.18) para Python 3.14 carrega normalmente.

Execução numa cópia limpa da pasta (sem .venv e sem saida/), com uma .venv nova em Python 3.14.4 e o mesmo requirements.txt:

```
gerar_dados_sinteticos.py -> código 0
treinar_modelo.py -> código 0
SHA-256 atual     BB432927BCCB1F27586DB9EDB5702F2397EF21C33A2F12D94E0EF85AD698FF89
SHA-256 congelado BB432927BCCB1F27586DB9EDB5702F2397EF21C33A2F12D94E0EF85AD698FF89 (registro) / BB432927BCCB1F27586DB9EDB5702F2397EF21C33A2F12D94E0EF85AD698FF89 (script)
hash conferido: OK
[cego v2] n=60 ocorrencia-v1: acc=0.65 F1m=0.64 falso automático=1 automáticos=2 kg exato=50/60
[cego v2] n=60 ocorrencia-v2: acc=0.7333 F1m=0.7339 falso automático=0 automáticos=4 kg exato=51/60
[cego v2] base: acc=0.4833 F1m=0.4873 falso automático=13
métricas: evidencias/metricas_cego_v2_2026-11-15.json e .md
== EXEC-20261115-181951 | tratados 11 | processado 3 | revisão humana 6 | falha 2 | duplicados 1 | não entregues 1 | taxa de erros 0.1818 | 4.72 s
   relatório: saida\relatorios\relatorio_EXEC-20261115-181951.md | log: saida\logs\EXEC-20261115-181951.log
   gabarito: 12 de 13 registros conferem
pytest: 58 passed
```

Conclusão: com Python 3.14 o robô roda do início ao fim e as métricas do cego v2 saem idênticas às publicadas (modelos determinísticos).
