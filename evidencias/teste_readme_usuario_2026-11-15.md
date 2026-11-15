# Teste do README por quem não escreveu o código (2026-11-15)

Executado pelo integrante Leonardo Melo (RM 567097), seguindo a seção "Como executar" do README numa cópia limpa da
pasta (`Desktop\TESTE_AIPA`, sem `.venv`, `saida/` nem caches), num PowerShell novo, com Python 3.14 e `.venv` nova.

Primeira tentativa (Python 3.13, README anterior): `treinar_modelo.py` parou com o bloqueio do Smart App Control do
Windows num arquivo do spaCy (DEC-047). O README foi corrigido (Python 3.14 e aviso para esse erro) e o teste foi refeito
do zero.

Segunda tentativa (README atual), saída colada pelo usuário:

```
== EXEC-20261115-182447 | tratados 11 | processado 3 | revisão humana 6 | falha 2 | duplicados 1 | não entregues 1 | taxa de erros 0.1818 | 3.18 s
   relatório: saida\relatorios\relatorio_EXEC-20261115-182447.md | log: saida\logs\EXEC-20261115-182447.log
   gabarito: 12 de 13 registros conferem
(.venv) PS C:\Users\silva\Desktop\TESTE_AIPA> python -m pytest testes -q
..........................................................                                                       [100%]
58 passed in 12.77s
```

Comandos seguidos: `py -3.14 -m venv .venv`, `.\.venv\Scripts\activate`, `pip install -r requirements.txt`,
`copy .env.exemplo .env`, `python gerar_dados_sinteticos.py`, `python treinar_modelo.py`, `python executar_robo.py`,
`python -m pytest testes -q`.

Limite: o teste foi feito na mesma máquina em que o robô foi desenvolvido (o driver do Edge já estava em cache).
