"""Treina e avalia o classificador de ocorrência (tema D): ocorrencia-v1 (TAR-012) e ocorrencia-v2 (TAR-013).

- conjunto da v1: dados/sinteticos/ocorrencias_rotuladas.csv (300 SINTÉTICOS, rótulo por construção do gerador),
  divisão 75/25 estratificada, semente fixa -> treino 225, teste 75 (o mesmo teste para v1 e v2)
- v1: TF-IDF de palavras + regressão logística, treino 225 (receita do TAR-012, sem mudança)
- v2: TF-IDF de palavras + TF-IDF de caracteres (char_wb 3-5) + regressão logística, treino 225 + 500 sintéticos
  extra do gerador v2 (dados/sinteticos/ocorrencias_rotuladas_v2_extra.csv); extração do kg v2
- LIMIAR_CONFIANCA: parte de 0,70 e é calibrado SÓ no treino de cada versão (validação cruzada de 5 partes):
  o menor limiar >= 0,70 sem nenhum "falso automático" fora da dobra
- avaliação: teste sintético (75) e conjunto de desenvolvimento (os 30 "fora do molde", escritos e rotulados pelo
  agente de IA; usados no TAR-013 para ajustar o gerador e a extração, por isso NÃO medem mais generalização)
- o conjunto cego v2 NÃO é lido aqui: a medição dele é `python medir_cego_v2.py` (confere o hash antes)
- grava modelos/ocorrencia-v1.joblib, modelos/ocorrencia-v2.joblib, modelos/metadados_v1.json, metadados_v2.json
  e evidencias/metricas_ia_AAAA-MM-DD.json/.md

Limitação: tudo é sintético e rotulado por gerador/IA, SEM revisão humana (DEC-044).
Uso: python treinar_modelo.py
"""
from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import date, datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_recall_fscore_support
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split

from robo import regras
from robo.config import carregar_parametros
from robo.nlp_ocorrencia import (CLASSES, classificar_palavras_chave, criar_pipeline, criar_pipeline_v2, extrair_kg,
                                 preprocessar, tokenizar)

BASE = Path(__file__).resolve().parent
SINT = BASE / "dados" / "sinteticos"
SEMENTE = 42
C_REG = 10.0
GRADE_LIMIAR = [0.70, 0.75, 0.80, 0.85, 0.90, 0.95]
VERSOES = {
    "ocorrencia-v1": {"algoritmo": "TF-IDF (1-2 gramas, tokenizador spaCy pt, sem acento, números -> numtok) + "
                                   f"LogisticRegression (class_weight=balanced, C={C_REG})",
                      "treino": "225 (75% de ocorrencias_rotuladas.csv)", "extracao_kg_versao": 1},
    "ocorrencia-v2": {"algoritmo": "TF-IDF de palavras (1-2 gramas, tokenizador spaCy pt, sem acento, números -> "
                                   "numtok, letra repetida -> 1) + TF-IDF de caracteres char_wb (3-5, min_df=2) + "
                                   f"LogisticRegression (class_weight=balanced, C={C_REG})",
                      "treino": "225 da v1 + 500 de ocorrencias_rotuladas_v2_extra.csv", "extracao_kg_versao": 2},
}
LIMITACAO = ("Conjuntos SINTÉTICOS: os textos do gerador têm rótulo por construção e os 30 'fora do molde' e os 60 do "
             "cego v2 foram escritos e rotulados pelo agente de IA da AIPA; nenhum texto teve revisão humana (DEC-044). "
             "No TAR-013 os 30 'fora do molde' viraram conjunto de DESENVOLVIMENTO (o gerador v2 e a extração v2 foram "
             "ajustados olhando os erros deles), então o resultado neles não mede mais generalização; quem mede é o "
             "cego v2 (medir_cego_v2.py). Não há texto real de beneficiário.")


def sha256(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def ler(caminho: Path) -> pd.DataFrame:
    df = pd.read_csv(caminho, sep=";", encoding="utf-8", dtype={"texto": str}, keep_default_na=False)
    df["kg_recebido_gabarito"] = df["kg_recebido_gabarito"].apply(lambda v: None if v in ("", None) else float(v))
    df["kg_cadastrado"] = df["kg_cadastrado"].astype(float)
    return df


def falso_automatico_classificador(y_true, pred, conf, limiar) -> int:
    return int(sum(1 for t, p, c in zip(y_true, pred, conf) if p == "sem_ocorrencia" and c >= limiar
                   and t != "sem_ocorrencia"))


def calibrar_limiar(pipe, X, y) -> tuple[float, list[dict], float]:
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEMENTE)
    proba = cross_val_predict(pipe, X, y, cv=cv, method="predict_proba")
    classes = sorted(set(y))
    pred = [classes[i] for i in proba.argmax(axis=1)]
    conf = proba.max(axis=1)
    tabela = []
    escolhido = None
    for lim in GRADE_LIMIAR:
        fa = falso_automatico_classificador(y, pred, conf, lim)
        auto = int(sum(1 for p, c in zip(pred, conf) if p == "sem_ocorrencia" and c >= lim))
        tabela.append({"limiar": lim, "falso_automatico_oof": fa, "seguiriam_automatico_oof": auto, "n": len(y)})
        if escolhido is None and fa == 0:
            escolhido = lim
    f1cv = round(f1_score(y, pred, average="macro"), 4)
    return (escolhido if escolhido is not None else GRADE_LIMIAR[-1]), tabela, f1cv


def kg_metricas(gab, ext) -> dict:
    n = len(gab)
    certos = sum(1 for g, e in zip(gab, ext) if (g is None and e is None) or
                 (g is not None and e is not None and abs(g - e) <= 0.01))
    com_kg = [(g, e) for g, e in zip(gab, ext) if g is not None]
    nao_enc = sum(1 for g, e in com_kg if e is None)
    errado = sum(1 for g, e in com_kg if e is not None and abs(g - e) > 0.01)
    inventado = sum(1 for g, e in zip(gab, ext) if g is None and e is not None)
    return {"n": n, "acerto_kg_exato": round(certos / n, 4) if n else None, "acertos": certos,
            "n_com_kg_no_gabarito": len(com_kg), "nao_encontrado": nao_enc,
            "pct_nao_encontrado": round(nao_enc / len(com_kg), 4) if com_kg else None,
            "valor_errado": errado, "kg_extraido_sem_kg_no_gabarito": inventado}


def cls_metricas(y, pred_) -> dict:
    p, r, f, s = precision_recall_fscore_support(y, pred_, labels=CLASSES, zero_division=0)
    return {"acuracia": round(accuracy_score(y, pred_), 4),
            "f1_macro": round(f1_score(y, pred_, labels=CLASSES, average="macro", zero_division=0), 4),
            "por_classe": {c: {"precisao": round(p[i], 4), "revocacao": round(r[i], 4), "f1": round(f[i], 4),
                               "suporte": int(s[i])} for i, c in enumerate(CLASSES)},
            "matriz_confusao": {"linhas_real_colunas_previsto": CLASSES,
                                "valores": confusion_matrix(y, pred_, labels=CLASSES).tolist()}}


def roteamento(y, pred_, conf_, ext, cads, limiar, params) -> dict:
    auto, fa, auto_ok = 0, 0, 0
    n_sem = sum(1 for t in y if t == "sem_ocorrencia")
    falsos = []
    for i, (t, p, c, k, cad) in enumerate(zip(y, pred_, conf_, ext, cads)):
        if not regras.roteamento_texto(p, c, limiar, k, cad, params):
            auto += 1
            if t != "sem_ocorrencia":
                fa += 1
                falsos.append(i)
            else:
                auto_ok += 1
    return {"seguiriam_automatico": auto, "taxa_automacao": round(auto / len(y), 4),
            "falso_automatico": fa, "sem_ocorrencia_reais": n_sem, "sem_ocorrencia_automaticos": auto_ok,
            "taxa_automacao_dos_sem_ocorrencia": round(auto_ok / n_sem, 4) if n_sem else None,
            "_indices_falso_automatico": falsos}


def avaliar(df: pd.DataFrame, modelos: dict, params: dict, nome: str) -> tuple[dict, pd.DataFrame]:
    """modelos: {nome: (pipeline, limiar, versao_extracao)}. Linha de base: palavras-chave + extração v1."""
    textos = df["texto"].tolist()
    y = df["classe"].tolist()
    cads = df["kg_cadastrado"].tolist()
    gab = [None if v is None or pd.isna(v) else float(v) for v in df["kg_recebido_gabarito"]]
    det = df[["id", "texto", "classe", "kg_recebido_gabarito", "kg_cadastrado"]].copy()
    res = {"conjunto": nome, "n": len(y), "distribuicao_classes": {c: int(y.count(c)) for c in CLASSES}}
    for mnome, (modelo, limiar, vext) in modelos.items():
        proba = modelo.predict_proba(textos)
        pred = [str(modelo.classes_[i]) for i in proba.argmax(axis=1)]
        conf = proba.max(axis=1).round(4).tolist()
        ext = [extrair_kg(t, versao=vext)["kg_extraido"] for t in textos]
        rot = roteamento(y, pred, conf, ext, cads, limiar, params)
        res[mnome] = {"limiar": limiar, "extracao_kg_versao": vext, "classificacao": cls_metricas(y, pred),
                      "falso_automatico_so_classificador": falso_automatico_classificador(y, pred, conf, limiar),
                      "roteamento_regras_de_texto_R4_a_R7": {k: v for k, v in rot.items() if not k.startswith("_")},
                      "extracao_kg": kg_metricas(gab, ext)}
        det[f"previsto_{mnome}"] = pred
        det[f"confianca_{mnome}"] = conf
        det[f"kg_extraido_{mnome}"] = ext
        det[f"falso_automatico_{mnome}"] = [i in rot["_indices_falso_automatico"] for i in range(len(y))]
    base = [classificar_palavras_chave(t) for t in textos]
    ext1 = [extrair_kg(t, versao=1)["kg_extraido"] for t in textos]
    rotb = roteamento(y, base, [1.0] * len(base), ext1, cads, 0.7, params)
    res["linha_de_base_palavras_chave"] = {
        "classificacao": cls_metricas(y, base),
        "roteamento_regras_de_texto_R4_a_R7": {k: v for k, v in rotb.items() if not k.startswith("_")}}
    det["previsto_base"] = base
    return res, det


def causa_provavel(texto, prev, vocab) -> str:
    toks = [t for t in tokenizar(preprocessar(texto)) if t != "numtok"]
    oov = [t for t in toks if t not in vocab]
    if toks and len(oov) / len(toks) >= 0.5:
        return f"vocabulário não visto no treino ({len(oov)}/{len(toks)} palavras: {', '.join(oov[:5])})"
    if prev == "sem_ocorrencia":
        return "nenhuma palavra de ocorrência conhecida pelo modelo"
    return "palavras compartilhadas entre classes no treino"


def vocab_palavras(modelo) -> set:
    tf = modelo.named_steps["tfidf"]
    if hasattr(tf, "vocabulary_"):
        return set(tf.vocabulary_)
    return set(dict(tf.transformer_list)["palavras"].vocabulary_)


def pesos_por_classe(modelo, n=8) -> dict:
    clf = modelo.named_steps["clf"]
    nomes = modelo.named_steps["tfidf"].get_feature_names_out()
    return {str(c): [str(nomes[j]).replace("palavras__", "").replace("caracteres__", "c:")
                     for j in np.argsort(clf.coef_[i])[::-1][:n]] for i, c in enumerate(clf.classes_)}


def erros_de(det, conj, mnome, vocab) -> tuple[list, list]:
    erros, erros_kg = [], []
    for _, r in det.iterrows():
        if r[f"previsto_{mnome}"] != r["classe"]:
            erros.append({"conjunto": conj, "id": r["id"], "texto": r["texto"], "real": r["classe"],
                          "previsto": r[f"previsto_{mnome}"], "confianca": r[f"confianca_{mnome}"],
                          "falso_automatico": bool(r[f"falso_automatico_{mnome}"]),
                          "causa_provavel_heuristica": causa_provavel(r["texto"], r[f"previsto_{mnome}"], vocab)})
        g, e = r["kg_recebido_gabarito"], r[f"kg_extraido_{mnome}"]
        g = None if g is None or pd.isna(g) else float(g)
        e = None if e is None or pd.isna(e) else float(e)
        if not ((g is None and e is None) or (g is not None and e is not None and abs(g - e) <= 0.01)):
            erros_kg.append({"conjunto": conj, "id": r["id"], "texto": r["texto"], "kg_gabarito": g, "kg_extraido": e})
    return erros, erros_kg


def tabela_md(cab, linhas) -> str:
    out = ["| " + " | ".join(cab) + " |", "|" + "---|" * len(cab)]
    for l in linhas:
        out.append("| " + " | ".join(str(x).replace("|", "/") for x in l) + " |")
    return "\n".join(out)


def matriz_md(m) -> str:
    cab = ["real \\ previsto"] + m["linhas_real_colunas_previsto"]
    return tabela_md(cab, [[c] + row for c, row in zip(m["linhas_real_colunas_previsto"], m["valores"])])


def bloco_md(r: dict, nomes_modelos: list[str]) -> str:
    bl = r["linha_de_base_palavras_chave"]
    cab = ["métrica"] + nomes_modelos + ["linha de base (palavras-chave)"]

    def linha(rotulo, f, fb):
        return [rotulo] + [f(r[m]) for m in nomes_modelos] + [fb(bl)]
    linhas = [
        linha("acurácia", lambda m: m["classificacao"]["acuracia"], lambda b: b["classificacao"]["acuracia"]),
        linha("F1 macro", lambda m: m["classificacao"]["f1_macro"], lambda b: b["classificacao"]["f1_macro"]),
        linha("falso automático (roteamento R4 a R7)", lambda m: m["roteamento_regras_de_texto_R4_a_R7"]["falso_automatico"],
              lambda b: b["roteamento_regras_de_texto_R4_a_R7"]["falso_automatico"]),
        linha("seguiriam automático", lambda m: f"{m['roteamento_regras_de_texto_R4_a_R7']['seguiriam_automatico']} de {r['n']}",
              lambda b: f"{b['roteamento_regras_de_texto_R4_a_R7']['seguiriam_automatico']} de {r['n']}"),
        linha("sem_ocorrencia que seguiriam automático",
              lambda m: f"{m['roteamento_regras_de_texto_R4_a_R7']['sem_ocorrencia_automaticos']} de "
                        f"{m['roteamento_regras_de_texto_R4_a_R7']['sem_ocorrencia_reais']}",
              lambda b: f"{b['roteamento_regras_de_texto_R4_a_R7']['sem_ocorrencia_automaticos']} de "
                        f"{b['roteamento_regras_de_texto_R4_a_R7']['sem_ocorrencia_reais']}"),
        linha("kg recebido exato (±0,01 kg)", lambda m: f"{m['extracao_kg']['acertos']} de {m['extracao_kg']['n']}",
              lambda b: "(extração v1)"),
        linha("limiar de confiança", lambda m: m["limiar"], lambda b: "não se aplica"),
    ]
    partes = [f"**n = {r['n']}** ({', '.join(f'{k}: {v}' for k, v in r['distribuicao_classes'].items())})", "",
              tabela_md(cab, linhas), ""]
    for m in nomes_modelos:
        pc = [[c, v["precisao"], v["revocacao"], v["f1"], v["suporte"]] for c, v in r[m]["classificacao"]["por_classe"].items()]
        kg = r[m]["extracao_kg"]
        partes += [f"Por classe ({m}):", "", tabela_md(["classe", "precisão", "revocação", "F1", "suporte"], pc), "",
                   f"Matriz de confusão ({m}):", "", matriz_md(r[m]["classificacao"]["matriz_confusao"]), "",
                   f"Extração do kg ({m}, extração v{r[m]['extracao_kg_versao']}): {kg['acertos']} de {kg['n']} exatos; "
                   f"dos {kg['n_com_kg_no_gabarito']} com kg no gabarito, {kg['nao_encontrado']} não encontrados e "
                   f"{kg['valor_errado']} com valor errado; {kg['kg_extraido_sem_kg_no_gabarito']} sem kg no gabarito "
                   "receberam um kg.", ""]
    partes += ["Matriz de confusão (linha de base):", "", matriz_md(bl["classificacao"]["matriz_confusao"])]
    return "\n".join(partes)


def main():
    params = carregar_parametros()
    arq = SINT / "ocorrencias_rotuladas.csv"
    arq_extra = SINT / "ocorrencias_rotuladas_v2_extra.csv"
    arq_dev = SINT / "ocorrencias_fora_do_molde.csv"
    if not arq.exists() or not arq_extra.exists():
        sys.exit("ERRO: rode antes `python gerar_dados_sinteticos.py` (conjunto rotulado ausente).")
    df, extra, dev = ler(arq), ler(arq_extra), ler(arq_dev)
    treino, teste = train_test_split(df, test_size=0.25, stratify=df["classe"], random_state=SEMENTE)
    treino_v2 = pd.concat([treino, extra], ignore_index=True)
    fabricas = {"ocorrencia-v1": (lambda: criar_pipeline(C_REG, SEMENTE), treino),
                "ocorrencia-v2": (lambda: criar_pipeline_v2(C_REG, SEMENTE), treino_v2)}
    modelos, calib = {}, {}
    (BASE / "modelos").mkdir(exist_ok=True)
    hoje = date.today().isoformat()
    for nome, (fab, tr) in fabricas.items():
        X, y = tr["texto"].tolist(), tr["classe"].tolist()
        limiar, tabela_lim, f1cv = calibrar_limiar(fab(), X, y)
        modelo = fab().fit(X, y)
        modelos[nome] = (modelo, limiar, VERSOES[nome]["extracao_kg_versao"])
        calib[nome] = {"tabela": tabela_lim, "f1_macro_validacao_cruzada_treino": f1cv, "n_treino": len(y)}
        meta = {
            "modelo": nome, "gerado_em": datetime.now().isoformat(timespec="seconds"),
            "algoritmo": VERSOES[nome]["algoritmo"], "treino": VERSOES[nome]["treino"],
            "extracao_kg_versao": VERSOES[nome]["extracao_kg_versao"], "semente": SEMENTE,
            "classes": [str(c) for c in modelo.classes_], "limiar_confianca": limiar,
            "limiar_partida": params["LIMIAR_CONFIANCA_PADRAO"],
            "calibracao_limiar": {"metodo": "validação cruzada estratificada de 5 partes só no treino; menor limiar >= "
                                            "0,70 com zero falso automático fora da dobra", "tabela": tabela_lim,
                                  "f1_macro_validacao_cruzada_treino": f1cv},
            "conjuntos": {"rotulados_v1": {"arquivo": "dados/sinteticos/ocorrencias_rotuladas.csv", "sha256": sha256(arq),
                                           "n_total": len(df), "n_treino": len(treino), "n_teste": len(teste)},
                          "extra_v2": {"arquivo": "dados/sinteticos/ocorrencias_rotuladas_v2_extra.csv",
                                       "sha256": sha256(arq_extra), "n": len(extra),
                                       "usado_no_treino": nome == "ocorrencia-v2"},
                          "desenvolvimento": {"arquivo": "dados/sinteticos/ocorrencias_fora_do_molde.csv",
                                              "sha256": sha256(arq_dev), "n": len(dev)}},
            "n_treino": len(y),
            "versoes": {"python": platform.python_version(), "scikit-learn": sklearn.__version__},
            "palavras_de_maior_peso_por_classe": pesos_por_classe(modelo),
            "limitacao": LIMITACAO,
        }
        joblib.dump(modelo, BASE / "modelos" / f"{nome}.joblib")
        (BASE / "modelos" / f"metadados_{nome.split('-')[1]}.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    res_teste, det_teste = avaliar(teste, modelos, params, "teste (25% do sintético da v1)")
    res_dev, det_dev = avaliar(dev, modelos, params, "desenvolvimento (30 'fora do molde')")
    erros, erros_kg = {}, {}
    for nome, (modelo, _, _) in modelos.items():
        vocab = vocab_palavras(modelo)
        e1, k1 = erros_de(det_teste, "teste", nome, vocab)
        e2, k2 = erros_de(det_dev, "desenvolvimento", nome, vocab)
        erros[nome], erros_kg[nome] = e1 + e2, k1 + k2
    pesos = {n: pesos_por_classe(m) for n, (m, _, _) in modelos.items()}

    saida = {"_aviso": "Métricas MEDIDAS por treinar_modelo.py em dados SINTÉTICOS. " + LIMITACAO,
             "data": hoje, "modelos": {n: {**VERSOES[n], "limiar_confianca": modelos[n][1], **calib[n]} for n in modelos},
             "teste": res_teste, "desenvolvimento": res_dev, "erros_classificacao": erros, "erros_extracao_kg": erros_kg,
             "palavras_de_maior_peso_por_classe": pesos,
             "cego_v2": "medido à parte por medir_cego_v2.py (evidencias/metricas_cego_v2_*.md)"}
    ev = BASE / "evidencias"
    ev.mkdir(exist_ok=True)
    (ev / f"metricas_ia_{hoje}.json").write_text(json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8")

    nomes = list(modelos)
    md = [f"# Métricas da IA da AIPA ({hoje}): ocorrencia-v1 x ocorrencia-v2", "",
          "> Geradas por `python treinar_modelo.py` (execução real). **Dados SINTÉTICOS, rotulados por gerador/IA, sem "
          "revisão humana.** " + LIMITACAO, "",
          "- Métricas da v1 publicadas no TAR-012 (arquivadas, sem mudança): `arquivo_v1/metricas_ia_2026-11-13_v1_TAR-012.md`.",
          "- **Conjunto cego v2 (60, a medida de generalização): `metricas_cego_v2_2026-11-13.md`** (gerado por "
          "`python medir_cego_v2.py`, que confere o SHA-256 registrado em `cego_v2_CONGELADO.md`).",
          "- \"Falso automático\" = texto com ocorrência real (classe diferente de sem_ocorrencia) que seguiria sem revisão "
          "humana pelas regras de texto R4 a R7 (classe, confiança, kg extraído x cadastrado). Meta: 0. No robô, as "
          "regras de IoT (R1 a R3) ainda se somam a estas.", "",
          "## Modelos", "",
          tabela_md(["modelo", "algoritmo", "treino", "extração do kg", "F1 macro (validação cruzada, treino)", "limiar"],
                    [[n, VERSOES[n]["algoritmo"], f"{calib[n]['n_treino']} ({VERSOES[n]['treino']})",
                      f"v{VERSOES[n]['extracao_kg_versao']}", calib[n]["f1_macro_validacao_cruzada_treino"],
                      modelos[n][1]] for n in nomes]), "",
          "## Calibração do limiar (só treino, fora da dobra)", ""]
    for n in nomes:
        md += [f"{n}:", "", tabela_md(["limiar", "falso automático (só classificador)", "seguiriam automático", "n"],
                                      [[t["limiar"], t["falso_automatico_oof"], t["seguiriam_automatico_oof"], t["n"]]
                                       for t in calib[n]["tabela"]]), ""]
    md += ["## Teste sintético (o mesmo para v1 e v2)", "", bloco_md(res_teste, nomes), "",
           "## Desenvolvimento (30 'fora do molde'; usado para ajustar a v2: NÃO mede generalização)", "",
           bloco_md(res_dev, nomes), ""]
    for n in nomes:
        md += [f"## Erros de classificação ({n}): {len(erros[n])}", "",
               "A causa é uma heurística automática (proporção de palavras fora do vocabulário de palavras do treino), "
               "não um julgamento humano.", "",
               tabela_md(["conjunto", "id", "texto", "real", "previsto", "confiança", "falso automático", "causa (heurística)"],
                         [[e["conjunto"], e["id"], e["texto"], e["real"], e["previsto"], e["confianca"],
                           "sim" if e["falso_automatico"] else "não", e["causa_provavel_heuristica"]] for e in erros[n]])
               if erros[n] else "(nenhum erro)", "",
               f"Erros de extração do kg ({n}): {len(erros_kg[n])}", "",
               tabela_md(["conjunto", "id", "texto", "kg gabarito", "kg extraído"],
                         [[e["conjunto"], e["id"], e["texto"], e["kg_gabarito"], e["kg_extraido"]] for e in erros_kg[n]])
               if erros_kg[n] else "(nenhum erro)", ""]
    md += ["## Atributos de maior peso por classe (interpretabilidade; `c:` = n-grama de caracteres)", ""]
    for n in nomes:
        md += [f"{n}:", "", tabela_md(["classe", "atributos"], [[c, ", ".join(p)] for c, p in pesos[n].items()]), ""]
    md += ["## Limites", "", "- " + LIMITACAO,
           "- O kg extraído só é usado se bater com o cadastrado (tolerância 5% ou 0,5 kg); se não bater ou faltar, o lote "
           "vai para revisão humana. Nenhuma saída da IA diz se o alimento é seguro para consumo."]
    (ev / f"metricas_ia_{hoje}.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    for n in nomes:
        print(f"{n}: treino {calib[n]['n_treino']} | F1 CV treino {calib[n]['f1_macro_validacao_cruzada_treino']} | "
              f"limiar {modelos[n][1]}")
    for conj, r in (("teste", res_teste), ("desenvolvimento", res_dev)):
        for n in nomes:
            m = r[n]
            print(f"[{conj}] n={r['n']} {n}: acc={m['classificacao']['acuracia']} F1m={m['classificacao']['f1_macro']} "
                  f"falso automático={m['roteamento_regras_de_texto_R4_a_R7']['falso_automatico']} "
                  f"automáticos={m['roteamento_regras_de_texto_R4_a_R7']['seguiriam_automatico']} "
                  f"kg exato={m['extracao_kg']['acerto_kg_exato']}")
        b = r["linha_de_base_palavras_chave"]
        print(f"[{conj}] base: acc={b['classificacao']['acuracia']} F1m={b['classificacao']['f1_macro']} "
              f"falso automático={b['roteamento_regras_de_texto_R4_a_R7']['falso_automatico']}")
    print(f"modelos: modelos/ocorrencia-v1.joblib e ocorrencia-v2.joblib | métricas: evidencias/metricas_ia_{hoje}.json e .md")
    print("cego v2: rode `python medir_cego_v2.py`")


if __name__ == "__main__":
    main()
