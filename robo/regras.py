"""Regras inteligentes do gateway G5 (R1 a R9, DESENVOLVIMENTO.md §4.3).

Cada regra que dispara acrescenta um motivo. Só segue automático o lote SEM nenhum motivo.
Nenhuma regra declara que o alimento é seguro: o resultado é "automático" ou "revisão humana".
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import calculos


@dataclass
class EntradaRegras:
    texto_presente: bool
    modelo_disponivel: bool
    classe: str | None
    confianca: float | None
    limiar: float
    kg_extraido: float | None
    kg_cadastrado: float
    kg_recebido_informado: float | None = None
    iot_fonte_disponivel: bool = True
    iot_ativacao_aceita: bool = False
    iot_desconhecido: bool = False
    lote_alterado: bool = False
    ocorrencias_automaticas: tuple = ("sem_ocorrencia",)
    detalhes: dict = field(default_factory=dict)


def avaliar(e: EntradaRegras, params: dict) -> list[str]:
    motivos: list[str] = []
    # R1: ativação da quebra da cadeia de frio (origem aceita) no período do transporte
    if e.iot_ativacao_aceita:
        motivos.append("alerta_iot_quebra_cadeia_frio")
    # R2: fonte da IoT ausente ou ilegível
    if not e.iot_fonte_disponivel:
        motivos.append("dados_iot_indisponiveis")
    # R3: valor da IoT não mapeado
    if e.iot_desconhecido:
        motivos.append("evento_iot_desconhecido")
    # R8: modelo ausente ou corrompido
    if not e.modelo_disponivel:
        motivos.append("modelo_indisponivel")
    else:
        # R4: classe diferente das automáticas
        if e.classe is not None and e.classe not in e.ocorrencias_automaticas:
            motivos.append(f"ocorrencia_{e.classe}")
        # R5: baixa confiança
        if e.confianca is not None and e.confianca < e.limiar:
            motivos.append("baixa_confianca")
    # R7: sem texto ou sem kg no texto
    if not e.texto_presente or e.kg_extraido is None:
        motivos.append("sem_confirmacao")
    else:
        # R6: divergência entre o kg extraído e o cadastrado (ou o informado no lote)
        tol = calculos.tolerancia_kg(e.kg_cadastrado, params)
        diverge = abs(e.kg_extraido - e.kg_cadastrado) > tol
        if e.kg_recebido_informado is not None and abs(e.kg_recebido_informado - e.kg_extraido) > tol:
            diverge = True
        if diverge:
            motivos.append("divergencia_kg")
    # R9: lote concluído chegou de novo com conteúdo diferente
    if e.lote_alterado:
        motivos.append("lote_alterado_apos_processamento")
    return motivos


def roteamento_texto(classe, confianca, limiar, kg_extraido, kg_cadastrado, params) -> list[str]:
    """Regras que dependem só do texto (R4 a R7), usadas para medir o 'falso automático'."""
    return avaliar(EntradaRegras(texto_presente=True, modelo_disponivel=True, classe=classe, confianca=confianca,
                                 limiar=limiar, kg_extraido=kg_extraido, kg_cadastrado=kg_cadastrado), params)
