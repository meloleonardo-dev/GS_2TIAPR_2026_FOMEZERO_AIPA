"""Orquestra o processo do BPMN (tema H): tarefas T1 a T12 e gateways G0 a G7, com o ID no código e no log.

Cada lote roda num try/except próprio: uma falha não interrompe a execução inteira [p.1 §4.b].
Nenhuma etapa declara que o alimento é seguro para consumo: ocorrência ou alerta -> revisão humana.
"""
from __future__ import annotations

import json
import time
import traceback
from pathlib import Path

from . import calculos, regras, saidas, termo_pdf
from .adaptadores import ct03 as ad_ct03
from .adaptadores import iot as ad_iot
from .banco import Banco, decidir_g4
from .config import BASE, Caminhos, agora, carregar_json
from .nlp_ocorrencia import Classificador, extrair_kg
from .observabilidade import (FalhaTarefa, Observador, backup_estado, configurar_log, mascarar, pasta_gravavel,
                              recursos)
from .portal_api import ClienteAPI
from .portal_selenium import LancadorSelenium, NavegadorIndisponivel
from . import portal_servidor
from .validacao import quarentena, validar


class Robo:
    def __init__(self, trabalho: Path, params: dict, segredos: dict, sem_portal: bool = False,
                 portal_modo: str = "nenhum", api=None, lancador=None, iniciar_portal: bool = True):
        self.params = params
        self.cam = Caminhos(trabalho, params)
        self.segredos = segredos
        self.sem_portal = sem_portal
        self.portal_modo = portal_modo
        self.api = api
        self.lancador = lancador
        self.iniciar_portal = iniciar_portal and api is None
        self.proc_portal = None
        self.portal_disponivel = False

    # ------------------------------------------------------------------ execução
    def executar(self) -> dict:
        p, cam = self.params, self.cam
        t_ini = time.perf_counter()
        inicio = agora(p["FUSO"])
        self.id_execucao = "EXEC-" + inicio.strftime("%Y%m%d-%H%M%S")
        cam.saida.mkdir(parents=True, exist_ok=True)
        logger, self.arquivo_log = configurar_log(cam.sub("logs"), self.id_execucao)
        obs = self.obs = Observador(logger, self.id_execucao)
        obs.info("E0", None, f"início da execução (trabalho={cam.trabalho.name}, origens IoT aceitas="
                             f"{p['ORIGENS_IOT_ACEITAS']}, portal_modo={self.portal_modo}, sem_portal={self.sem_portal})")
        contexto = {"id_execucao": self.id_execucao, "inicio": inicio.isoformat(), "simulado": True,
                    "arquivo_lotes": str(cam.arquivo_lotes.relative_to(cam.trabalho)) if cam.arquivo_lotes.is_relative_to(cam.trabalho) else str(cam.arquivo_lotes),
                    "modo_iot": p["ORIGENS_IOT_ACEITAS"],
                    "modo_iot_texto": ("IoT: evidência FÍSICA (origem fisico; logs reais de 10 e 11/11/2026, commit 4b09c42)."
                                       if p["ORIGENS_IOT_ACEITAS"] == ["fisico"] else
                                       f"IoT SIMULADA (origens {p['ORIGENS_IOT_ACEITAS']}); não misturar com a física.")}
        resultados: list[dict] = []
        try:
            ok = self._t1(contexto)
            if not ok:
                obs.gateway("G0", None, "nao_ambiente")
                obs.critico("E-fim", None, "execução abortada com segurança antes de gravar qualquer saída de lote")
                return self._finalizar(resultados, contexto, t_ini, abortado=True)
            obs.gateway("G0", None, "sim")
            lotes = self._t2(contexto)
            if lotes is None:
                obs.gateway("G1", None, "nao")
                return self._finalizar(resultados, contexto, t_ini)
            obs.gateway("G1", None, "sim")
            self.banco = Banco(cam.estado_db)
            self.vistos: set[str] = set()
            self.entradas: dict[str, dict] = {}
            for indice, registro in enumerate(lotes):
                resultados.append(self._processar_lote(indice, registro))
            self._t11(resultados, contexto)
            return self._finalizar(resultados, contexto, t_ini)
        finally:
            self._encerrar_recursos(contexto)

    # ------------------------------------------------------------------ T1
    def _t1(self, ctx) -> bool:
        p, cam, obs = self.params, self.cam, self.obs
        with obs.tarefa("T1"):
            rec = recursos(cam.trabalho)
            ctx["recursos"] = rec
            obs.info("T1", None, f"recursos: disco livre {rec['disco_livre_mb']} MB, memória disponível "
                                 f"{rec['memoria_disponivel_mb']} MB, CPU {rec['cpu_pct']}%")
            if rec["disco_livre_mb"] < p["DISCO_MIN_LIVRE_MB"]:
                obs.critico("T1", None, f"disco livre {rec['disco_livre_mb']} MB < mínimo {p['DISCO_MIN_LIVRE_MB']} MB")
                obs.falha("F11", None, "disco_insuficiente", "aborta antes de gravar; relatório explica")
                return False
            cam.criar_pastas()
            sem_escrita = [n for n in cam.PASTAS_SAIDA if not pasta_gravavel(cam.sub(n))]
            if sem_escrita:
                obs.critico("T1", None, f"pastas sem permissão de escrita: {sem_escrita}")
                obs.falha("F11", None, "pasta_sem_permissao", "aborta antes de gravar; relatório explica")
                return False
            faltando = [k for k in ("PORTAL_USUARIO", "PORTAL_SENHA", "PORTAL_API_TOKEN") if not self.segredos.get(k)]
            if faltando:
                obs.erro("T1", None, f"segredos ausentes no .env: {faltando} (copie .env.exemplo para .env)")
            url = p["PORTAL_URL"]
            if self.api is None:
                self.api = ClienteAPI(url, self.segredos.get("PORTAL_API_TOKEN", ""), p["TIMEOUT_API_S"],
                                      p["TENTATIVAS"], p["ESPERA_BASE_S"], obs)
            if self.iniciar_portal and not self.sem_portal and not portal_servidor.no_ar(url):
                obs.info("T1", None, f"portal SIMULADO fora do ar: subindo em {url} (modo de falha {self.portal_modo})")
                self.proc_portal = portal_servidor.iniciar(url, p["PORTAL_PORTA"], cam.portal_db, self.portal_modo,
                                                           cam.sub("logs") / "portal_simulado.log")
            self.portal_disponivel = self.api.health()
            ctx["portal"] = (f"SIMULADO em {url}, {'no ar' if self.portal_disponivel else 'FORA DO AR'}"
                             f"{' (iniciado pelo robô)' if self.proc_portal else ''}, modo de falha {self.portal_modo}")
            if self.portal_disponivel:
                obs.info("T1", None, "health do portal SIMULADO ok")
            else:
                obs.erro("T1", None, "portal SIMULADO fora do ar após as tentativas; lotes válidos ficam em falha "
                                     "portal_indisponivel e são retomados na próxima execução")
                obs.falha("F6", None, "portal_indisponivel", "Termo e CT-04 gravados; retomada na próxima execução")
            return True

    # ------------------------------------------------------------------ T2
    def _t2(self, ctx):
        p, cam, obs = self.params, self.cam, self.obs
        with obs.tarefa("T2"):
            self.mapa_ct03 = carregar_json(BASE / "config" / "mapa_campos_ct03.json")
            self.mapa_iot = carregar_json(BASE / "config" / "mapa_campos_iot.json")
            self.iot = ad_iot.ler_pasta(cam.pasta_iot, self.mapa_iot)
            n_tipos = {}
            for m in self.iot["mensagens"]:
                n_tipos[m["tipo_mensagem"]] = n_tipos.get(m["tipo_mensagem"], 0) + 1
            ctx["iot_resumo"] = (f"{len(self.iot['arquivos'])} arquivo(s), {len(self.iot['mensagens'])} mensagens "
                                 f"{n_tipos}, {len(self.iot['linhas_invalidas'])} linha(s) inválida(s)")
            if not self.iot["disponivel"]:
                obs.aviso("T2", None, f"fonte da IoT ausente ({cam.pasta_iot.name}/*.log): todos os lotes vão para "
                                      "revisão humana (dados_iot_indisponiveis)")
                obs.falha("F2", None, "dados_iot_indisponiveis", "todos os lotes -> revisão humana")
            else:
                obs.info("T2", None, f"IoT lida: {ctx['iot_resumo']}")
            for inv in self.iot["linhas_invalidas"]:
                obs.aviso("T2", None, f"linha da IoT ignorada ({inv['fonte_arquivo']}:{inv['linha']}, {inv['erro']})")
                obs.falha("F4", None, f"iot_linha_invalida:{inv['fonte_arquivo']}:{inv['linha']}", "linha ignorada; leitura continua")
            self.clf = Classificador(cam.modelo)
            meta = carregar_json(cam.metadados_modelo) if cam.metadados_modelo.exists() else {}
            self.limiar = float(meta.get("limiar_confianca", p["LIMIAR_CONFIANCA_PADRAO"]))
            self.nome_modelo = str(meta.get("modelo") or cam.modelo.stem)
            self.versao_extracao = int(meta.get("extracao_kg_versao", 2))
            ctx["modelo"] = (f"{self.nome_modelo} carregado (extração do kg v{self.versao_extracao})"
                             if self.clf.disponivel else f"INDISPONÍVEL ({self.clf.erro})")
            ctx["limiar_confianca"] = self.limiar
            if not self.clf.disponivel:
                obs.erro("T2", None, f"modelo indisponível ({self.clf.erro}): todos os lotes vão para revisão humana")
                obs.falha("F3", None, "modelo_indisponivel", "todos os lotes -> revisão humana")
            self.decisoes, avisos = saidas.ler_decisoes(cam.arquivo_decisoes)
            for a in avisos:
                obs.aviso("T2", None, f"decisão de revisão ignorada: {a}")
            if self.decisoes:
                obs.info("H1", None, f"{len(self.decisoes)} decisão(ões) humana(s) lida(s) de {cam.arquivo_decisoes.name}")
            try:
                lotes = ad_ct03.ler_arquivo(cam.arquivo_lotes)
            except FileNotFoundError:
                obs.erro("T2", None, f"entrada_ausente: {cam.arquivo_lotes.name} não existe; nada a processar")
                obs.falha("F1", None, "entrada_ausente", "nada a processar; relatório explica; código de saída 0")
                return None
            except ad_ct03.EntradaIlegivel as e:
                obs.erro("T2", None, f"entrada_ilegivel: {e}")
                obs.falha("F1", None, "entrada_ilegivel", "nada a processar; relatório explica")
                return None
            b = backup_estado(cam.estado_db, cam.sub("backup"), self.id_execucao)
            if b:
                obs.info("T2", None, f"backup do estado: {b.name}")
            obs.info("T2", None, f"{len(lotes)} registro(s) lido(s) de {cam.arquivo_lotes.name}")
            return lotes

    # ------------------------------------------------------------------ por lote
    def _processar_lote(self, indice: int, registro) -> dict:
        p, obs = self.params, self.obs
        lote, erros_conv = ad_ct03.adaptar(registro if isinstance(registro, dict) else {}, self.mapa_ct03)
        lid = lote.get("lote_id") or None
        chave = lid or f"indice{indice}"
        res = {"indice": indice, "lote_id": lid or "", "status": None, "motivo": []}
        if lote.get("status_logistico") != p["STATUS_PROCESSAVEL"]:
            obs.gateway("G2", chave, f"nao ({lote.get('status_logistico')})")
            res["status"] = "ignorado_nao_entregue"
            return res
        obs.gateway("G2", chave, "sim")
        if lid:
            self.entradas[lid] = lote
        obs.iniciar_lote(chave)
        momento = agora(p["FUSO"]).isoformat()
        ct04 = saidas.ct04_base(lote, p, self.id_execucao, momento)
        try:
            # T3 validar
            with obs.tarefa("T3", chave) as reg:
                erros = validar(lote, erros_conv, self.mapa_ct03["obrigatorios"])
                if erros:
                    reg["resultado"], reg["motivo"] = "erro", "dado_invalido"
            if erros:
                obs.gateway("G3", chave, "nao")
                if self.banco.quarentena_registrada(lote["_hash"]):
                    obs.gateway("G4", chave, "duplicado")
                    obs.info("T3", chave, "registro inválido idêntico já está em quarentena: ignorado")
                    obs.falha("F5", chave, "invalido_repetido", "ignorado; já em quarentena")
                    res["status"] = "ignorado_duplicado"
                    obs.fechar_lote(chave)
                    return res
                self.banco.registrar_quarentena(lote["_hash"], lid, erros, self.id_execucao)
                q = quarentena(self.cam.sub("quarentena"), indice, lote, erros, self.id_execucao)
                for c in erros:
                    obs.aviso("T3", chave, f"campo inválido: {c}")
                ct04["status"], ct04["motivo"] = "falha", [f"dado_invalido:{c}" for c in erros]
                obs.falha("F4", chave, ",".join(ct04["motivo"]), f"quarentena ({q.name}); os outros lotes seguem")
                return self._t10(res, ct04, lote, indice, "T3")
            obs.gateway("G3", chave, "sim")

            # T4 idempotência
            with obs.tarefa("T4", chave):
                if lid in self.vistos:
                    g4 = "duplicado"
                else:
                    anterior = self.banco.obter(lid)
                    g4 = decidir_g4(anterior, lote["_hash"], self.decisoes.get(lid))
                self.vistos.add(lid)
            obs.gateway("G4", chave, g4)
            if g4 == "duplicado":
                obs.info("T4", chave, "lote já tratado com o mesmo conteúdo: ignorado (não lança de novo)")
                obs.falha("F5", chave, "lote_duplicado", "ignorado; nenhum lançamento novo")
                res["status"] = "ignorado_duplicado"
                obs.fechar_lote(chave)
                return res

            kg_validado, origem_qtd = None, None
            if g4 == "decisao_revisao":
                d = self.decisoes[lid]
                ct04 = dict(anterior["ct04"])
                ct04.update({"id_execucao": self.id_execucao, "processado_em": momento})
                obs.info("H1", chave, f"decisão humana: {d['decisao']} (revisor {d['revisor'] or 'sem código'})")
                if d["decisao"] == "reprovado":
                    ct04["revisao"] = {"situacao": "reprovado", "decidido_em": momento, "revisor": d["revisor"]}
                    ct04["motivo"] = list(dict.fromkeys(ct04["motivo"] + ["reprovado_na_revisao"]))
                    return self._t10(res, ct04, lote, indice, "H1")
                ct04["revisao"] = {"situacao": "aprovado", "decidido_em": momento, "revisor": d["revisor"],
                                   "motivos_originais": ct04["motivo"]}
                ct04["motivo"] = []
                kg_validado, origem_qtd = d["kg_aprovado"], "revisao_humana"
            elif g4 == "retomar" and anterior["ct04"].get("quantidade_recebida_kg") is not None:
                obs.info("T4", chave, f"retomando lote pendente da etapa {anterior['etapa']} "
                                      f"(motivo anterior {anterior['motivos']})")
                prev = anterior["ct04"]
                ct04["ia"], ct04["revisao"] = prev["ia"], prev.get("revisao")
                kg_validado, origem_qtd = prev["quantidade_recebida_kg"], prev["origem_quantidade"]
            else:
                ia, motivos = self._t5_t6(lote, chave, alterado=(g4 == "alterado_apos_processamento"))
                ct04["ia"] = ia
                if motivos:
                    obs.gateway("G5", chave, "revisao_humana")
                    ct04.update({"status": "revisao_humana", "motivo": motivos,
                                 "revisao": {"situacao": "pendente", "decidido_em": None}})
                    obs.info("G5", chave, f"revisão humana: {motivos}")
                    return self._t10(res, ct04, lote, indice, "T6")
                obs.gateway("G5", chave, "automatico")
                if ia["kg_extraido"] is not None:
                    kg_validado, origem_qtd = ia["kg_extraido"], "confirmacao_beneficiario"
                else:  # R7 aceitou o campo numérico: texto sem kg, mas kg recebido informado e sem divergência
                    kg_validado, origem_qtd = lote["quantidade_recebida_kg"], "informado_beneficiario"

            return self._t7_a_t10(res, ct04, lote, indice, chave, kg_validado, origem_qtd)
        except Exception as e:  # noqa: BLE001 - caminho seguro para erro não previsto
            obs.erro("T10", chave, f"erro inesperado: {type(e).__name__}: {e} | {traceback.format_exc(limit=2)!r}"[:500])
            ct04["status"], ct04["motivo"] = "falha", ["erro_inesperado"]
            obs.falha("inesperado", chave, type(e).__name__, "lote marcado falha; os outros seguem")
            return self._t10(res, ct04, lote, indice, "erro")

    def _t5_t6(self, lote, chave, alterado=False):
        p, obs = self.params, self.obs
        texto = lote.get("confirmacao_entrega_texto")
        with obs.tarefa("T5", chave):
            ext = extrair_kg(texto, versao=getattr(self, "versao_extracao", 2))
            classe = conf = None
            if self.clf.disponivel and texto:
                classe, conf = self.clf.classificar(texto)
            elif self.clf.disponivel:
                classe, conf = None, None
            obs.info("T5", chave, f"IA: ocorrência={classe} confiança={conf} kg_extraido={ext['kg_extraido']} "
                                  f"kg_ocorrencia={ext['kg_ocorrencia']}")
        with obs.tarefa("T6", chave):
            if self.iot["disponivel"]:
                iot = ad_iot.avaliar_lote(lote["lote_id"], lote["_entrega_dt"], self.iot, p["ORIGENS_IOT_ACEITAS"],
                                          p["JANELA_TRANSPORTE_HORAS"])
            else:
                iot = {"monitorado": False, "ativacao_aceita": False, "desconhecido": False, "ativacoes": [],
                       "origem": None, "n_ignoradas_por_origem": 0}
            valores_ct03 = {str(lote.get("evento_atual") or "").lower(), str(lote.get("estado_termico") or "").lower()}
            alerta_ct03 = bool({p["EVENTO_IOT"], "alerta"} & valores_ct03)
            for a in sorted(iot["ativacoes"], key=lambda a: a["tipo_mensagem"] != "alerta_ativacao")[:3]:
                obs.info("T6", chave, f"ativação {p['EVENTO_IOT']} ({a['tipo_mensagem']}) origem={a['origem']} "
                                      f"seq={a['seq']} ts={a['ts']} ({a['fonte_arquivo']}:{a['linha']})")
            if iot.get("n_normalizacoes_no_periodo"):
                obs.info("T6", chave, f"{iot['n_normalizacoes_no_periodo']} normalização(ões) no período: não apagam "
                                      "o histórico de ativação")
            if len(iot["ativacoes"]) > 3:
                obs.info("T6", chave, f"... {len(iot['ativacoes'])} ativações no período no total")
            if iot.get("n_ignoradas_por_origem"):
                obs.info("T6", chave, f"{iot['n_ignoradas_por_origem']} mensagem(ns) IoT de origem fora de "
                                      f"{p['ORIGENS_IOT_ACEITAS']} ignorada(s) (não misturar físico e simulado)")
            for d in iot.get("desconhecidos", [])[:3]:
                obs.aviso("T6", chave, f"valor IoT não mapeado estado={d['estado_bruto']} evento={d['evento_bruto']} "
                                       f"({d['fonte_arquivo']}:{d['linha']})")
            entrada = regras.EntradaRegras(
                texto_presente=bool(texto and texto.strip()), modelo_disponivel=self.clf.disponivel, classe=classe,
                confianca=conf, limiar=self.limiar, kg_extraido=ext["kg_extraido"],
                kg_cadastrado=lote["quantidade_disponibilizada_kg"], kg_recebido_informado=lote.get("quantidade_recebida_kg"),
                iot_fonte_disponivel=self.iot["disponivel"], iot_ativacao_aceita=iot["ativacao_aceita"] or alerta_ct03,
                iot_desconhecido=iot["desconhecido"], lote_alterado=alterado,
                ocorrencias_automaticas=tuple(p["OCORRENCIAS_AUTOMATICAS"]),
                divergencias_informadas=tuple(lote.get("divergencias_informadas") or ()),
                triagem_visual=lote.get("triagem_visual"))
            motivos = regras.avaliar(entrada, p)
            if not self.clf.disponivel:
                self.obs.falha("F3", chave, "modelo_indisponivel", "revisão humana")
            if not self.iot["disponivel"]:
                self.obs.falha("F2", chave, "dados_iot_indisponiveis", "revisão humana")
        ia = {"ocorrencia": classe, "confianca": conf, "kg_extraido": ext["kg_extraido"],
              "alerta_iot": ("quebra_cadeia_frio" if iot["ativacao_aceita"] or alerta_ct03 else
                             ("desconhecido" if (iot["desconhecido"] or not self.iot["disponivel"]) else
                              "sem_alerta_registrado")),
              "iot_monitorado": iot["monitorado"], "iot_origem": iot["origem"],
              "iot_ativacoes_no_periodo": len(iot["ativacoes"]),
              "iot_ativacao_referencia": next(iter(sorted(iot["ativacoes"], key=lambda a: a["tipo_mensagem"] !=
                                                         "alerta_ativacao")), None),
              "alerta_ct03": alerta_ct03,
              "kg_informado": lote.get("quantidade_recebida_kg"),
              "divergencias_informadas": list(lote.get("divergencias_informadas") or []),
              "triagem_visual": lote.get("triagem_visual"),
              "modelo": getattr(self, "nome_modelo", None) if self.clf.disponivel else None,
              "limiar_confianca": self.limiar}
        self._ultimo_texto = mascarar(texto)
        return ia, motivos

    def _t7_a_t10(self, res, ct04, lote, indice, chave, kg, origem):
        p, obs = self.params, self.obs
        lid, doador = lote["lote_id"], lote["doador_id"]
        with obs.tarefa("T7", chave):
            co2 = calculos.co2_evitado(kg, p)
            pts = calculos.pontos(kg, p)
            acum_antes = self.banco.acumulado_doador(doador, excluir_lote=lid)
            acum = round(acum_antes + kg, 3)
            selo, sit = calculos.selo(acum, p)
            obs.info("T7", chave, f"kg validado {kg} ({origem}) -> CO₂ evitado {co2} kg CO₂eq (estimativa), "
                                  f"{pts} pontos, acumulado do doador {acum} kg -> selo {selo or sit}")
        ct04.update({"quantidade_recebida_kg": kg, "origem_quantidade": origem, "co2_evitado_kg_co2eq": co2})
        termo_id = f"TERMO-{lid}"
        arq_termo = self.cam.sub("termos") / f"TERMO_{lid}.pdf"
        try:
            with obs.tarefa("T8", chave):
                dados_termo = {**{k: lote.get(k) for k in ("lote_id", "doador_id", "doador_nome_ficticio", "beneficiario_id",
                                                             "beneficiario_tipo", "alimento_descricao",
                                                             "quantidade_disponibilizada_kg", "entrega_confirmada_em")},
                               "quantidade_recebida_kg": kg, "origem_quantidade": origem, "co2_evitado_kg_co2eq": co2,
                               "metodologia_carbono": ct04["metodologia_carbono"], "pontos": pts, "selo_verde_esg": selo,
                               "selo_situacao": sit, "kg_acumulado_doador": acum, "termo_doacao_id": termo_id,
                               "id_execucao": self.id_execucao, "emitido_em": agora(p["FUSO"]).isoformat()}
                termo_pdf.gerar(dados_termo, arq_termo)
                ok, det = termo_pdf.conferir(arq_termo, lid, co2)
                if not ok:
                    raise FalhaTarefa("termo_invalido", det)
            obs.gateway("G6", chave, "sim")
            ct04["termo_doacao_id"] = termo_id
            ct04["termo_doacao_arquivo"] = str(arq_termo.relative_to(self.cam.trabalho)).replace("\\", "/")
            obs.info("T8", chave, f"Termo de Doação gerado e conferido: {arq_termo.name}")

            with obs.tarefa("T9", chave):
                protocolo, meio = self._t9(lote, kg, co2, pts, selo, chave)
            obs.gateway("G7", chave, "sim")
        except FalhaTarefa as e:
            if e.motivo == "termo_invalido":
                obs.gateway("G6", chave, "nao")
            else:
                obs.gateway("G7", chave, "nao")
            obs.erro("T9" if e.motivo != "termo_invalido" else "T8", chave, f"falha tratada: {e.motivo} ({e.detalhe})")
            codigo = {"portal_indisponivel": "F6", "portal_timeout": "F7", "confirmacao_api_falhou": "F8",
                      "credenciais_invalidas": "F9", "termo_invalido": "G6"}.get(e.motivo, e.motivo)
            obs.falha(codigo, chave, e.motivo, "status falha; pontos e selo null; retomado na próxima execução")
            ct04.update({"status": "falha", "motivo": [e.motivo], "kg_acumulado_doador": acum_antes,
                         "pontos_acumulados_doador": self._pontos_acumulados(doador, lid)})
            return self._t10(res, ct04, lote, indice, "T9" if e.motivo != "termo_invalido" else "T8")
        ct04.update({"status": "processado", "motivo": [], "pontos": pts, "selo_verde_esg": selo, "selo_situacao": sit,
                     "kg_acumulado_doador": acum,
                     "pontos_acumulados_doador": self._pontos_acumulados(doador, lid) + pts,
                     "portal": {"lancado": True, "protocolo": protocolo, "confirmado_api": True, "meio": meio}})
        self.banco.registrar_lancamento(lid, protocolo, meio, True, agora(p["FUSO"]).isoformat())
        res["protocolo"] = protocolo
        return self._t10(res, ct04, lote, indice, "T10")

    def _pontos_acumulados(self, doador, excluir):
        return sum((l["ct04"] or {}).get("pontos") or 0 for l in self.banco.todos()
                   if l["doador_id"] == doador and l["status"] == "processado" and l["lote_id"] != excluir)

    def _t9(self, lote, kg, co2, pts, selo, chave):
        p, obs = self.params, self.obs
        lid = lote["lote_id"]
        if not self.portal_disponivel:
            raise FalhaTarefa("portal_indisponivel", "health falhou no T1")
        if not all(self.segredos.get(k) for k in ("PORTAL_USUARIO", "PORTAL_SENHA", "PORTAL_API_TOKEN")):
            raise FalhaTarefa("credenciais_invalidas", "segredos ausentes no .env")
        dados = {"lote_id": lid, "doador_id": lote["doador_id"], "kg": f"{kg:.2f}", "co2": f"{co2:.2f}",
                 "pontos": pts, "selo": selo or ""}
        existente = self.api.consultar(lid)
        if existente:
            protocolo, meio = existente["protocolo"], existente.get("meio")
            obs.info("T9", chave, f"lote já lançado no portal (protocolo {protocolo}): não lança de novo")
        else:
            if self.lancador is None:
                self.lancador = LancadorSelenium(p["PORTAL_URL"], self.segredos["PORTAL_USUARIO"],
                                                 self.segredos["PORTAL_SENHA"], self.cam.sub("prints"),
                                                 p["TIMEOUT_PORTAL_S"], p["HEADLESS"], p["NAVEGADOR"],
                                                 p["TENTATIVAS"], p["ESPERA_BASE_S"], obs)
            try:
                protocolo = self.lancador.lancar(dados)
                meio = "selenium"
                obs.info("T9", chave, f"lançado pelo Selenium, protocolo {protocolo}")
            except NavegadorIndisponivel as e:
                obs.erro("T9", chave, f"navegador não iniciou ({e}); contingência pela API REST")
                obs.falha("F10", chave, "navegador_indisponivel", "lançamento por POST /api/lancamentos (api_contingencia)")
                protocolo = self.api.lancar(dados)
                meio = "api_contingencia"
        conf = self.api.consultar(lid)
        if not conf or conf.get("protocolo") != protocolo or int(conf.get("pontos", -1)) != pts:
            raise FalhaTarefa("confirmacao_api_falhou", "API não confirma o lançamento feito")
        obs.info("T9", chave, f"lançamento confirmado pela API REST (protocolo {protocolo}, meio {meio})")
        return protocolo, meio

    def _t10(self, res, ct04, lote, indice, etapa):
        obs, chave = self.obs, (lote.get("lote_id") or f"indice{indice}")
        with obs.tarefa("T10", chave):
            if ct04["status"] != "processado" and ct04["kg_acumulado_doador"] is None and ct04["doador_id"] and hasattr(self, "banco"):
                ct04["kg_acumulado_doador"] = self.banco.acumulado_doador(ct04["doador_id"])
                ct04["pontos_acumulados_doador"] = self._pontos_acumulados(ct04["doador_id"], None)
            if ct04["lote_id"]:
                self.banco.gravar_lote(ct04, lote["_hash"], etapa, agora(self.params["FUSO"]).isoformat())
            saidas.gravar_ct04(self.cam.sub("ct04"), ct04, indice)
            if not ct04["lote_id"]:
                self._sem_id = getattr(self, "_sem_id", []) + [ct04]
            if ct04["status"] == "revisao_humana" and ct04["lote_id"]:
                self._textos = getattr(self, "_textos", {})
                self._textos[ct04["lote_id"]] = getattr(self, "_ultimo_texto", None)
        obs.info("T10", chave, f"status {ct04['status']} motivo {ct04['motivo']}")
        obs.fechar_lote(chave)
        res.update({"status": ct04["status"], "motivo": ct04["motivo"], "co2_evitado_kg_co2eq": ct04["co2_evitado_kg_co2eq"],
                    "pontos": ct04["pontos"], "selo_verde_esg": ct04["selo_verde_esg"],
                    "selo_situacao": ct04["selo_situacao"], "protocolo": ct04["portal"]["protocolo"]})
        return res

    # ------------------------------------------------------------------ T11 / T12
    def _t11(self, resultados, ctx):
        obs, cam = self.obs, self.cam
        with obs.tarefa("T11"):
            estado = self.banco.todos()
            saidas.gravar_ct04_agregado(cam.sub("ct04"), [l["ct04"] for l in estado] + getattr(self, "_sem_id", []))
            textos = getattr(self, "_textos", {})
            fila = []
            for l in estado:
                c = l["ct04"]
                if c["status"] == "revisao_humana" and (c.get("revisao") or {}).get("situacao") == "pendente":
                    e = self.entradas.get(c["lote_id"], {})
                    fila.append({"lote_id": c["lote_id"], "doador_id": c["doador_id"], "motivos": ",".join(c["motivo"]),
                                 "ocorrencia_prevista": c["ia"].get("ocorrencia"), "confianca": c["ia"].get("confianca"),
                                 "kg_extraido": c["ia"].get("kg_extraido"),
                                 "kg_cadastrado": e.get("quantidade_disponibilizada_kg"),
                                 "alerta_iot": c["ia"].get("alerta_iot"),
                                 "texto_confirmacao_mascarado": textos.get(c["lote_id"]) or mascarar(e.get("confirmacao_entrega_texto")) or ""})
            saidas.gravar_fila_revisao(cam.sub("revisao"), fila)
            obs.info("T11", None, f"fila de revisão humana: {len(fila)} lote(s) pendente(s)")
            cont = {s: sum(r["status"] == s for r in resultados) for s in ("processado", "revisao_humana", "falha")}
            trat = sum(cont.values())
            resumo = {"ignorados_nao_entregues": sum(r["status"] == "ignorado_nao_entregue" for r in resultados),
                      "taxa_automacao": round(cont["processado"] / trat, 4) if trat else None,
                      "taxa_revisao_humana": round(cont["revisao_humana"] / trat, 4) if trat else None,
                      "taxa_erros": round(cont["falha"] / trat, 4) if trat else None}
            saidas.gravar_ct05(cam.sub("ct05"), estado, resumo, self.params, self.id_execucao,
                               agora(self.params["FUSO"]).isoformat(), self.entradas)
            obs.info("T11", None, "CT-05 gravado (indicadores.json, historico_entregas.csv)")

    def _encerrar_recursos(self, ctx):
        if self.lancador is not None and hasattr(self.lancador, "fechar"):
            try:
                self.lancador.fechar()
            except Exception:  # noqa: BLE001
                pass
        if self.proc_portal:
            portal_servidor.parar(self.proc_portal)
            self.obs.info("E1", None, "portal SIMULADO iniciado pelo robô foi encerrado")
        if hasattr(self, "banco"):
            self.banco.fechar()

    def _finalizar(self, resultados, ctx, t_ini, abortado=False):
        obs, p = self.obs, self.params
        if self.portal_disponivel and self.api is not None:
            try:
                ctx["portal_resumo"] = self.api.resumo()
                ctx["portal_total_lancamentos"] = ctx["portal_resumo"]["total_lancamentos"]
            except Exception as e:  # noqa: BLE001
                ctx["portal_total_lancamentos"] = None
                obs.aviso("T12", None, f"não foi possível ler o resumo do portal: {type(e).__name__}")
        with obs.tarefa("T12"):
            ctx["fim"] = agora(p["FUSO"]).isoformat()
            ctx["duracao_total_s"] = round(time.perf_counter() - t_ini, 2)
            ctx["abortado"] = abortado
            ctx["arquivo_log"] = self.arquivo_log.name
            gab = self.cam.gabarito_demo
            from . import relatorio
            pj, pm = relatorio.gerar(self.cam.sub("relatorios"), obs, resultados, ctx, gab)
        if hasattr(self, "banco"):
            self.banco.registrar_execucao(self.id_execucao, ctx["inicio"], ctx["fim"],
                                          {"n": len(resultados), "abortado": abortado})
        obs.info("E1", None, f"fim da execução: relatório {pm.name}")
        self.relatorio_json, self.relatorio_md = pj, pm
        return json.loads(pj.read_text(encoding="utf-8"))
