"""Certificado do Selo Verde ESG em PDF: reconhecimento interno do doador, gerado a partir do estado do robô.

O selo vem do mesmo cálculo do robô (calculos.selo sobre o acumulado de lotes PROCESSADOS no banco); o portal
nunca calcula. Documento SIMULADO: reconhecimento interno do FOMEZERO, não é certificação nem o "Selo Doador de
Alimentos" da Lei 15.224/2025, e não atesta que algum alimento é seguro para consumo.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from fpdf import FPDF
from pypdf import PdfReader

from . import calculos
from .config import BASE
from .termo_pdf import _latin

IMAGENS = {nivel: BASE / "assets" / "selos" / f"selo-{nivel.lower()}.jpg" for nivel in ("Bronze", "Prata", "Ouro")}
VERMELHO = (234, 29, 44)
AVISO = ("Reconhecimento interno do FOMEZERO, com regra de demonstração não aprovada pelo grupo. Não é certificação "
         "nem o 'Selo Doador de Alimentos' da Lei 15.224/2025. Não atesta que o alimento é seguro para consumo. "
         "Dados SIMULADOS.")


def _kg(valor: float) -> str:
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _data(iso: str) -> str:
    return f"{iso[8:10]}/{iso[5:7]}/{iso[0:4]} às {iso[11:16]}" if len(iso) >= 16 else iso


class SemSelo(Exception):
    """O doador ainda não tem lote processado suficiente para um selo."""


def dados_do_doador(banco, doador_id: str, params: dict, nome_ficticio: str | None, emitido_em: str) -> dict:
    lotes = [l for l in banco.todos() if l and l["doador_id"] == doador_id and l["status"] == "processado"]
    kg = banco.acumulado_doador(doador_id)
    selo, situacao = calculos.selo(kg, params)
    if not selo:
        raise SemSelo(f"acumulado {kg:.2f} kg, abaixo do mínimo do Bronze ({params['SELO_BRONZE_KG']} kg)")
    pontos = sum((l["ct04"] or {}).get("pontos") or 0 for l in lotes)
    codigo = hashlib.sha256(f"{doador_id}|{selo}|{kg:.3f}|{emitido_em[:10]}".encode("utf-8")).hexdigest()[:12].upper()
    return {"doador_id": doador_id, "nome": (nome_ficticio or "").strip()[:60] or None, "selo": selo,
            "situacao": situacao, "kg_acumulado": kg, "pontos": pontos, "n_lotes": len(lotes),
            "emitido_em": emitido_em, "codigo": f"FZ-{codigo}",
            "faixas": calculos.regras_recompensa(params)["selo_kg_minimo_acumulado"]}


def gerar(d: dict, caminho: Path) -> Path:
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    pdf = FPDF(orientation="L", format="A4")
    pdf.set_auto_page_break(False)
    pdf.add_page()
    largura, altura = pdf.w, pdf.h
    # moldura vermelha
    pdf.set_draw_color(*VERMELHO)
    pdf.set_line_width(2.2)
    pdf.rect(8, 8, largura - 16, altura - 16)
    pdf.set_line_width(0.5)
    pdf.rect(12, 12, largura - 24, altura - 24)
    # faixa do título
    pdf.set_fill_color(*VERMELHO)
    pdf.rect(12, 12, largura - 24, 24, style="F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_xy(12, 17)
    pdf.cell(largura - 24, 14, _latin("fomezero  |  Certificado de reconhecimento"), align="C")
    # selo
    imagem = IMAGENS[d["selo"]]
    if imagem.exists():
        pdf.image(str(imagem), x=24, y=50, w=72, h=72)
    # texto
    x = 108
    pdf.set_text_color(26, 26, 26)
    pdf.set_xy(x, 50)
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 12, _latin(f"Selo Verde ESG - Nível {d['selo']}"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(x)
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 8, _latin("Conferido a"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(x)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*VERMELHO)
    pdf.multi_cell(largura - x - 22, 9, _latin(d["nome"] or "Doador FOMEZERO"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(26, 26, 26)
    pdf.set_x(x)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, _latin(f"Identificador do doador: {d['doador_id']} (conta fictícia)"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_x(x)
    pdf.set_font("Helvetica", "", 12)
    pdf.multi_cell(largura - x - 22, 7, _latin(
        f"Pelas doações de alimentos entregues e validadas pelo robô pós-entrega do FOMEZERO: "
        f"{_kg(d['kg_acumulado'])} kg em {d['n_lotes']} lote(s) de doação, {d['pontos']} pontos."),
        new_x="LMARGIN", new_y="NEXT", align="L")
    pdf.ln(2)
    pdf.set_x(x)
    pdf.set_font("Helvetica", "", 9)
    f = d["faixas"]
    pdf.multi_cell(largura - x - 22, 5, _latin(
        f"Níveis pelo total acumulado de kg validados: Bronze {f['Bronze']} kg, Prata {f['Prata']} kg, "
        f"Ouro {f['Ouro']} kg."), new_x="LMARGIN", new_y="NEXT")
    # rodapé do certificado
    pdf.set_xy(24, altura - 52)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, _latin(f"Código de conferência: {d['codigo']}   |   Emitido em {_data(d['emitido_em'])}   |   DOCUMENTO SIMULADO"),
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(24)
    pdf.set_font("Helvetica", "I", 8.5)
    pdf.set_text_color(90, 90, 90)
    pdf.multi_cell(largura - 48, 4.5, _latin(AVISO + " FOMEZERO - Global Solution FIAP 2026 (protótipo acadêmico)."),
                   new_x="LMARGIN", new_y="NEXT")
    pdf.output(str(caminho))
    return caminho


def conferir(caminho: Path, selo: str, codigo: str) -> tuple[bool, str]:
    """Relê o PDF e confere o nível, o código, 'SIMULADO' e o aviso de que não é certificação."""
    try:
        texto = " ".join("".join(p.extract_text() or "" for p in PdfReader(str(caminho)).pages).split())
    except Exception as e:  # noqa: BLE001
        return False, f"PDF ilegível: {type(e).__name__}"
    alvos = (("selo", f"Nível {selo}"), ("codigo", codigo), ("SIMULADO", "SIMULADO"), ("aviso", "Não é certificação"))
    faltando = [nome for nome, alvo in alvos if alvo not in texto]
    return (not faltando), ("ok" if not faltando else "faltando: " + ", ".join(faltando))
