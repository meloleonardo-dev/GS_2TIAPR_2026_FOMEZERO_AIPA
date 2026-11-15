"""Termo de Doação em PDF (tema B): gera com fpdf2 e confere lendo o texto de volta com pypdf.

Só para lote validado. Documento SIMULADO, sem validade jurídica; não atesta que o alimento é seguro.
Usa a fonte padrão Helvetica (sem arquivo de fonte no repositório); o "2" de CO2 sai em subscrito.
"""
from __future__ import annotations

from pathlib import Path

from fpdf import FPDF
from pypdf import PdfReader

RODAPE = ("Documento sintético, sem validade jurídica. Não atesta que o alimento é seguro para consumo.")
TROCAS = {"₂": "2", "—": "-", "–": "-", "“": '"', "”": '"', "’": "'", "≥": ">=", "×": "x"}


def _latin(t) -> str:
    t = str(t)
    for a, b in TROCAS.items():
        t = t.replace(a, b)
    return t.encode("latin-1", "replace").decode("latin-1")


class _Termo(FPDF):
    def footer(self):
        self.set_y(-18)
        self.set_font("Helvetica", "I", 8)
        self.multi_cell(0, 4, _latin(RODAPE + " FOMEZERO - Global Solution FIAP 2026 (protótipo)."), align="C")


def _escrever_subscrito(pdf: FPDF, texto: str, h: float = 6):
    """Escreve o texto trocando cada '₂' por um 2 subscrito."""
    partes = texto.split("₂")
    for i, parte in enumerate(partes):
        pdf.write(h, _latin(parte))
        if i < len(partes) - 1:
            pdf.char_vpos = "SUB"
            pdf.write(h, "2")
            pdf.char_vpos = "LINE"
    pdf.ln(h)


def gerar(d: dict, caminho: Path) -> Path:
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    pdf = _Termo(format="A4")
    pdf.set_auto_page_break(True, margin=22)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, _latin("Termo de Doação - DOCUMENTO SIMULADO"), new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, _latin(f"{d['termo_doacao_id']} | id_execucao {d['id_execucao']} | emitido em {d['emitido_em']}"),
             new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 11)
    linhas = [
        ("Lote de doação", d["lote_id"]),
        ("Doador", f"{d['doador_id']} - {d.get('doador_nome_ficticio') or 'nome não informado'} (fictício)"),
        ("Beneficiário", f"{d['beneficiario_id']} ({d.get('beneficiario_tipo') or 'tipo não informado'})"),
        ("Alimento", d["alimento_descricao"]),
        ("Quantidade cadastrada", f"{d['quantidade_disponibilizada_kg']:.2f} kg"),
        ("Quantidade recebida validada", f"{d['quantidade_recebida_kg']:.2f} kg ({d['origem_quantidade']})"),
        ("Entrega confirmada em", d["entrega_confirmada_em"]),
    ]
    for rot, val in linhas:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(62, 7, _latin(rot + ":"))
        pdf.set_font("Helvetica", "", 11)
        pdf.multi_cell(0, 7, _latin(val), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 11)
    _escrever_subscrito(pdf, f"CO₂ evitado (kg CO₂eq), ESTIMATIVA: {d['co2_evitado_kg_co2eq']:.2f}")
    pdf.set_font("Helvetica", "", 9)
    m = d["metodologia_carbono"]
    pdf.multi_cell(0, 5, _latin(
        f"Cálculo: {d['quantidade_recebida_kg']:.2f} kg x {m['fator_kg_co2eq_por_kg']} kg CO2eq/kg. Fonte: {m['fonte']}. "
        f"Fator: {m['calculo_do_fator']}. Ano de referência {m['ano_referencia']}; {m['escopo']}. "
        f"Cenário: {m['cenario_referencia']}. Não inclui: {m['nao_inclui']}. Aprovação do grupo: {m['aprovacao_grupo']}. "
        "É a pegada média do alimento desperdiçado, não uma redução medida causada pela doação."),
        new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 11)
    selo = d["selo_verde_esg"] or f"sem selo ({d['selo_situacao']})"
    pdf.multi_cell(0, 7, _latin(f"Pontos: {d['pontos']}   |   Selo Verde ESG do doador: {selo} "
                                f"(acumulado {d['kg_acumulado_doador']:.2f} kg)"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 5, _latin(
        "Pontos e Selo Verde ESG: regra de demonstração do FOMEZERO proposta pela AIPA (10 pontos por kg; Bronze 50 kg, "
        "Prata 200 kg, Ouro 500 kg acumulados), não aprovada pelo grupo, reconhecimento interno, não certificação. "
        "Não é o 'Selo Doador de Alimentos' da Lei 15.224/2025."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 10)
    pdf.multi_cell(0, 6, _latin("Aviso: " + RODAPE + " Dados SIMULADOS; portal do parceiro SIMULADO."),
                   new_x="LMARGIN", new_y="NEXT")
    pdf.output(str(caminho))
    return caminho


def conferir(caminho: Path, lote_id: str, co2: float) -> tuple[bool, str]:
    """G6: relê o PDF e verifica lote_id, 'SIMULADO' e o valor do CO2."""
    try:
        texto = "".join(p.extract_text() or "" for p in PdfReader(str(caminho)).pages)
    except Exception as e:  # noqa: BLE001
        return False, f"PDF ilegível: {type(e).__name__}"
    faltando = [nome for nome, alvo in (("lote_id", lote_id), ("SIMULADO", "SIMULADO"), ("co2", f"{co2:.2f}"))
                if alvo not in texto]
    return (not faltando), ("ok" if not faltando else "faltando: " + ", ".join(faltando))
