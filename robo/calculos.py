"""CO₂ evitado (estimativa), pontos e Selo Verde ESG (regra de demonstração, DEC-043/044).

CO₂ evitado (kg CO₂eq) = kg recebido validado x fator (2,54; FAO 2013, F-026). É a pegada média do
alimento desperdiçado, não uma redução medida causada pela doação. Pontos e Selo Verde ESG são regra de
demonstração proposta pela AIPA, não aprovada pelo grupo, não certificação. Indisponível = None (nunca 0).
"""
from __future__ import annotations

import math

METODOLOGIA_CARBONO = {
    "tipo": "estimativa",
    "fator_kg_co2eq_por_kg": 2.54,
    "fonte": "FAO (2013). Food wastage footprint: Impacts on natural resources. Summary report, "
             "ISBN 978-92-5-107752-8, p. 7 e 18 (F-026)",
    "calculo_do_fator": "3,3 Gt CO2eq / 1,3 Gt de alimento comestível desperdiçado (cálculo do grupo; não é número "
                        "publicado pela FAO)",
    "ano_referencia": 2007,
    "escopo": "média global, toda a cadeia (produção até a perda), sem mudança de uso da terra; não específico do "
              "alimento",
    "cenario_referencia": "hipótese: sem a doação, o alimento teria sido descartado",
    "massa_elegivel": "quantidade_recebida_kg validada (não a quantidade cadastrada)",
    "nao_inclui": "emissões de transporte e refrigeração da doação; destino evitado específico",
    "aprovacao_grupo": "pendente (PC-011)",
}

AVISO_RECOMPENSA = ("Regra de demonstração do FOMEZERO proposta pela AIPA (DEC-043), não aprovada pelo grupo, "
                    "não norma.")


def metodologia(params: dict) -> dict:
    m = dict(METODOLOGIA_CARBONO)
    m["fator_kg_co2eq_por_kg"] = params["FATOR_CO2_KG_CO2EQ_POR_KG"]
    return m


def regras_recompensa(params: dict) -> dict:
    return {"pontos_por_kg": params["PONTOS_POR_KG"], "arredondamento_pontos": "para baixo (inteiro)",
            "selo_kg_minimo_acumulado": {"Bronze": params["SELO_BRONZE_KG"], "Prata": params["SELO_PRATA_KG"],
                                         "Ouro": params["SELO_OURO_KG"]},
            "aviso": AVISO_RECOMPENSA}


def tolerancia_kg(kg_cadastrado: float, params: dict) -> float:
    return max(params["TOLERANCIA_DIVERGENCIA_PCT"] * kg_cadastrado, params["TOLERANCIA_DIVERGENCIA_MIN_KG"])


def co2_evitado(kg: float | None, params: dict) -> float | None:
    if kg is None:
        return None
    return round(kg * params["FATOR_CO2_KG_CO2EQ_POR_KG"], params["CASAS_CO2"])


def pontos(kg: float | None, params: dict) -> int | None:
    if kg is None:
        return None
    return int(math.floor(kg * params["PONTOS_POR_KG"] + 1e-9))


def selo(kg_acumulado: float, params: dict) -> tuple[str | None, str]:
    """Retorna (selo, situacao). Abaixo do mínimo: (None, 'abaixo_do_minimo')."""
    if kg_acumulado >= params["SELO_OURO_KG"]:
        return "Ouro", "concedido"
    if kg_acumulado >= params["SELO_PRATA_KG"]:
        return "Prata", "concedido"
    if kg_acumulado >= params["SELO_BRONZE_KG"]:
        return "Bronze", "concedido"
    return None, "abaixo_do_minimo"
