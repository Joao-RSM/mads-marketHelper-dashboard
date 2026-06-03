import os
import json
from pathlib import Path
from flask import Flask, request, render_template, redirect, url_for, session, flash, jsonify, render_template_string
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

@app.route("/login", methods=["GET", "POST"])
def login():
    destino = request.args.get("destino", "dashboard")
    
    if request.method == "POST":
        chave_inserida = request.form.get("chave", "").strip()
        destino_post = request.form.get("destino", "dashboard")
        
        # Admin integridade
        if chave_inserida == KEYS.get("integridade_admin"):
            session["integridade_admin"] = True
            return redirect(url_for("integridade_route"))
            
        # Acesso geral dashboard
        if chave_inserida == KEYS.get("dados_privados"):
            session["dados_privados"] = True
            return redirect(url_for("dashboard_route"))
            
        # Acesso por item especifico
        for nome_chave, password in KEYS.items():
            if str(nome_chave).startswith("item_") and chave_inserida == str(password):
                session["dados_privados"] = True
                session["item_especifico"] = str(nome_chave).replace("item_", "")
                return redirect(url_for("item_simples_route"))
                
        # Acesso view tabelas
        if chave_inserida == KEYS.get("ver_users_123"):
            session["tabela_permitida"] = "Utilizadores"
            return redirect(url_for("visualizar_tabela", nome_tabela="Utilizadores"))
            
        if chave_inserida == KEYS.get("ver_compras_123"):
            session["tabela_permitida"] = "Compras"
            return redirect(url_for("visualizar_tabela", nome_tabela="Compras"))
            
        if chave_inserida == KEYS.get("ver_cat_123"):
            session["tabela_permitida"] = "categoriasLojas"
            return redirect(url_for("visualizar_tabela", nome_tabela="categoriasLojas"))
        
        # Falha autenticacao
        flash("Chave de acesso inválida.", "error")
        return redirect(url_for("index"))

    return render_template("login.html", destino=destino)

@app.route("/item_simples", methods=["GET"])
def item_simples_route():
    # Validar sessao
    if not session.get("dados_privados") or not session.get("item_especifico"):
        return redirect(url_for("login"))

    item = session.get("item_especifico")
    compras = obter_linhas_cloud("Compras")
    
    grafico_base64 = dashboard.gerar_grafico_evolucao(compras, item)
    
    # Template inline renderizado via string
    html_simples = """
    {% extends 'base.html' %}
    {% block title %}Análise: {{ item.title() }}{% endblock %}
    {% block content %}
    <div class="row justify-content-center mb-4">
        <div class="col-md-8 text-center">
            <div class="card shadow-sm mt-5">
                <div class="card-header bg-dark text-white fw-bold fs-5">
                    Variação de Preço: {{ item.title() }}
                </div>
                <div class="card-body p-5">
                    {% if grafico_base64 %}
                        <img src="data:image/png;base64,{{ grafico_base64 }}" class="img-fluid rounded mb-4 shadow" alt="Gráfico de {{ item }}">
                    {% else %}
                        <div class="alert alert-warning">Ainda não há dados suficientes registados na Cloud para desenhar um gráfico de "{{ item }}".</div>
                    {% endif %}
                    <br><br>
                    <a href="/logout" class="btn btn-outline-danger fw-bold px-4">Voltar</a>
                </div>
            </div>
        </div>
    </div>
    {% endblock %}
    """
    return render_template_string(html_simples, item=item, grafico_base64=grafico_base64)

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

@app.route("/tabela/<nome_tabela>", methods=["GET"])
def visualizar_tabela(nome_tabela):
    # Validar autorizacao para a tabela especifica
    if session.get("tabela_permitida") != nome_tabela:
        return redirect(url_for("index"))
        
    dados_tabela = obter_linhas_cloud(nome_tabela)
        
    return render_template("ver_tabela.html", titulo=nome_tabela, dados=dados_tabela)

@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=not is_production)
