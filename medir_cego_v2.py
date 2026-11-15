"""Medição do conjunto cego v2 (TAR-013): ocorrencia-v1, ocorrencia-v2 e linha de base por palavras-chave.

- confere o SHA-256 de dados/sinteticos/ocorrencias_cego_v2.csv contra o valor registrado em
  evidencias/cego_v2_CONGELADO.md ANTES de qualquer predição; se não bater, para sem medir
- usa os modelos já treinados por treinar_modelo.py (não treina, não ajusta nada)
- grava evidencias/metricas_cego_v2_AAAA-MM-DD.json/.md

O cego tem 60 textos SINTÉTICOS (12 por classe), escritos e rotulados pelo agente de IA da AIPA e congelados antes
de qualquer mudança no modelo; sem revisão humana (DEC-044). Os modelos são determinísticos (semente fixa): rodar de
novo reproduz os mesmos números.
Uso: python medir_cego_v2.py
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

import joblib

from robo.config import carregar_parametros
from robo.nlp_ocorrencia import preprocessar, tokenizar
from treinar_modelo import (BASE, avaliar, bloco_md, erros_de, ler, tabela_md, vocab_palavras)

ARQ = BASE / "dados" / "sinteticos" / "ocorrencias_cego_v2.csv"
REGISTRO = BASE / "evidencias" / "cego_v2_CONGELADO.md"
SHA_CONGELADO = "BB432927BCCB1F27586DB9EDB5702F2397EF21C33A2F12D94E0EF85AD698FF89"
AVISO = ("Conjunto cego v2: 60 textos SINTÉTICOS (12 por classe), escritos e rotulados pelo agente de IA da AIPA, "
         "congelados (SHA-256 registrado) antes de qualquer mudança no modelo e medidos uma única vez no fim do TAR-013; "
         "sem revisão humana (DEC-044). O mesmo agente escreveu o cego e depois ajustou o gerador v2: o modelo não viu "
         "o cego, mas o autor sim (limite registrado). n = 60 é pequeno.")


def palavras(texto: str) -> set:
    return {t for t in tokenizar(preprocessar(texto)) if t != "numtok" and re.search(r"[a-z]", t)}


def main():
    sha = hashlib.sha256(ARQ.read_bytes()).hexdigest().upper()
    registrado = re.search(r"SHA-256 \| `([0-9A-F]{64})`", REGISTRO.read_text(encoding="utf-8"))
    registrado = registrado.group(1) if registrado else None
    conferido = sha == SHA_CONGELADO == registrado
    print(f"SHA-256 atual     {sha}\nSHA-256 congelado {registrado} (registro) / {SHA_CONGELADO} (script)")
    if not conferido:
        sys.exit("ERRO: o arquivo do cego v2 não é o congelado. Medição NÃO feita.")
    print("hash conferido: OK")

    params = carregar_parametros()
    modelos = {}
    for nome in ("ocorrencia-v1", "ocorrencia-v2"):
        meta = json.loads((BASE / "modelos" / f"metadados_{nome.split('-')[1]}.json").read_text(encoding="utf-8"))
        modelos[nome] = (joblib.load(BASE / "modelos" / f"{nome}.joblib"), float(meta["limiar_confianca"]),
                         int(meta["extracao_kg_versao"]))
    cego = ler(ARQ)
    res, det = avaliar(cego, modelos, params, "cego v2 (60)")
    erros, erros_kg = {}, {}
    for nome, (modelo, _, _) in modelos.items():
        erros[nome], erros_kg[nome] = erros_de(det, "cego_v2", nome, vocab_palavras(modelo))

    # quanto do vocabulário do cego cada treino conhece (palavras inteiras, sem números)
    sint = BASE / "dados" / "sinteticos"
    rot, extra, dev = ler(sint / "ocorrencias_rotuladas.csv"), ler(sint / "ocorrencias_rotuladas_v2_extra.csv"), \
        ler(sint / "ocorrencias_fora_do_molde.csv")
    v_rot = set().union(*[palavras(t) for t in rot["texto"]])
    v_extra = set().union(*[palavras(t) for t in extra["texto"]])
    v_dev = set().union(*[palavras(t) for t in dev["texto"]])
    v_cego = set().union(*[palavras(t) for t in cego["texto"]])
    v1_vocab = vocab_palavras(modelos["ocorrencia-v1"][0])
    v2_vocab = vocab_palavras(modelos["ocorrencia-v2"][0])
    so_extra = sorted(v_cego & (v_extra - v_rot - v_dev))
    cobertura = {"palavras_distintas_no_cego": len(v_cego),
                 "conhecidas_pelo_vocabulario_v1": len(v_cego & v1_vocab),
                 "conhecidas_pelo_vocabulario_v2": len(v_cego & v2_vocab),
                 "palavras_do_cego_que_so_o_gerador_v2_trouxe": so_extra}

    fa = {n: res[n]["roteamento_regras_de_texto_R4_a_R7"]["falso_automatico"] for n in modelos}
    hoje = date.today().isoformat()
    saida = {"_aviso": AVISO, "data": hoje, "medido_em": datetime.now().isoformat(timespec="seconds"),
             "arquivo": "dados/sinteticos/ocorrencias_cego_v2.csv", "sha256": sha, "hash_conferido": conferido,
             "resultado": res, "erros_classificacao": erros, "erros_extracao_kg": erros_kg,
             "cobertura_de_vocabulario": cobertura,
             "regra_de_decisao": "v2 só entra no robô se o falso automático dela não for maior que o da v1 em nenhum "
                                 "conjunto (registrada em cego_v2_CONGELADO.md antes da medição)",
             "falso_automatico_cego": fa,
             "detalhe_por_texto": json.loads(det.to_json(orient="records", force_ascii=False))}
    ev = BASE / "evidencias"
    (ev / f"metricas_cego_v2_{hoje}.json").write_text(json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8")

    nomes = list(modelos)
    md = [f"# Conjunto cego v2: medição única ({hoje})", "", "> " + AVISO, "",
          f"- Arquivo `dados/sinteticos/ocorrencias_cego_v2.csv`, SHA-256 `{sha}`: **igual ao congelado** "
          "(`cego_v2_CONGELADO.md`), conferido pelo script antes de qualquer predição.",
          f"- Medido em {saida['medido_em']} com os modelos salvos por `treinar_modelo.py` (sem treino nem ajuste aqui).",
          "- Linha de base: palavras-chave + extração do kg v1 (a mesma do TAR-012).", "",
          "## Resultado", "", bloco_md(res, nomes), ""]
    for n in nomes:
        md += [f"## Erros de classificação ({n}): {len(erros[n])}", "",
               tabela_md(["id", "texto", "real", "previsto", "confiança", "falso automático", "causa (heurística)"],
                         [[e["id"], e["texto"], e["real"], e["previsto"], e["confianca"],
                           "sim" if e["falso_automatico"] else "não", e["causa_provavel_heuristica"]] for e in erros[n]])
               if erros[n] else "(nenhum erro)", "",
               f"Erros de extração do kg ({n}): {len(erros_kg[n])}", "",
               tabela_md(["id", "texto", "kg gabarito", "kg extraído"],
                         [[e["id"], e["texto"], e["kg_gabarito"], e["kg_extraido"]] for e in erros_kg[n]])
               if erros_kg[n] else "(nenhum erro)", ""]
    md += ["## Cobertura de vocabulário (palavras inteiras, sem números)", "",
           tabela_md(["item", "valor"], [
               ["palavras distintas no cego", cobertura["palavras_distintas_no_cego"]],
               ["conhecidas pelo vocabulário de palavras da v1", cobertura["conhecidas_pelo_vocabulario_v1"]],
               ["conhecidas pelo vocabulário de palavras da v2", cobertura["conhecidas_pelo_vocabulario_v2"]],
               ["palavras do cego que só o gerador v2 trouxe (não estão no treino v1 nem no desenvolvimento)",
                ", ".join(so_extra) or "(nenhuma)"]]), "",
           "## Regra de decisão (registrada antes da medição)", "",
           f"- {saida['regra_de_decisao']}.",
           f"- Falso automático no cego: v1 = {fa['ocorrencia-v1']}, v2 = {fa['ocorrencia-v2']}."]
    (ev / f"metricas_cego_v2_{hoje}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    for n in nomes:
        m = res[n]
        print(f"[cego v2] n={res['n']} {n}: acc={m['classificacao']['acuracia']} F1m={m['classificacao']['f1_macro']} "
              f"falso automático={m['roteamento_regras_de_texto_R4_a_R7']['falso_automatico']} "
              f"automáticos={m['roteamento_regras_de_texto_R4_a_R7']['seguiriam_automatico']} "
              f"kg exato={m['extracao_kg']['acertos']}/{m['extracao_kg']['n']}")
    b = res["linha_de_base_palavras_chave"]
    print(f"[cego v2] base: acc={b['classificacao']['acuracia']} F1m={b['classificacao']['f1_macro']} "
          f"falso automático={b['roteamento_regras_de_texto_R4_a_R7']['falso_automatico']}")
    print(f"métricas: evidencias/metricas_cego_v2_{hoje}.json e .md")


if __name__ == "__main__":
    main()
