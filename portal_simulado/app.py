"""PORTAL SIMULADO da prefeitura/empresa parceira (Flask, 127.0.0.1:5050). Dados fictícios.

Não é um portal real. Páginas: /login, /lancamentos/novo, POST /lancamentos (protocolo aparece depois de um
atraso via JavaScript, para o Selenium esperar). API: /health, GET/POST /api/lancamentos, GET /api/resumo.
Banco próprio (portal.db), separado do estado do robô. Credenciais e token lidos do .env (nunca do código).
Modos de falha (variável PORTAL_MODO_FALHA): nenhum | erro_api | lento | json_invalido.

Uso: python portal_simulado/app.py   (ou deixe o robô subir o portal sozinho)
"""
from __future__ import annotations

import hmac
import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path

from dotenv import dotenv_values
from flask import Flask, abort, jsonify, redirect, render_template, request, session, url_for

AQUI = Path(__file__).resolve().parent
BASE = AQUI.parent


def _segredos() -> dict:
    caminho = Path(os.environ.get("PORTAL_ENV_ARQUIVO", BASE / ".env"))
    return {k: v for k, v in dotenv_values(caminho).items() if v} if caminho.exists() else {}


def criar_app(db: str | Path | None = None, modo_falha: str | None = None, segredos: dict | None = None) -> Flask:
    app = Flask(__name__, template_folder=str(AQUI / "templates"))
    seg = segredos if segredos is not None else _segredos()
    faltando = [k for k in ("PORTAL_USUARIO", "PORTAL_SENHA", "PORTAL_API_TOKEN") if not seg.get(k)]
    if faltando:
        raise SystemExit(f"Portal simulado: configure {', '.join(faltando)} no .env (veja .env.exemplo).")
    app.secret_key = seg.get("PORTAL_CHAVE_SESSAO") or os.urandom(16).hex()
    app.config["DB"] = str(db or os.environ.get("PORTAL_DB", AQUI / "portal.db"))
    app.config["MODO_FALHA"] = (modo_falha or os.environ.get("PORTAL_MODO_FALHA", "nenhum")).lower()
    app.config["ATRASO_LENTO_S"] = float(os.environ.get("PORTAL_ATRASO_LENTO_S", "8"))
    app.config["ATRASO_PROTOCOLO_MS"] = int(os.environ.get("PORTAL_ATRASO_PROTOCOLO_MS", "1200"))

    def con():
        c = sqlite3.connect(app.config["DB"])
        c.row_factory = sqlite3.Row
        c.execute("""CREATE TABLE IF NOT EXISTS lancamentos (id INTEGER PRIMARY KEY AUTOINCREMENT, protocolo TEXT,
                     lote_id TEXT UNIQUE, doador_id TEXT, kg REAL, co2 REAL, pontos INTEGER, selo TEXT, meio TEXT,
                     criado_em TEXT)""")
        return c

    def inserir(dados: dict, meio: str):
        c = con()
        try:
            atual = c.execute("SELECT protocolo FROM lancamentos WHERE lote_id = ?", (dados["lote_id"],)).fetchone()
            if atual:
                return atual["protocolo"], False
            cur = c.execute("INSERT INTO lancamentos (lote_id, doador_id, kg, co2, pontos, selo, meio, criado_em) "
                            "VALUES (?,?,?,?,?,?,?,?)",
                            (dados["lote_id"], dados["doador_id"], float(dados["kg"]), float(dados["co2"]),
                             int(dados["pontos"]), dados.get("selo") or None, meio,
                             datetime.now().isoformat(timespec="seconds")))
            protocolo = f"SIM-{cur.lastrowid:06d}"
            c.execute("UPDATE lancamentos SET protocolo = ? WHERE id = ?", (protocolo, cur.lastrowid))
            c.commit()
            return protocolo, True
        finally:
            c.close()

    def api_falha():
        modo = app.config["MODO_FALHA"]
        if modo == "lento":
            time.sleep(app.config["ATRASO_LENTO_S"])
        if modo == "erro_api":
            return jsonify({"erro": "erro interno simulado"}), 500
        if modo == "json_invalido":
            return app.response_class("{isto nao e json", mimetype="application/json")
        return None

    def token_ok() -> bool:
        return hmac.compare_digest(request.headers.get("X-API-Token", ""), seg["PORTAL_API_TOKEN"])

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "simulado": True, "modo_falha": app.config["MODO_FALHA"]})

    @app.get("/")
    def inicio():
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        erro = None
        if request.method == "POST":
            u, s = request.form.get("usuario", ""), request.form.get("senha", "")
            if hmac.compare_digest(u, seg["PORTAL_USUARIO"]) and hmac.compare_digest(s, seg["PORTAL_SENHA"]):
                session["logado"] = True
                return redirect(url_for("novo"))
            erro = "Usuário ou senha inválidos."
        return render_template("login.html", erro=erro), (401 if erro else 200)

    @app.get("/lancamentos/novo")
    def novo():
        if not session.get("logado"):
            return redirect(url_for("login"))
        return render_template("novo.html")

    @app.post("/lancamentos")
    def lancar():
        if not session.get("logado"):
            return redirect(url_for("login"))
        protocolo, criado = inserir(request.form, "selenium")
        return render_template("confirmacao.html", protocolo=protocolo, criado=criado, lote_id=request.form["lote_id"],
                               atraso=app.config["ATRASO_PROTOCOLO_MS"]), (201 if criado else 409)

    @app.get("/api/lancamentos/<lote_id>")
    def api_consultar(lote_id):
        if not token_ok():
            abort(401)
        f = api_falha()
        if f is not None:
            return f
        c = con()
        r = c.execute("SELECT * FROM lancamentos WHERE lote_id = ?", (lote_id,)).fetchone()
        c.close()
        if not r:
            return jsonify({"lote_id": lote_id, "encontrado": False}), 404
        return jsonify({**dict(r), "encontrado": True, "simulado": True})

    @app.post("/api/lancamentos")
    def api_lancar():
        if not token_ok():
            abort(401)
        f = api_falha()
        if f is not None:
            return f
        dados = request.get_json(silent=True) or {}
        if not all(k in dados for k in ("lote_id", "doador_id", "kg", "co2", "pontos")):
            return jsonify({"erro": "campos obrigatórios ausentes"}), 400
        protocolo, criado = inserir(dados, "api_contingencia")
        return jsonify({"protocolo": protocolo, "lote_id": dados["lote_id"], "simulado": True}), (201 if criado else 409)

    @app.get("/api/resumo")
    def api_resumo():
        if not token_ok():
            abort(401)
        c = con()
        n = c.execute("SELECT COUNT(*) FROM lancamentos").fetchone()[0]
        por_lote = [dict(r) for r in c.execute("SELECT lote_id, protocolo, meio FROM lancamentos ORDER BY id")]
        c.close()
        return jsonify({"total_lancamentos": n, "lancamentos": por_lote, "simulado": True})

    return app


if __name__ == "__main__":
    porta = int(os.environ.get("PORTAL_PORTA", "5050"))
    criar_app().run(host="127.0.0.1", port=porta, debug=False, use_reloader=False)
