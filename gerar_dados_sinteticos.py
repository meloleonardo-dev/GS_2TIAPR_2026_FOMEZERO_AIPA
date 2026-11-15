"""Gera os dados SINTÉTICOS do robô (semente fixa) e prepara a pasta entrada/.

Saídas:
- dados/sinteticos/ocorrencias_rotuladas.csv  300 textos (60 por classe), rótulo POR CONSTRUÇÃO do gerador
- dados/sinteticos/lotes_demo.json            12 lotes de demonstração + 1 em transporte (CT-03 provisório)
- dados/sinteticos/lotes_demo_esperado.json   gabarito do status e do motivo de cada lote
- dados/cenarios/iot_simulado_invalido.log    mensagens IoT SIMULADAS para o cenário de dado inválido
- entrada/lotes_entregues.json e entrada/iot/  (cópia dos lotes de demonstração e dos 2 logs FÍSICOS reais)

Nenhum texto passou por revisão humana (DEC-044). Nenhum dado pessoal real.
Uso: python gerar_dados_sinteticos.py
"""
from __future__ import annotations

import csv
import json
import random
import re
import shutil
import unicodedata
from pathlib import Path

BASE = Path(__file__).resolve().parent
SEMENTE = 20261113
POR_CLASSE = 60

ALIMENTOS = [("pão francês", "o"), ("arroz", "o"), ("feijão", "o"), ("tomate", "o"), ("batata", "a"),
             ("banana", "a"), ("maçã", "a"), ("alface", "a"), ("cenoura", "a"), ("macarrão", "o"),
             ("mamão", "o"), ("laranja", "a"), ("pão de forma", "o"), ("abobrinha", "a"), ("chuchu", "o")]
PERECIVEIS = [("iogurte", "o"), ("queijo", "o"), ("leite", "o"), ("frango", "o"), ("carne moída", "a"),
              ("presunto", "o"), ("refeição pronta", "a"), ("requeijão", "o"), ("peixe", "o"), ("manteiga", "a")]

UNIDADES_EXT = ["um", "dois", "três", "quatro", "cinco", "seis", "sete", "oito", "nove"]
ESPECIAIS = {10: "dez", 11: "onze", 12: "doze", 13: "treze", 14: "catorze", 15: "quinze", 16: "dezesseis",
             17: "dezessete", 18: "dezoito", 19: "dezenove"}
DEZENAS = {2: "vinte", 3: "trinta", 4: "quarenta", 5: "cinquenta", 6: "sessenta", 7: "setenta", 8: "oitenta",
           9: "noventa"}

# moldes por classe: (texto, chave do kg recebido no gabarito ou None)
MOLDES = {
    "sem_ocorrencia": [
        ("recebemos {q} de {al}, tudo certo", "q"),
        ("chegaram {q} de {al} em bom estado", "q"),
        ("entrega confirmada: {q} de {al}", "q"),
        ("confirmo o recebimento de {q} de {al}. obrigado!", "q"),
        ("{q} de {al} recebidos sem problemas", "q"),
        ("{art} {al} chegou certinho, {q}", "q"),
        ("recebi {q} de {al}, tudo conforme o combinado", "q"),
        ("entregaram {q} de {al} hoje cedo, tudo ok", "q"),
        ("chegou tudo: {q} de {al}", "q"),
        ("recebemos a doação de {q} de {al}, muito obrigado", "q"),
        ("vieram {q} de {al}, embalagem perfeita", "q"),
        ("{al} recebido, {q}, tudo em ordem", "q"),
    ],
    "avaria": [
        ("recebemos {q} de {al}, {q2} vieram amassados", "q"),
        ("chegaram {q} de {al} mas parte estava estragada", "q"),
        ("recebi {q} de {al}, a embalagem veio rasgada", "q"),
        ("{q} de {al} entregues, mas {q2} estavam danificados", "q"),
        ("chegou {q} de {al}, algumas unidades mofadas", "q"),
        ("recebemos {q} de {al}; {q2} com avaria na caixa", "q"),
        ("vieram {q} de {al} e {q2} estavam quebrados", "q"),
        ("{art} {al} chegou com vazamento, recebemos {q}", "q"),
        ("recebemos {q} de {al} porém {q2} podres", "q"),
        ("entrega de {q} de {al} com produtos danificados", "q"),
        ("chegaram {q} de {al}, várias unidades amassadas", "q"),
        ("recebi {q} de {al} mas a caixa estava furada", "q"),
    ],
    "divergencia_quantidade": [
        ("dos {qc} combinados só chegaram {q}", "q"),
        ("chegaram apenas {q} de {al}, faltou uma caixa", "q"),
        ("recebemos {q} de {al}, mas o cadastro dizia {qc}", "q"),
        ("veio menos {al} do que o cadastrado: {q}", "q"),
        ("faltaram {qf} de {al}", None),
        ("só recebemos {q} de {al}", "q"),
        ("a doação era de {qc} mas vieram {q}", "q"),
        ("recebi {q} de {al}, faltando {qf}", "q"),
        ("quantidade diferente: chegaram {q} de {al} e não {qc}", "q"),
        ("entregaram {q} de {al}, menos do que o prometido", "q"),
        ("{q} de {al} recebidos, esperávamos {qc}", "q"),
        ("contamos {q} de {al}, está faltando {qf}", "q"),
    ],
    "problema_temperatura": [
        ("recebemos {q} de {al} mas chegou quente", "q"),
        ("{art} {al} chegou morno, {q}", "q"),
        ("{q} de {al}, o gelo tinha derretido", "q"),
        ("a caixa térmica chegou sem gelo, {q} de {al}", "q"),
        ("chegaram {q} de {al} fora da refrigeração", "q"),
        ("recebi {q} de {al}, estava em temperatura ambiente", "q"),
        ("{art} {al} veio quente, recebemos {q}", "q"),
        ("{q} de {al} entregues, mas a temperatura estava alta", "q"),
        ("chegou {q} de {al} sem estar gelado", "q"),
        ("recebemos {q} de {al}, a caixa estava quente e úmida", "q"),
        ("{al} recebido ({q}) mas não estava frio", "q"),
        ("chegaram {q} de {al} e o termômetro marcava {graus} graus", "q"),
    ],
    "ilegivel_outro": [
        ("ok", None), ("recebido", None), ("?", None), ("entregue", None), ("boa tarde", None),
        ("ligar para o responsável", None), ("mandei foto no grupo", None), ("xpto {n}", None), ("sim", None),
        ("foi", None), ("obrigado", None), ("aguardando", None), ("teste", None), ("confirmo", None),
        ("favor verificar", None), ("não sei informar", None), ("depois eu vejo", None), ("pode ser", None),
        ("{lixo}", None), ("{lixo} {lixo}", None), ("alguém pode me ligar?", None), ("qual o horário amanhã", None),
    ],
}


def extenso(n: int) -> str | None:
    if 1 <= n <= 9:
        return UNIDADES_EXT[n - 1]
    if n in ESPECIAIS:
        return ESPECIAIS[n]
    if 20 <= n <= 99:
        d, u = divmod(n, 10)
        return DEZENAS[d] + ("" if u == 0 else " e " + UNIDADES_EXT[u - 1])
    return None


def fmt_kg(v: float, rnd: random.Random) -> str:
    inteiro = float(v).is_integer()
    num = str(int(v)) if inteiro else f"{v:.1f}".replace(".", ",")
    opcoes = [f"{num} kg", f"{num}kg", f"{num} quilos" if v != 1 else "1 quilo", f"{num} kgs", f"{num} kilos"]
    if inteiro and extenso(int(v)) and rnd.random() < 0.25:
        e = extenso(int(v))
        return f"{e} quilos" if v != 1 else "um quilo"
    return rnd.choice(opcoes)


def sorteia_kg(rnd: random.Random, minimo=0.5, maximo=80.0) -> float:
    v = rnd.uniform(minimo, maximo)
    return float(round(v)) if rnd.random() < 0.7 else round(v * 2) / 2


def sem_acento(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", t) if not unicodedata.combining(c))


def ruido(texto: str, rnd: random.Random, protegidas: set[str]) -> str:
    """Minúsculas, sem acento, erro de digitação em palavra comum (nunca em número/unidade)."""
    if rnd.random() < 0.3:
        texto = sem_acento(texto)
    if rnd.random() < 0.5:
        texto = texto.lower()
    if rnd.random() < 0.2:
        palavras = texto.split(" ")
        cand = [i for i, p in enumerate(palavras) if len(p) > 4 and p.isalpha() and p.lower() not in protegidas]
        if cand:
            i = rnd.choice(cand)
            p = list(palavras[i])
            j = rnd.randrange(1, len(p) - 2)
            p[j], p[j + 1] = p[j + 1], p[j]
            palavras[i] = "".join(p)
            texto = " ".join(palavras)
    if rnd.random() < 0.15:
        texto = texto.rstrip(".!") + rnd.choice(["!", "!!", " :)", "."])
    return texto


PROTEGIDAS = {"quilos", "quilo", "kilos", "kgs", "dez", "onze", "doze", "treze", "catorze", "quinze", "dezesseis",
              "dezessete", "dezoito", "dezenove", "vinte", "trinta", "quarenta", "cinquenta", "sessenta", "setenta",
              "oitenta", "noventa", "quatro", "cinco"}


def gerar_rotulados(rnd: random.Random) -> list[dict]:
    linhas, vistos = [], set()
    for classe, moldes in MOLDES.items():
        n, tentativas = 0, 0
        while n < POR_CLASSE and tentativas < 10000:
            tentativas += 1
            molde, chave = rnd.choice(moldes)
            lista = PERECIVEIS if classe == "problema_temperatura" else ALIMENTOS + PERECIVEIS
            al, art = rnd.choice(lista)
            q = sorteia_kg(rnd, 1, 80)
            q2 = max(0.5, round(q * rnd.uniform(0.1, 0.4) * 2) / 2)
            qc = q
            if classe == "divergencia_quantidade":
                qc = q + max(1.0, round(q * rnd.uniform(0.15, 0.6)))
            qf = round(qc - q, 1)
            texto = molde.format(q=fmt_kg(q, rnd), q2=fmt_kg(q2, rnd), qc=fmt_kg(qc, rnd), qf=fmt_kg(qf, rnd), al=al,
                                 art=art.capitalize() if molde.startswith("{art}") else art, n=rnd.randint(1, 999),
                                 graus=rnd.randint(9, 20),
                                 lixo="".join(rnd.choice("asdfghjklqwertyuiopzxcvbnm") for _ in range(rnd.randint(3, 8))))
            texto = ruido(texto, rnd, PROTEGIDAS)
            if texto in vistos:
                continue
            vistos.add(texto)
            kg_cad = qc if classe != "ilegivel_outro" else sorteia_kg(rnd, 1, 80)
            linhas.append({"id": f"SIN-{len(linhas) + 1:04d}", "texto": texto, "classe": classe,
                           "kg_recebido_gabarito": q if chave == "q" else "", "kg_cadastrado": kg_cad,
                           "origem": "SINTETICO_gerador", "rotulado_por": "gerador (rótulo por construção)",
                           "revisao_humana": "nao"})
            n += 1
    rnd.shuffle(linhas)
    return linhas


# ---------------------------------------------------------------------------------------------------------------
# v2 (TAR-013): conjunto EXTRA de treino com mais variação. Não altera os 300 da v1 (outra semente, outro arquivo).
# Vocabulário tirado da análise de erros do conjunto de desenvolvimento ("fora do molde", 30) e de variações gerais
# do português informal (sinônimos, paráfrases, ordem das frases, ruído, números por extenso, mais de um fato).
# Rótulo POR CONSTRUÇÃO do gerador; sem revisão humana (DEC-044).
# ---------------------------------------------------------------------------------------------------------------
SEMENTE_V2 = 20261114
POR_CLASSE_V2 = 100

ABERTURAS_V2 = ["oi", "oi, tudo bem?", "bom dia", "boa tarde", "boa noite", "olá", "pessoal", "gente", "então",
                "é...", "passando pra avisar", "só pra avisar", "aqui é da ong", "aqui é do abrigo", "aqui da creche",
                "falando aqui da igreja", "oii", "opa"]
FECHOS_V2 = ["obrigado", "obrigada", "valeu", "valeu demais", "gratidão", "muito obrigado pela doação", "abraço",
             "até mais", "boa semana", "Deus ajude", "qualquer coisa me chama"]
FATOS_V2 = ["o motorista chegou às {h}h", "já separamos para as famílias", "vai pro almoço de amanhã",
            "a distribuição é na sexta", "o rapaz foi muito educado", "chegou antes do horário",
            "a entrega foi de manhã", "o carro parou na frente da sede", "a coordenadora conferiu",
            "a fila de hoje tava grande", "chegou junto com a outra doação", "o voluntário ajudou a descarregar"]

NUCLEOS_V2 = {
    "sem_ocorrencia": [
        ("{q} de {al} {ok}", "q"), ("{show}, {q} de {al} {ok}", "q"), ("a doação de {q} de {al} {ok}", "q"),
        ("deixaram {q} de {al}, {ok}", "q"), ("o pessoal do mercado deixou {q} de {al}, {ok}", "q"),
        ("{show}! {q} de {al} aqui com a gente", "q"), ("tá aqui: {q} de {al}, {ok}", "q"),
        ("{al} {ok}, {q}", "q"), ("pegamos {q} de {al} hoje, {ok}", "q"),
        ("{q} de {al} na mão, {ok}", "q"), ("o {al} chegou bem, {q}", "q"),
        ("chegou a doação ({q} de {al}), {ok}", "q"),
    ],
    "avaria": [
        ("{q} de {al}, mas {parte} {av}", "q"), ("chegou {q} de {al} e {parte} {av}", "q"),
        ("o {emb} {abriu} no caminho e {espalhou}, {sobrou} {q}", "q"),
        ("{al} veio {todo} {av2}, deu pra aproveitar pouco dos {q}", "q"),
        ("{al} {av2} e com {defeito}, {q}", "q"),
        ("as {embs} chegaram com várias {trinc}, mais ou menos {qo} perdidos de {qn}", "q"),
        ("recebemos {q} de {al}, só que {parte} {av}", "q"),
        ("{q} de {al} com {defeito}", "q"), ("{parte} do {al} {av}, total {q}", "q"),
        ("o {emb} de {al} {abriu} e {espalhou}, ficou {q}", "q"),
    ],
    "divergencia_quantidade": [
        ("no {sistema} {estava} {qc} mas na balança deu {qn}", "q"), ("pediram {qce}, vieram {q}", "q"),
        ("chegou metade do que {anunciaram}, uns {q}", "q"), ("tinha que ser {qc} de {al}, mas {quem} trouxe {qn}", "q"),
        ("deveria ter {qc} e chegou {q}", "q"), ("o combinado era {qc}, recebemos {q}", "q"),
        ("contei aqui e sumiram {n} {embs}", None), ("veio {uma} caixa de {al}, uns {q}, a outra ficou {lugar}", "q"),
        ("a conta não bate, {q} de {al} pra {qc} {anunciados}", "q"), ("pesamos e deu {q}, mas {anunciaram} {qc}", "q"),
        ("{quem} trouxe só {q} de {al}, o resto ficou {lugar}", "q"),
        ("cadê o resto? chegou {q} de {al}", "q"),
    ],
    "problema_temperatura": [
        ("o {al} {tava} {suando}, parece que ficou no sol, {q}", "q"), ("{al} chegou {molinho}, sem {friagem}, {q}", "q"),
        ("a caixa de isopor veio {aberta} e o {al} {tava} {suado}, {q}", "q"),
        ("o {al} chegou {fora_isopor}, uns {q}", "q"), ("{al} veio pingando água, {q}", "q"),
        ("o carro ficou parado no calor por {h} horas com o {al} dentro, recebemos {q}", "q"),
        ("o {al} esquentou no caminho, {q}", "q"), ("{q} de {al}, ficou {h} horas fora da geladeira", "q"),
        ("o gelo derreteu todo e o {al} {tava} {suado}, {q}", "q"), ("{al} sem refrigeração nenhuma, {q}", "q"),
        ("{q} de {al}, tava tudo {suado} e {molinho}", "q"), ("pegou sol no caminho, o {al} chegou {molinho}, {q}", "q"),
    ],
    "ilegivel_outro": [
        ("oi bom dia quem fala?", None), ("quem é?", None), ("é da ong?", None), ("esse número é de quem?", None),
        ("manda o comprovante", None), ("me chama no zap", None), ("que horas vcs abrem?", None),
        ("onde fica a sede?", None), ("kkkk", None), ("rsrs", None), ("hahaha", None), ("...", None),
        ("teste {n}", None), ("alô", None), ("oi?", None), ("tá funcionando?", None), ("recebi a mensagem", None),
        ("vou ver e te falo", None), ("liga pra coordenadora", None), ("qual o endereço?", None),
        ("amanhã tem entrega?", None), ("pedido {n}", None), ("sala {n}", None), ("me manda o link", None),
        ("{lixo}", None), ("não entendi", None), ("pode repetir?", None), ("depois te mando", None),
    ],
}
LISTAS_V2 = {
    "ok": ["tão aqui", "já tá aqui", "guardados", "foi guardado", "conferido", "conferido e guardado", "na despensa",
           "já no estoque", "bem embalado", "chegou bem", "chegou inteiro", "em ótimo estado", "tudo ok", "tudo em ordem",
           "beleza", "show", "tudo perfeito", "veio bonito", "tudo nos conformes"],
    "show": ["show", "beleza", "valeu", "perfeito", "massa", "top", "certo", "show de bola", "ótimo"],
    "parte": ["metade", "boa parte", "uma parte", "umas unidades", "várias", "algumas", "um monte"],
    "av": ["tá machucada", "veio machucada", "pisada", "esmagada", "estragada", "estragou", "veio podre", "passada",
           "com bolor", "com mofo", "melando", "com bicho", "estourada", "aberta", "furada", "com a embalagem aberta",
           "molhada", "toda batida", "amassada", "quebrada", "vazando"],
    "av2": ["esmagado", "machucado", "batido", "pisado", "estragado", "podre", "preto", "melado", "furado", "aberto",
            "amassado", "molhado"],
    "todo": ["todo", "meio", "bem", "muito"],
    "emb": ["saco", "pacote", "fardo", "engradado", "saquinho"],
    "embs": ["bandejas", "caixas", "sacos", "pacotes", "garrafas", "caixinhas"],
    "abriu": ["abriu", "furou", "estourou", "rompeu", "rasgou"],
    "espalhou": ["espalhou tudo", "caiu uma parte", "perdemos uma parte", "espalhou pelo carro", "sujou tudo"],
    "sobrou": ["sobrou uns", "ficou", "recebemos", "sobrou"],
    "defeito": ["bicho em volta", "mosca em volta", "embalagem estufada", "caixinhas estufadas", "furo na embalagem",
                "cheiro de estragado", "parte mofada", "fruta passada"],
    "trinc": ["trincadas", "quebradas", "rachadinhas", "furadas", "abertas", "amassadas"],
    "sistema": ["app", "sistema", "cadastro", "aplicativo", "pedido"],
    "estava": ["tava", "estava", "dizia", "mostrava"],
    "anunciaram": ["vocês anunciaram", "anunciaram", "prometeram", "falaram", "combinaram", "tava no app"],
    "anunciados": ["anunciados", "prometidos", "do cadastro", "do pedido"],
    "quem": ["o motorista", "o rapaz", "o entregador", "o voluntário", "a moça"],
    "uma": ["uma", "só uma", "1"],
    "lugar": ["no mercado", "no caminhão", "na loja", "pra trás", "em outro lugar"],
    "tava": ["tava", "estava", "veio", "chegou"],
    "suando": ["suando", "suado", "mole", "molinho", "morno", "quente"],
    "suado": ["suado", "mole", "quente", "morno", "molenga"],
    "molinho": ["molinho", "mole", "morno", "quente", "sem gelo"],
    "friagem": ["aquela friagem de freezer", "gelo", "frio nenhum", "estar gelado", "refrigeração"],
    "aberta": ["aberta", "sem tampa", "furada", "quebrada"],
    "fora_isopor": ["na mão, fora do isopor", "fora do isopor", "sem isopor", "no banco do carro, sem gelo",
                    "fora da caixa térmica"],
}
ABREV_V2 = {"para": "pra", "que": "q", "você": "vc", "vocês": "vcs", "está": "tá", "estava": "tava", "também": "tb",
            "muito": "mto", "hoje": "hj", "porque": "pq"}
APROX_V2 = ["", "", "", "uns ", "mais ou menos ", "quase ", "uns "]
# números e unidades nunca recebem erro de digitação nem letra repetida (o gabarito do kg tem de continuar legível)
PROTEGIDAS_V2 = PROTEGIDAS | set(UNIDADES_EXT) | set(ESPECIAIS.values()) | set(DEZENAS.values()) | {
    "três", "tres", "meio", "meia", "quilo", "kilo", "kg", "kgs", "kilos", "quilos", "um", "uma", "dois", "duas"}


def fmt_kg_v2(v: float, rnd: random.Random) -> str:
    """Como fmt_kg, com mais número por extenso (inclusive 'e meio') e unidade no singular/abreviada."""
    inteiro = float(v).is_integer()
    if rnd.random() < 0.35:
        e = extenso(int(v))
        if e and (inteiro or (v - int(v) == 0.5 and int(v) >= 1)):
            un = "quilo" if int(v) == 1 and inteiro else rnd.choice(["quilos", "quilos", "kilos", "quilo", "kg"])
            return f"{e} {un}" + ("" if inteiro else " e meio")
    num = str(int(v)) if inteiro else rnd.choice([f"{v:.1f}".replace(".", ","), f"{v:.1f}"])
    return rnd.choice([f"{num} kg", f"{num}kg", f"{num} quilos", f"{num} quilo", f"{num} kgs", f"{num} kilos",
                       f"{num} kilo", f"{num} Kg", f"{num}KG"])


def num_nu_v2(v: float, rnd: random.Random) -> str:
    """Número sem unidade ('deu 18', 'trouxe trinta')."""
    if float(v).is_integer() and extenso(int(v)) and rnd.random() < 0.4:
        return extenso(int(v))
    return str(int(v)) if float(v).is_integer() else f"{v:.1f}".replace(".", ",")


def ruido_v2(texto: str, rnd: random.Random) -> str:
    palavras = texto.split(" ")
    if rnd.random() < 0.4:  # abreviações comuns de mensagem
        palavras = [ABREV_V2.get(p.lower(), p) if rnd.random() < 0.7 else p for p in palavras]
    if rnd.random() < 0.15:  # letra repetida ("demaaais")
        cand = [i for i, p in enumerate(palavras) if p.isalpha() and len(p) > 3 and p.lower() not in PROTEGIDAS_V2]
        if cand:
            i = rnd.choice(cand)
            j = rnd.randrange(2, len(palavras[i]))
            palavras[i] = palavras[i][:j] + palavras[i][j - 1] * rnd.randint(1, 3) + palavras[i][j:]
    if rnd.random() < 0.1:  # palavra de enchimento da fala
        livres = [i for i in range(len(palavras) + 1) if not any(
            j < len(palavras) and (palavras[j][:1].isdigit() or palavras[j].lower().strip(",.") in PROTEGIDAS_V2)
            for j in (i - 1, i) if j >= 0)]  # nunca entre o número e a unidade
        palavras.insert(rnd.choice(livres) if livres else 0, rnd.choice(["né", "tipo", "assim", "aí"]))
    texto = " ".join(palavras)
    if rnd.random() < 0.2:
        texto = re.sub(r"(?<!\d)[,.]|[,.](?!\d)", "", texto)  # tira pontuação, nunca dentro de número
    if rnd.random() < 0.05:
        texto = texto.upper()
    return ruido(texto, rnd, PROTEGIDAS_V2)


def gerar_rotulados_v2_extra(rnd: random.Random) -> list[dict]:
    linhas, vistos = [], set()
    for classe, nucleos in NUCLEOS_V2.items():
        n, tentativas = 0, 0
        while n < POR_CLASSE_V2 and tentativas < 20000:
            tentativas += 1
            nucleo, chave = rnd.choice(nucleos)
            lista = PERECIVEIS if classe == "problema_temperatura" else ALIMENTOS + PERECIVEIS
            al, art = rnd.choice(lista)
            nucleo = re.sub(r"\b(o|do) \{al\}", lambda m: ("{art}" if m.group(1) == "o" else "d{art}") + " {al}", nucleo)
            q = sorteia_kg(rnd, 1, 60)
            qc = q + max(1.0, round(q * rnd.uniform(0.2, 0.7))) if classe == "divergencia_quantidade" else q
            qo = max(0.5, round(q * rnd.uniform(0.1, 0.4) * 2) / 2)
            campos = {k: rnd.choice(v) for k, v in LISTAS_V2.items()}
            aprox = "" if re.search(r"(dos|uns|só) \{q\}", nucleo) else rnd.choice(APROX_V2)
            texto = nucleo.format(q=aprox + fmt_kg_v2(q, rnd), qc=fmt_kg_v2(qc, rnd), qce=num_nu_v2(qc, rnd),
                                  qn=num_nu_v2(q, rnd), qo=fmt_kg_v2(qo, rnd), al=al, art=art, n=rnd.randint(2, 9),
                                  h=rnd.randint(2, 11),
                                  lixo="".join(rnd.choice("asdfghjklqwertyuiopzxcvbnm") for _ in range(rnd.randint(3, 8))),
                                  **campos)
            partes = [texto]
            if classe != "ilegivel_outro":
                if rnd.random() < 0.35:
                    fato = rnd.choice(FATOS_V2).format(h=rnd.randint(7, 11))
                    partes.insert(rnd.choice([0, 1]), fato)
                if rnd.random() < 0.35:
                    partes.insert(0, rnd.choice(ABERTURAS_V2))
                if rnd.random() < 0.35:
                    partes.append(rnd.choice(FECHOS_V2))
            elif rnd.random() < 0.2:
                partes.insert(0, rnd.choice(["oi", "bom dia", "boa tarde", "gente"]))
            texto = rnd.choice([", ", ". ", " "]).join(partes)
            texto = ruido_v2(texto, rnd)
            if texto in vistos:
                continue
            vistos.add(texto)
            kg_cad = qc if classe != "ilegivel_outro" else sorteia_kg(rnd, 1, 60)
            linhas.append({"id": f"SIN2-{len(linhas) + 1:04d}", "texto": texto, "classe": classe,
                           "kg_recebido_gabarito": q if chave == "q" else "", "kg_cadastrado": kg_cad,
                           "origem": "SINTETICO_gerador_v2", "rotulado_por": "gerador (rótulo por construção)",
                           "revisao_humana": "nao"})
            n += 1
    rnd.shuffle(linhas)
    return linhas


def lote(lote_id, doador, benef, alimento, kg, texto, entrega="2026-11-16T10:30:00-03:00", status="entregue",
         nome="Mercado Exemplo (SIMULADO)", tipo="ONG", **extra):
    d = {"lote_id": lote_id, "doador_id": doador, "beneficiario_id": benef, "alimento_descricao": alimento,
         "quantidade_disponibilizada_kg": kg, "quantidade_recebida_kg": None, "quantidade_aproveitada_kg": None,
         "status_logistico": status, "estado_termico": None, "evento_atual": None,
         "entrega_confirmada_em": entrega if status == "entregue" else None, "confirmacao_entrega_texto": texto,
         "doador_nome_ficticio": nome, "beneficiario_tipo": tipo, "simulado": True}
    d.update(extra)
    return d


def gerar_lotes_demo() -> tuple[dict, list[dict]]:
    l2 = lote("LOTE-2026-0002", "DOADOR-001", "BENEF-003", "pão francês", 12.0, "recebemos 12 kg de pão, tudo certo",
              "2026-11-16T09:10:00-03:00")
    lotes = [
        lote("LOTE-2026-0001", "DOADOR-002", "BENEF-001", "iogurte", 8.0, "chegaram 8 kg de iogurte",
             "2026-11-11T11:00:00-03:00", nome="Restaurante Exemplo (SIMULADO)", tipo="cozinha_comunitaria",
             estado_termico="ALERTA", evento_atual="quebra_cadeia_frio"),
        l2,
        lote("LOTE-2026-0003", "DOADOR-001", "BENEF-002", "cenoura", 20.0,
             "confirmo o recebimento de 20 kg de cenoura, tudo em ordem", "2026-11-16T09:40:00-03:00"),
        lote("LOTE-2026-0005", "DOADOR-001", "BENEF-004", "banana", 25.0, "chegaram 25 kg de banana em bom estado",
             "2026-11-16T10:05:00-03:00"),
        lote("LOTE-2026-0006", "DOADOR-003", "BENEF-005", "refeição pronta", 6.0,
             "recebemos 6 kg de refeição pronta, muito obrigado", "2026-11-16T10:20:00-03:00",
             nome="Padaria Exemplo (SIMULADO)", tipo="cozinha_comunitaria"),
        lote("LOTE-2026-0007", "DOADOR-003", "BENEF-002", "tomate", 10.0,
             "recebemos 10 kg de tomate, 2 kg vieram amassados", "2026-11-16T10:40:00-03:00",
             nome="Padaria Exemplo (SIMULADO)"),
        lote("LOTE-2026-0008", "DOADOR-004", "BENEF-003", "batata", 15.0,
             "dos 15 kg combinados só chegaram 9 kg de batata", "2026-11-16T11:00:00-03:00",
             nome="Hortifruti Exemplo (SIMULADO)"),
        lote("LOTE-2026-0009", "DOADOR-004", "BENEF-001", "queijo", 5.0,
             "recebemos 5 kg de queijo mas chegou morno", "2026-11-16T11:15:00-03:00",
             nome="Hortifruti Exemplo (SIMULADO)", tipo="cozinha_comunitaria"),
        lote("LOTE-2026-0010", "DOADOR-002", "BENEF-004", "arroz", 30.0, "ok, valeu", "2026-11-16T11:30:00-03:00",
             nome="Restaurante Exemplo (SIMULADO)"),
        lote("LOTE-2026-0011", "DOADOR-002", "BENEF-005", "feijão", -3.0, "recebemos 3 kg de feijão",
             "2026-11-16T11:45:00-03:00", nome="Restaurante Exemplo (SIMULADO)"),
        lote("", "DOADOR-003", "BENEF-001", "macarrão", 4.0, "chegaram 4 kg de macarrão", "2026-11-16T12:00:00-03:00",
             nome="Padaria Exemplo (SIMULADO)"),
        dict(l2),  # duplicado exato do LOTE-2026-0002
        lote("LOTE-2026-0004", "DOADOR-001", "BENEF-002", "banana", 15.0, None, status="em_transporte"),
    ]
    arquivo = {"_aviso": "SIMULADO. Lotes de demonstração da AIPA com os nomes do 'modelo de aplicação' proposto pelo "
                         "Erick v1.0 (não confirmado, PEN-001); confirmacao_entrega_texto, doador_nome_ficticio, "
                         "beneficiario_tipo e simulado são acréscimos propostos pela AIPA. Só o alerta da IoT do "
                         "LOTE-2026-0001 é dado físico real (logs de 10 e 11/11/2026); o lote em si é sintético.",
               "lotes": lotes}
    esperado = [
        {"indice": 0, "lote_id": "LOTE-2026-0001", "status": "revisao_humana", "motivo_contem": ["alerta_iot_quebra_cadeia_frio"],
         "caso": "lote sintético cruzado com o alerta FÍSICO real de 11/11/2026 (ativação 13:32:35Z após normalização)"},
        {"indice": 1, "lote_id": "LOTE-2026-0002", "status": "processado", "motivo_contem": [], "caso": "normal"},
        {"indice": 2, "lote_id": "LOTE-2026-0003", "status": "processado", "motivo_contem": [], "caso": "normal"},
        {"indice": 3, "lote_id": "LOTE-2026-0005", "status": "processado", "motivo_contem": [], "selo_verde_esg": "Bronze",
         "caso": "normal; DOADOR-001 passa de 50 kg acumulados (12 + 20 + 25 = 57) -> Bronze"},
        {"indice": 4, "lote_id": "LOTE-2026-0006", "status": "processado", "motivo_contem": [], "selo_situacao": "abaixo_do_minimo",
         "caso": "normal; doador abaixo do mínimo do selo"},
        {"indice": 5, "lote_id": "LOTE-2026-0007", "status": "revisao_humana", "motivo_contem": ["ocorrencia_avaria"], "caso": "avaria"},
        {"indice": 6, "lote_id": "LOTE-2026-0008", "status": "revisao_humana", "motivo_contem": ["divergencia_kg"],
         "caso": "divergência de quantidade (9 de 15 kg)"},
        {"indice": 7, "lote_id": "LOTE-2026-0009", "status": "revisao_humana", "motivo_contem": ["ocorrencia_problema_temperatura"],
         "caso": "texto de temperatura"},
        {"indice": 8, "lote_id": "LOTE-2026-0010", "status": "revisao_humana", "motivo_contem": ["sem_confirmacao"],
         "caso": "texto ilegível, sem kg"},
        {"indice": 9, "lote_id": "LOTE-2026-0011", "status": "falha", "motivo_contem": ["dado_invalido:quantidade_disponibilizada_kg"],
         "caso": "inválido: kg negativo"},
        {"indice": 10, "lote_id": "", "status": "falha", "motivo_contem": ["dado_invalido:lote_id"], "caso": "inválido: sem lote_id"},
        {"indice": 11, "lote_id": "LOTE-2026-0002", "status": "ignorado_duplicado", "motivo_contem": [],
         "caso": "duplicado exato no mesmo arquivo"},
        {"indice": 12, "lote_id": "LOTE-2026-0004", "status": "ignorado_nao_entregue", "motivo_contem": [],
         "caso": "em_transporte (fora dos 12 de demonstração)"},
    ]
    return arquivo, esperado


def gerar_iot_simulado() -> list[str]:
    """Mensagens SIMULADAS (origem simulador) para o cenário de dado inválido da IoT."""
    p = "fomezero/gs2026/simulado/lote"
    linhas = [
        f'{p}/LOTE-2026-0003/telemetria {{"schema":"fomezero.telemetria.v1","lote_id":"LOTE-2026-0003","device_id":"esp32-simulado-01","seq":1,"ts":"2026-11-16T12:00:00Z","ts_valido":true,"temp_c":3.9,"limite_c":5.0,"evento":"normal","estado":"FRIO_OK","origem":"simulador"}}',
        f'{p}/LOTE-2026-0003/telemetria {{"schema":"fomezero.telemetria.v1","lote_id":"LOTE-2026-0003","device_id":"esp32-simulado-01","seq":2,"ts":"2026-11-16T12:00:10Z","ts_valido":true,"temp_c":4.0,"limite_c":5.0,"evento":"normal","estado":"SENSOR_XYZ","origem":"simulador"}}',
        f'{p}/LOTE-2026-0005/telemetria {{"schema":"fomezero.telemetria.v1","lote_id":"LOTE-2026-0005","device_id":"esp32-simulado-01","seq":3,"ts":"2026-11-16T12:01:00Z"',
        f'{p}/LOTE-2026-0005/alerta {{"schema":"fomezero.alerta.v1","lote_id":"LOTE-2026-0005","device_id":"esp32-simulado-01","seq":4,"ts":"2026-11-16T12:02:00Z","evento":"quebra_cadeia_frio","temp_c":7.5,"limite_c":5.0,"duracao_acima_s":40,"severidade":"alta","acao":"alerta_visual_app","origem":"simulador"}}',
        f'{p}/LOTE-2026-0006/telemetria {{"schema":"fomezero.telemetria.v1","lote_id":"LOTE-2026-0006","device_id":"esp32-simulado-01","seq":5,"ts":"data-invalida","ts_valido":false,"temp_c":4.1,"limite_c":5.0,"evento":"normal","estado":"FRIO_OK","origem":"simulador"}}',
    ]
    return linhas


def main():
    rnd = random.Random(SEMENTE)
    pasta = BASE / "dados" / "sinteticos"
    pasta.mkdir(parents=True, exist_ok=True)
    rot = gerar_rotulados(rnd)
    campos = list(rot[0].keys())
    with open(pasta / "ocorrencias_rotuladas.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos, delimiter=";")
        w.writeheader()
        w.writerows(rot)
    extra = gerar_rotulados_v2_extra(random.Random(SEMENTE_V2))
    with open(pasta / "ocorrencias_rotuladas_v2_extra.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos, delimiter=";")
        w.writeheader()
        w.writerows(extra)
    arquivo, esperado = gerar_lotes_demo()
    (pasta / "lotes_demo.json").write_text(json.dumps(arquivo, ensure_ascii=False, indent=2), encoding="utf-8")
    (pasta / "lotes_demo_esperado.json").write_text(json.dumps(
        {"_aviso": "Gabarito dos lotes de demonstração (SIMULADO), escrito pelo agente da AIPA; sem revisão humana.",
         "esperado": esperado}, ensure_ascii=False, indent=2), encoding="utf-8")
    cen = BASE / "dados" / "cenarios"
    cen.mkdir(parents=True, exist_ok=True)
    (cen / "iot_simulado_invalido.log").write_text("\n".join(gerar_iot_simulado()) + "\n", encoding="utf-8")

    entrada = BASE / "entrada"
    if entrada.exists():
        shutil.rmtree(entrada)
    (entrada / "iot").mkdir(parents=True)
    shutil.copy2(pasta / "lotes_demo.json", entrada / "lotes_entregues.json")
    for log in sorted((BASE / "dados" / "iot_fisico").glob("*.log")):
        shutil.copy2(log, entrada / "iot" / log.name)

    contagem = {}
    for r in rot:
        contagem[r["classe"]] = contagem.get(r["classe"], 0) + 1
    print(f"ocorrencias_rotuladas.csv: {len(rot)} textos SINTÉTICOS {contagem}")
    print(f"ocorrencias_rotuladas_v2_extra.csv: {len(extra)} textos SINTÉTICOS (treino extra da v2, {POR_CLASSE_V2} por classe)")
    print(f"lotes_demo.json: {len(arquivo['lotes'])} registros (12 de demonstração + 1 em transporte)")
    print(f"entrada/ preparada: lotes_entregues.json + {len(list((entrada / 'iot').glob('*.log')))} logs FÍSICOS da IoT")


if __name__ == "__main__":
    main()
