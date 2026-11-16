# app.py - backend do painel administrativo (Flask)
# Liga o painel (HTML no navegador) ao banco MySQL.
# Uso: py -3.11 app.py   e abrir http://127.0.0.1:5000

import os
import subprocess
import sys
from functools import wraps

from flask import Flask, jsonify, redirect, request, send_from_directory, session
from mysql.connector import Error as ErroBanco
from werkzeug.security import check_password_hash

import banco
import config

PASTA = os.path.dirname(os.path.abspath(__file__))
PASTA_PAINEL = os.path.join(PASTA, "painel")
PORTA = getattr(config, "PORTA_PAINEL", 5000)  # pode ser trocada no config.py
PERFIS = ["aluno", "professor", "funcionario", "visitante"]

app = Flask(__name__, static_folder=None)
app.secret_key = os.urandom(24)  # muda a cada execução: ao reiniciar o app, é preciso entrar de novo
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")


def exige_login(funcao):
    """Bloqueia a rota para quem não entrou com usuário e senha."""
    @wraps(funcao)
    def protegida(*args, **kwargs):
        if not session.get("admin"):
            if request.path.startswith("/api/"):
                return jsonify(erro="Sessão expirada. Entre novamente."), 401
            return redirect("/login")
        return funcao(*args, **kwargs)
    return protegida


def servir_pagina(nome):
    """Entrega um arquivo da pasta painel. Se ele não estiver lá, explica exatamente o que falta."""
    caminho = os.path.join(PASTA_PAINEL, nome)
    if not os.path.isfile(caminho):
        return (f"Arquivo não encontrado: {caminho}\n\n"
                f"Coloque o arquivo '{nome}' dentro da pasta 'painel' (ao lado do app.py) e atualize a página."), 404, \
               {"Content-Type": "text/plain; charset=utf-8"}
    return send_from_directory(PASTA_PAINEL, nome)


def formatar(data):
    return data.strftime("%d/%m/%Y %H:%M:%S") if data else ""


@app.errorhandler(ErroBanco)
def erro_do_banco(erro):
    print(f"[ERRO MySQL] {erro}")
    return jsonify(erro="Não foi possível acessar o banco de dados."), 500


# ----------------------------- páginas -----------------------------

@app.get("/login")
def pagina_login():
    return servir_pagina("login.html")


@app.post("/login")
def entrar():
    usuario = request.form.get("usuario", "").strip()
    senha = request.form.get("senha", "")
    try:
        admin = banco.obter_admin(usuario)
    except ErroBanco as erro:
        print(f"[ERRO MySQL] {erro}")
        return redirect("/login?erro=banco")
    # A senha digitada é comparada com o hash guardado no banco
    if admin and check_password_hash(admin["senha_hash"], senha):
        session.clear()
        session["admin"] = admin["usuario"]
        return redirect("/")
    return redirect("/login?erro=1")


@app.get("/sair")
def sair():
    session.clear()
    return redirect("/login")


@app.get("/")
@exige_login
def painel():
    return servir_pagina("painel.html")


# ------------------------------ API --------------------------------

@app.get("/api/resumo")
@exige_login
def api_resumo():
    dados = banco.resumo()
    ultimo = banco.listar_acessos(1)
    dados["ultimo"] = ({"nome": ultimo[0]["nome"] or "Desconhecido", "resultado": ultimo[0]["resultado"],
                        "hora": formatar(ultimo[0]["data_hora"])} if ultimo else None)
    return jsonify(dados)


@app.get("/api/usuarios")
@exige_login
def api_usuarios():
    return jsonify([{"id": u["id"], "nome": u["nome"], "perfil": u["perfil"], "ativo": bool(u["ativo"]),
                     "amostras": int(u["amostras"]), "criado_em": formatar(u["criado_em"])}
                    for u in banco.listar_usuarios()])


@app.get("/api/acessos")
@exige_login
def api_acessos():
    limite = min(max(request.args.get("limite", 50, type=int), 1), 500)
    return jsonify([{"id": a["id"], "hora": formatar(a["data_hora"]), "nome": a["nome"] or "Desconhecido",
                     "resultado": a["resultado"]} for a in banco.listar_acessos(limite)])


@app.post("/api/usuarios/<int:usuario_id>/ativo")
@exige_login
def api_ativo(usuario_id):
    dados = request.get_json(silent=True) or {}
    banco.alterar_ativo(usuario_id, bool(dados.get("ativo")))
    return jsonify(ok=True)


@app.post("/api/usuarios/<int:usuario_id>/perfil")
@exige_login
def api_perfil(usuario_id):
    perfil = (request.get_json(silent=True) or {}).get("perfil")
    if perfil not in PERFIS:
        return jsonify(erro="Perfil inválido."), 400
    banco.alterar_perfil(usuario_id, perfil)
    return jsonify(ok=True)


@app.delete("/api/usuarios/<int:usuario_id>")
@exige_login
def api_excluir(usuario_id):
    banco.excluir_usuario(usuario_id)
    return jsonify(ok=True)


@app.post("/api/cadastrar")
@exige_login
def api_cadastrar():
    """Abre a câmera (neste computador) para cadastrar o rosto da pessoa."""
    dados = request.get_json(silent=True) or {}
    nome = (dados.get("nome") or "").strip()
    perfil = dados.get("perfil")
    if not nome or len(nome) > 120 or perfil not in PERFIS:
        return jsonify(erro="Informe o nome e escolha um perfil válido."), 400
    subprocess.Popen([sys.executable, os.path.join(PASTA, "cadastrar.py"), nome, perfil], cwd=PASTA,
                     creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return jsonify(ok=True, mensagem="Olhe para a câmera e aperte ESPAÇO 5 vezes. O usuário aparece na lista ao terminar.")


if __name__ == "__main__":
    # host 127.0.0.1: só este computador acessa o painel
    print(f"Painel no ar em http://127.0.0.1:{PORTA}")
    app.run(host="127.0.0.1", port=PORTA, debug=False)
