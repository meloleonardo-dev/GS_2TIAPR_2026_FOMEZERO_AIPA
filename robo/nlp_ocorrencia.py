"""IA com função real (tema D): lê a confirmação de entrega do beneficiário.

(a) extrai o kg recebido com spaCy (tokenizador do português + Matcher);
(b) classifica a ocorrência com scikit-learn (TF-IDF + regressão logística), com confiança;
(c) linha de base por palavras-chave, para medir se o ML agrega.

Nada aqui decide se o alimento é seguro para consumo: a saída só alimenta as regras
que mandam o lote para revisão humana.
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import spacy
from spacy.matcher import Matcher

CLASSES = ["sem_ocorrencia", "avaria", "divergencia_quantidade", "problema_temperatura", "ilegivel_outro"]

UNIDADES = {"kg", "kgs", "kilo", "kilos", "quilo", "quilos", "quilograma", "quilogramas", "kilograma", "kilogramas"}
NUMEROS = {
    "zero": 0, "um": 1, "uma": 1, "dois": 2, "duas": 2, "tres": 3, "três": 3, "quatro": 4, "cinco": 5,
    "seis": 6, "sete": 7, "oito": 8, "nove": 9, "dez": 10, "onze": 11, "doze": 12, "treze": 13,
    "catorze": 14, "quatorze": 14, "quinze": 15, "dezesseis": 16, "dezessete": 17, "dezoito": 18,
    "dezenove": 19, "vinte": 20, "trinta": 30, "quarenta": 40, "cinquenta": 50, "sessenta": 60,
    "setenta": 70, "oitenta": 80, "noventa": 90, "cem": 100, "meio": 0.5, "meia": 0.5,
}
# listas de palavras da §4.1 (radicais, comparados sem acento)
RADICAIS_RECEBIDO = ("receb", "cheg", "entreg", "vier", "veio", "contamos", "conferimos")
RADICAIS_REFERENCIA = ("dos", "cadastr", "combinad", "prometid", "esperav", "esperad", "era", "eram", "nao", "dizia")
RADICAIS_FALTANTE = ("falt",)
RADICAIS_OCORRENCIA = ("amassad", "estragad", "rasgad", "vazad", "vazament", "danificad", "mofad", "quebrad",
                       "podre", "avaria", "furad", "derret", "quente", "morn")
PALAVRAS_BASE = {
    "problema_temperatura": ("quente", "morn", "derret", "gelo", "gelad", "refrigera", "temperatura", "frio", "termic",
                             "termometr", "ambiente"),
    "avaria": ("amassad", "estragad", "rasgad", "vazad", "vazament", "danificad", "mofad", "quebrad", "podre",
               "avaria", "furad"),
    "divergencia_quantidade": ("falt", "so ", "apenas", "menos", "diferente", "cadastr", "combinad", "esperav"),
}
_RE_NUM = re.compile(r"^\d+([.,]\d+)?$")
_RE_NUM_UNIDADE = re.compile(r"^(\d+(?:[.,]\d+)?)(kg|kgs|quilos?|kilos?)$", re.IGNORECASE)

_NLP = None
_MATCHER = None


def sem_acento(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", t) if not unicodedata.combining(c))


def nlp():
    """spaCy só com o tokenizador do português (sem modelo baixado, DL-AIPA-03)."""
    global _NLP, _MATCHER
    if _NLP is None:
        _NLP = spacy.blank("pt")
        _MATCHER = Matcher(_NLP.vocab)
        palavras = sorted(set(NUMEROS) | {"e"})
        _MATCHER.add("QTD_DIGITOS", [[{"TEXT": {"REGEX": r"^\d+([.,]\d+)?$"}}, {"LOWER": {"IN": sorted(UNIDADES)}}]])
        _MATCHER.add("QTD_EXTENSO", [[{"LOWER": {"IN": palavras}, "OP": "+"}, {"LOWER": {"IN": sorted(UNIDADES)}}]])
        _MATCHER.add("QTD_COLADA", [[{"TEXT": {"REGEX": r"(?i)^\d+([.,]\d+)?(kg|kgs|quilos?|kilos?)$"}}]])
    return _NLP, _MATCHER


def _valor_extenso(tokens: list[str]) -> float | None:
    total, achou = 0.0, False
    for t in tokens:
        t = t.lower()
        if t == "e":
            continue
        if t in NUMEROS:
            total += NUMEROS[t]
            achou = True
        else:
            return None
    return total if achou else None


def _contexto(doc, inicio: int, fim: int, janela: int = 3) -> tuple[list[str], list[str]]:
    antes, depois = [], []
    i = inicio - 1
    while i >= 0 and len(antes) < janela and not doc[i].is_punct:
        antes.append(sem_acento(doc[i].lower_))
        i -= 1
    j = fim
    while j < len(doc) and len(depois) < 5 and not doc[j].is_punct:
        if doc[j].like_num or _RE_NUM.match(doc[j].text):
            break
        depois.append(sem_acento(doc[j].lower_))
        j += 1
    return antes, depois


def _tem(tokens: list[str], radicais) -> bool:
    return any(tok.startswith(r) or tok == r for tok in tokens for r in radicais)


# ---- v2 (TAR-013): listas ampliadas a partir dos erros do conjunto de desenvolvimento (FM-10, FM-12, FM-15, FM-17)
RADICAIS_RECEBIDO_V2 = RADICAIS_RECEBIDO + ("trouxe", "trouxer", "deu", "sobrou", "ficou", "pesou")
RADICAIS_REFERENCIA_V2 = ("cadastr", "combinad", "prometid", "esperav", "esperad", "dizia", "anunci", "pedid",
                          "pediram", "deveria", "aplicativo", "sistema")
REFERENCIA_EXATA_V2 = {"era", "eram", "nao", "app", "ser", "nota", "mostrava"}
REFERENCIA_FRACA_V2 = {"dos", "das"}  # "aproveitar pouco dos 5 kg": se não houver outro kg recebido, é o total
RADICAIS_OCORRENCIA_V2 = RADICAIS_OCORRENCIA + ("perd", "machucad", "esmagad", "pisad", "estufad", "trincad",
                                                "estourad", "estragou", "melad", "melando")
SALTAR_ANTES_V2 = {"uns", "umas", "quase", "so", "apenas", "mais", "ou", "menos", "tipo", "cerca"}
# substantivo de contagem/medida depois do número: não é kg ("3 caixas", "15 graus", "12 litros", "2 horas")
NAO_KG_PREFIXOS_V2 = ("caixa", "caixinha", "saco", "pacote", "bandej", "unidade", "lata", "litro", "grau", "hora",
                      "minuto", "marmita", "pessoa", "familia", "reais", "sacola", "fardo", "cesta", "pote", "garrafa",
                      "engradado", "duzia", "cacho", "semana", "grama")
NAO_KG_EXATOS_V2 = {"h", "dia", "dias", "real", "vez", "vezes", "kit", "kits", "pe", "pes", "maco", "macos", "x", "ml",
                    "g", "l", "lt", "lts", "un", "und", "mes", "meses", "%", "°", "º", "de", "do", "da", "por"}
_RE_REPETIDA_EXTR = re.compile(r"([^\W\d_])\1{2,}")


def _papel_v2(antes: list[str]) -> str | None:
    for pos, tok in enumerate(antes):  # da palavra mais próxima para a mais distante
        if tok in REFERENCIA_FRACA_V2:
            return "referencia_fraca"
        if tok == "nao" and pos > 0:
            continue  # "não" só marca referência colado ao número ("e não 60")
        if tok in REFERENCIA_EXATA_V2 or _tem([tok], RADICAIS_REFERENCIA_V2):
            return "referencia"
        if _tem([tok], RADICAIS_FALTANTE):
            return "faltante"
        if _tem([tok], RADICAIS_RECEBIDO_V2):
            return "recebido"
    return None


def _numeros_sem_unidade_v2(doc, ocupado: set, fins_kg: set) -> list[dict]:
    """Número sem unidade num texto que já fala em kg ('na balança deu 18', 'trouxe 32', 'perdidos de dez').

    Só vale quando a palavra logo antes (pulando 'uns', 'quase'...) é um verbo de recebimento/referência, ou quando é
    'de'/'dos' logo depois de uma quantidade em kg. Número seguido de substantivo de contagem ou medida ('3 caixas',
    '15 graus', '12 litros') não vira kg."""
    saida, i = [], 0
    while i < len(doc):
        tok = doc[i]
        if i in ocupado:
            i += 1
            continue
        if _RE_NUM.match(tok.text):
            ini, fim, valor = i, i + 1, float(tok.text.replace(",", "."))
        elif sem_acento(tok.lower_) in NUMEROS and tok.lower_ not in ("um", "uma", "meio", "meia"):
            j = i
            while j < len(doc) and j not in ocupado and (sem_acento(doc[j].lower_) in NUMEROS or doc[j].lower_ == "e"):
                j += 1
            while j > i and doc[j - 1].lower_ == "e":
                j -= 1
            valor = _valor_extenso([sem_acento(t.lower_) for t in doc[i:j]])
            ini, fim = i, j
            if valor is None:
                i += 1
                continue
        else:
            i += 1
            continue
        prox = sem_acento(doc[fim].lower_) if fim < len(doc) else ""
        if prox and (prox in NAO_KG_EXATOS_V2 or prox.startswith(NAO_KG_PREFIXOS_V2) or prox[:1] in "°º%"):
            i = fim
            continue
        k = ini - 1
        while k >= 0 and sem_acento(doc[k].lower_) in SALTAR_ANTES_V2:
            k -= 1
        papel = None
        if k >= 0:
            ant = sem_acento(doc[k].lower_)
            if ant in ("de", "dos") and any(f in fins_kg for f in range(k - 1, k - 5, -1)) and not any(
                    doc[x].is_punct for x in range(max(k - 4, 0), k)):
                papel = "recebido"  # "dois quilos perdidos de dez": o total
            elif ant in REFERENCIA_EXATA_V2 or _tem([ant], RADICAIS_REFERENCIA_V2):
                papel = "referencia"
            elif _tem([ant], RADICAIS_RECEBIDO_V2):
                papel = "recebido"
        if papel:
            saida.append({"ini": ini, "valor": round(valor, 3), "papel": papel, "trecho": doc[ini:fim].text,
                          "sem_unidade": True})
        i = fim
    return saida


def extrair_quantidades(texto: str | None, versao: int = 2) -> list[dict]:
    """Lista de quantidades em kg com o papel inferido pela vizinhança (versao=1: regra do TAR-012)."""
    if not texto:
        return []
    doc_nlp, matcher = nlp()
    if versao >= 2:
        texto = _RE_REPETIDA_EXTR.sub(r"\1", texto)  # "cheeeegou" -> "chegou"
    doc = doc_nlp(texto)
    achados = []
    for _id, ini, fim in matcher(doc):
        achados.append((ini, fim, doc_nlp.vocab.strings[_id]))
    # fica com o trecho mais longo quando há sobreposição (extenso com OP "+")
    achados.sort(key=lambda x: (x[0], -(x[1] - x[0])))
    escolhidos, ocupado = [], set()
    for ini, fim, nome in sorted(achados, key=lambda x: -(x[1] - x[0])):
        if any(k in ocupado for k in range(ini, fim)):
            continue
        escolhidos.append((ini, fim, nome))
        ocupado.update(range(ini, fim))
    saida = []
    for ini, fim, nome in sorted(escolhidos):
        if nome == "QTD_DIGITOS":
            valor = float(doc[ini].text.replace(",", "."))
        elif nome == "QTD_COLADA":
            m = _RE_NUM_UNIDADE.match(doc[ini].text)
            valor = float(m.group(1).replace(",", "."))
        else:
            toks = [t.text for t in doc[ini:fim - 1]]
            while toks and toks[0].lower() == "e":
                toks.pop(0)
                ini += 1
            valor = _valor_extenso(toks)
            if valor is None:
                continue
        # "dois quilos e meio"
        if fim + 1 < len(doc) and doc[fim].lower_ == "e" and doc[fim + 1].lower_ in ("meio", "meia"):
            valor += 0.5
        antes, depois = _contexto(doc, ini, fim)
        papel = None
        if versao >= 2:
            papel = _papel_v2(antes)
            if papel is None:
                papel = "ocorrencia" if _tem(depois, RADICAIS_OCORRENCIA_V2) else "recebido"
        else:
            for tok in antes:  # da palavra mais próxima para a mais distante
                if _tem([tok], RADICAIS_REFERENCIA):
                    papel = "referencia"
                elif _tem([tok], RADICAIS_FALTANTE):
                    papel = "faltante"
                elif _tem([tok], RADICAIS_RECEBIDO):
                    papel = "recebido"
                if papel:
                    break
            if papel is None:
                papel = "ocorrencia" if _tem(depois, RADICAIS_OCORRENCIA) else "recebido"
        saida.append({"ini": ini, "fim": fim, "valor": round(valor, 3), "papel": papel, "trecho": doc[ini:fim].text})
    if versao >= 2 and saida:
        fins = {q["fim"] - 1 for q in saida}
        saida += _numeros_sem_unidade_v2(doc, ocupado, fins)
        saida.sort(key=lambda q: q["ini"])
    for q in saida:
        q.pop("ini", None)
        q.pop("fim", None)
    return saida


def extrair_kg(texto: str | None, versao: int = 2) -> dict:
    """kg_extraido = primeira quantidade com papel 'recebido'; kg_ocorrencia = soma das de ocorrência.

    versao=2 (padrão, TAR-013): também lê número sem unidade depois de verbo de recebimento ('na balança deu 18'),
    separa o valor de referência ('no app tava 25 kg', 'tinha que ser 40 kilos') e, se não houver outro, usa o total
    em 'dos 5 kg'. versao=1: regra do TAR-012 (mantida para comparação e para a linha de base)."""
    qs = extrair_quantidades(texto, versao)
    recebidos = [q["valor"] for q in qs if q["papel"] == "recebido"]
    if not recebidos and versao >= 2:
        recebidos = [q["valor"] for q in qs if q["papel"] == "referencia_fraca"]
    ocorr = [q["valor"] for q in qs if q["papel"] == "ocorrencia"]
    return {
        "kg_extraido": recebidos[0] if recebidos else None,
        "kg_ocorrencia": round(sum(ocorr), 3) if ocorr else None,
        "quantidades": qs,
    }


# ---------- classificação ----------
_RE_DIGITOS = re.compile(r"\d+([.,]\d+)?")


def preprocessar(texto: str | None) -> str:
    """Minúsculas, sem acento, números trocados por <num> (o modelo não decora valores)."""
    t = sem_acento((texto or "").lower())
    return _RE_DIGITOS.sub(" numtok ", t)


def tokenizar(texto: str) -> list[str]:
    doc_nlp, _ = nlp()
    return [t.text for t in doc_nlp(texto) if not t.is_space and not t.is_punct]


def criar_pipeline(c: float = 10.0, semente: int = 42):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    return Pipeline([
        ("tfidf", TfidfVectorizer(tokenizer=tokenizar, preprocessor=preprocessar, token_pattern=None,
                                  ngram_range=(1, 2), sublinear_tf=True, min_df=1)),
        ("clf", LogisticRegression(class_weight="balanced", max_iter=2000, C=c, random_state=semente)),
    ])


# ---- v2 (TAR-013). As funções acima (preprocessar, tokenizar, criar_pipeline) ficam como estão: o arquivo
# ocorrencia-v1.joblib guarda referência a elas.
_RE_REPETIDA = re.compile(r"([a-z])\1{2,}")


def preprocessar_v2(texto: str | None) -> str:
    """Como preprocessar, e letra repetida 3+ vezes vira uma ('demaaais' -> 'demais')."""
    return _RE_REPETIDA.sub(r"\1", preprocessar(texto))


def criar_pipeline_v2(c: float = 10.0, semente: int = 42, char: bool = True, palavras: bool = True):
    """TF-IDF de palavras (1-2) + TF-IDF de caracteres dentro da palavra (char_wb 3-5) + regressão logística.

    Os n-gramas de caracteres pegam pedaços de palavra ('molinh', 'machuc', 'estrag') e sobrevivem a erro de
    digitação e a sufixo diferente; a regressão logística continua simples, gratuita e explicável (pesos por
    n-grama)."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import FeatureUnion, Pipeline
    partes = []
    if palavras:
        partes.append(("palavras", TfidfVectorizer(tokenizer=tokenizar, preprocessor=preprocessar_v2, token_pattern=None,
                                                   ngram_range=(1, 2), sublinear_tf=True, min_df=1)))
    if char:
        partes.append(("caracteres", TfidfVectorizer(analyzer="char_wb", preprocessor=preprocessar_v2,
                                                     ngram_range=(3, 5), sublinear_tf=True, min_df=2)))
    return Pipeline([
        ("tfidf", FeatureUnion(partes)),
        ("clf", LogisticRegression(class_weight="balanced", max_iter=5000, C=c, random_state=semente)),
    ])


class Classificador:
    """Carrega o modelo salvo. Se faltar ou estiver corrompido, `disponivel` = False (regra R8)."""

    def __init__(self, caminho: Path):
        self.caminho = Path(caminho)
        self.pipeline = None
        self.erro = None
        try:
            import joblib
            if not self.caminho.exists():
                raise FileNotFoundError(str(self.caminho.name))
            self.pipeline = joblib.load(self.caminho)
        except Exception as e:  # noqa: BLE001 - qualquer erro de carga leva ao caminho seguro
            self.erro = f"{type(e).__name__}: {e}"

    @property
    def disponivel(self) -> bool:
        return self.pipeline is not None

    def classificar(self, texto: str | None) -> tuple[str, float]:
        proba = self.pipeline.predict_proba([texto or ""])[0]
        i = int(proba.argmax())
        return str(self.pipeline.classes_[i]), round(float(proba[i]), 4)


def classificar_palavras_chave(texto: str | None) -> str:
    """Linha de base: só listas de palavras (mesmas da §4.1), sem aprendizado."""
    t = " " + sem_acento((texto or "").lower()) + " "
    tokens = re.findall(r"\w+", t)
    for classe in ("problema_temperatura", "avaria", "divergencia_quantidade"):
        for r in PALAVRAS_BASE[classe]:
            if r.endswith(" "):
                if f" {r}" in t:
                    return classe
            elif any(tok.startswith(r) for tok in tokens):
                return classe
    if extrair_kg(texto, versao=1)["kg_extraido"] is None:  # linha de base fixa (regra do TAR-012)
        return "ilegivel_outro"
    return "sem_ocorrencia"
