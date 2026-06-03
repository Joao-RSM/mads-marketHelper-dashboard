import os
import json
from pathlib import Path
from flask import Flask, request, render_template, redirect, url_for, session, flash, jsonify
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials

import integridade
import mapa
import dashboard

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "chave_secreta_provisoria_grupo2")

load_dotenv()
is_production = os.getenv("isProduction", "false").lower() == "true"

if is_production:
    service_file_path = "/etc/secrets/mads-markethelper-credentials.json"
    chaves_file_path = "/etc/secrets/chave.json"
else:
    service_file_path = str(Path(__file__).resolve().parent / "secrets/mads-markethelper-credentials.json")
    chaves_file_path = str(Path(__file__).resolve().parent / "secrets/chave.json")

try:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(service_file_path, scope)
    gc = gspread.authorize(creds)
    sheet = gc.open("Base de Dados - Utilizadores - Grupo 2")
except Exception as e:
    print(f"Erro na conexao com Google Sheets: {e}")
    sheet = None

try:
    with open(chaves_file_path, "r", encoding="utf-8") as f:
        KEYS = json.load(f)
except Exception:
    KEYS = {
        "dados_privados": "chave_dados_grupo2",
        "integridade_admin": "chave_integridade_grupo2"
    }

def obter_linhas_cloud(nome_aba):
    try:
        if sheet:
            worksheet = sheet.worksheet(nome_aba)
            return worksheet.get_all_records()
    except Exception:
        return []
    return []

@app.route("/", methods=["GET"])
def index():
    lojas = obter_linhas_cloud("Lojas")
    mapa_html = mapa.gerar_mapa_lojas(lojas)
    return render_template("landing.html", lojas=lojas, mapa_html=mapa_html)

@app.route("/add_compra", methods=["POST"])
def add_compra():
    nif = request.form.get("nif", "").strip()
    produto = request.form.get("produto", "").strip().lower()
    preco = request.form.get("preco", "").strip()
    id_loja = request.form.get("id_loja", "").strip()
    data_compra = request.form.get("data_compra", "").strip()
    tipo_pagamento = request.form.get("tipo_pagamento", "").strip()

    try:
        if sheet:
            worksheet_compras = sheet.worksheet("Compras")
            nova_linha = [
                str(len(worksheet_compras.get_all_values())),
                nif,
                produto,
                float(preco),
                id_loja,
                data_compra,
                tipo_pagamento if tipo_pagamento else "Não especificado"
            ]
            worksheet_compras.append_row(nova_linha)
            flash("Compra registada com sucesso na Cloud!", "success")
    except Exception as e:
        flash(f"Falha ao registar compra: {str(e)}", "error")

    return redirect(url_for("index"))

@app.route("/login", methods=["GET", "POST"])
def login():
    destino = request.args.get("destino", "dashboard")
    
    if request.method == "POST":
        chave_inserida = request.form.get("chave", "").strip()
        destino_post = request.form.get("destino", "dashboard")
        
        if destino_post == "integridade":
            if chave_inserida == KEYS.get("integridade_admin"):
                session["integridade_admin"] = True
                return redirect(url_for("integridade_route"))
        else:
            if chave_inserida == KEYS.get("dados_privados"):
                session["dados_privados"] = True
                return redirect(url_for("dashboard_route"))
        
        flash("Chave de acesso inválida.", "error")
        return render_template("login.html", destino=destino_post)

    return render_template("login.html", destino=destino)

@app.route("/dashboard", methods=["GET"])
def dashboard_route():
    if not session.get("dados_privados"):
        return redirect(url_for("login", destino="dashboard"))
        
    compras = obter_linhas_cloud("Compras")
    
    filtro_tipo = request.args.get("filtro_tipo", "")
    filtro_valor = request.args.get("filtro_valor", "")
    ordem = request.args.get("ordem", "asc")
    
    compras_filtradas = dashboard.filtrar_e_ordenar(compras, filtro_tipo, filtro_valor, ordem)
    
    grafico_produto = request.args.get("grafico_produto", "").strip().lower()
    grafico_base64 = None
    if grafico_produto:
        grafico_base64 = dashboard.gerar_grafico_evolucao(compras, grafico_produto)

    session["compras_filtradas_view"] = compras_filtradas

    return render_template(
        "dashboard.html", 
        compras=compras_filtradas, 
        filtro_tipo=filtro_tipo, 
        filtro_valor=filtro_valor, 
        ordem=ordem,
        grafico_produto=grafico_produto,
        grafico_base64=grafico_base64
    )

@app.route("/exportar_json", methods=["GET"])
def exportar_json():
    if not session.get("dados_privados"):
        return jsonify({"erro": "Acesso nao autorizado"}), 401
    
    dados_view = session.get("compras_filtradas_view", [])
    return jsonify(dados_view)

@app.route("/integridade", methods=["GET"])
def integridade_route():
    if not session.get("integridade_admin"):
        return redirect(url_for("login", destino="integridade"))
        
    dados_totais = {
        "Utilizadores": obter_linhas_cloud("Utilizadores"),
        "Lojas": obter_linhas_cloud("Lojas"),
        "Compras": obter_linhas_cloud("Compras"),
        "categoriasLojas": obter_linhas_cloud("categoriasLojas")
    }
    
    erros_detetados = integridade.executar_auditoria_cloud(dados_totais)
    total_linhas = sum(len(v) for v in dados_totais.values())

    return render_template("integridade.html", erros=erros_detetados, total_linhas=total_linhas)

@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    flash("Sessão encerrada.", "success")
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=not is_production)
