"""Estado do robô em SQLite (tema E): idempotência, retomada, acumulado do doador."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

ESQUEMA = """
CREATE TABLE IF NOT EXISTS lotes (
  lote_id TEXT PRIMARY KEY, hash TEXT, status TEXT, motivos TEXT, etapa TEXT, doador_id TEXT,
  kg_validado REAL, origem_quantidade TEXT, revisao_situacao TEXT, ct04 TEXT, atualizado_em TEXT, id_execucao TEXT
);
CREATE TABLE IF NOT EXISTS lancamentos (
  lote_id TEXT PRIMARY KEY, protocolo TEXT, meio TEXT, confirmado_api INTEGER, lancado_em TEXT
);
CREATE TABLE IF NOT EXISTS quarentena (
  hash TEXT PRIMARY KEY, lote_id TEXT, motivos TEXT, id_execucao TEXT
);
CREATE TABLE IF NOT EXISTS execucoes (
  id_execucao TEXT PRIMARY KEY, inicio TEXT, fim TEXT, resumo TEXT
);
"""
MOTIVOS_TRANSITORIOS = {"portal_indisponivel", "portal_timeout", "credenciais_invalidas", "confirmacao_api_falhou",
                        "termo_invalido", "erro_inesperado"}
MOTIVOS_TECNICOS_REVISAO = {"modelo_indisponivel", "dados_iot_indisponiveis"}


class Banco:
    def __init__(self, caminho: Path):
        self.caminho = Path(caminho)
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        self.con = sqlite3.connect(self.caminho)
        self.con.row_factory = sqlite3.Row
        self.con.executescript(ESQUEMA)
        self.con.commit()

    def fechar(self):
        self.con.close()

    def obter(self, lote_id: str) -> dict | None:
        r = self.con.execute("SELECT * FROM lotes WHERE lote_id = ?", (lote_id,)).fetchone()
        if not r:
            return None
        d = dict(r)
        d["motivos"] = json.loads(d["motivos"] or "[]")
        d["ct04"] = json.loads(d["ct04"]) if d["ct04"] else None
        return d

    def gravar_lote(self, ct04: dict, hash_: str, etapa: str, agora: str):
        self.con.execute(
            """INSERT INTO lotes (lote_id, hash, status, motivos, etapa, doador_id, kg_validado, origem_quantidade,
                                  revisao_situacao, ct04, atualizado_em, id_execucao)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(lote_id) DO UPDATE SET hash=excluded.hash, status=excluded.status, motivos=excluded.motivos,
                 etapa=excluded.etapa, doador_id=excluded.doador_id, kg_validado=excluded.kg_validado,
                 origem_quantidade=excluded.origem_quantidade, revisao_situacao=excluded.revisao_situacao,
                 ct04=excluded.ct04, atualizado_em=excluded.atualizado_em, id_execucao=excluded.id_execucao""",
            (ct04["lote_id"], hash_, ct04["status"], json.dumps(ct04["motivo"]), etapa, ct04["doador_id"],
             ct04["quantidade_recebida_kg"] if ct04["status"] == "processado" else None, ct04["origem_quantidade"],
             (ct04.get("revisao") or {}).get("situacao"), json.dumps(ct04, ensure_ascii=False), agora,
             ct04["id_execucao"]))
        self.con.commit()

    def acumulado_doador(self, doador_id: str, excluir_lote: str | None = None) -> float:
        r = self.con.execute("SELECT COALESCE(SUM(kg_validado), 0) FROM lotes WHERE doador_id = ? AND status = "
                             "'processado' AND lote_id != ?", (doador_id, excluir_lote or "")).fetchone()
        return round(float(r[0]), 3)

    def registrar_lancamento(self, lote_id: str, protocolo: str, meio: str, confirmado: bool, agora: str):
        self.con.execute("INSERT OR REPLACE INTO lancamentos VALUES (?,?,?,?,?)",
                         (lote_id, protocolo, meio, int(confirmado), agora))
        self.con.commit()

    def lancamento(self, lote_id: str) -> dict | None:
        r = self.con.execute("SELECT * FROM lancamentos WHERE lote_id = ?", (lote_id,)).fetchone()
        return dict(r) if r else None

    def quarentena_registrada(self, hash_: str) -> bool:
        return self.con.execute("SELECT 1 FROM quarentena WHERE hash = ?", (hash_,)).fetchone() is not None

    def registrar_quarentena(self, hash_: str, lote_id: str | None, motivos: list[str], id_execucao: str):
        self.con.execute("INSERT OR IGNORE INTO quarentena VALUES (?,?,?,?)",
                         (hash_, lote_id, json.dumps(motivos), id_execucao))
        self.con.commit()

    def todos(self) -> list[dict]:
        return [self.obter(r[0]) for r in self.con.execute("SELECT lote_id FROM lotes ORDER BY lote_id")]

    def registrar_execucao(self, id_execucao: str, inicio: str, fim: str, resumo: dict):
        self.con.execute("INSERT OR REPLACE INTO execucoes VALUES (?,?,?,?)",
                         (id_execucao, inicio, fim, json.dumps(resumo, ensure_ascii=False)))
        self.con.commit()


def decidir_g4(anterior: dict | None, hash_: str, decisao: dict | None) -> str:
    """Saída do gateway G4 (idempotência)."""
    if anterior is None:
        return "novo"
    if anterior["hash"] != hash_:
        return "alterado_apos_processamento" if anterior["status"] == "processado" else "novo"
    st, motivos = anterior["status"], set(anterior["motivos"])
    if st == "processado":
        return "duplicado"
    if st == "revisao_humana":
        if anterior.get("revisao_situacao") == "pendente" and decisao:
            return "decisao_revisao"
        if motivos and motivos <= MOTIVOS_TECNICOS_REVISAO:
            return "reavaliar"
        return "duplicado"
    if st == "falha" and motivos & MOTIVOS_TRANSITORIOS:
        return "retomar"
    return "duplicado"
