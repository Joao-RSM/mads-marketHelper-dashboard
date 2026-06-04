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
        "dados_privados": "dados_privados",
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

@app.route("/login", methods=["POST"])
def login():
    chave_inserida = request.form.get("chave", "").strip()
    
    # enter vazio -> index
    if not chave_inserida:
        return redirect(url_for("index"))
        
    # admin integridade
    if chave_inserida == KEYS.get("integridade_admin"):
        session["integridade_admin"] = True
        return redirect(url_for("integridade_route"))
        
    # painel principal (4 graficos)
    if chave_inserida == KEYS.get("dados_privados"):
        session["dados_privados"] = True
        return redirect(url_for("dados_route"))
        
    # view tabelas
    if chave_inserida == KEYS.get("ver_utilizadores"):
        session["tabela_permitida"] = "Utilizadores"
        return redirect(url_for("visualizar_tabela", nome_tabela="Utilizadores"))
        
    if chave_inserida == KEYS.get("ver_compras"):
        session["tabela_permitida"] = "Compras"
        return redirect(url_for("visualizar_tabela", nome_tabela="Compras"))
        
    if chave_inserida == KEYS.get("ver_categorias"):
        session["tabela_permitida"] = "categoriasLojas"
        return redirect(url_for("visualizar_tabela", nome_tabela="categoriasLojas"))
        
    # acesso por item especifico (se ainda quiseres usar os graficos de frango, carne, etc)
    for nome_chave, password in KEYS.items():
        if str(nome_chave).startswith("item_") and chave_inserida == str(password):
            session["dados_privados"] = True
            session["item_especifico"] = str(nome_chave).replace("item_", "")
            return redirect(url_for("item_simples_route"))
            
    # falhou autenticacao
    flash("Chave de acesso inválida.", "error")
    return redirect(url_for("index"))

@app.route("/item_simples", methods=["GET"])
def item_simples_route():
    # validar sessao
    if not session.get("dados_privados") or not session.get("item_especifico"):
        return redirect(url_for("index"))

    item = session.get("item_especifico")
    compras = obter_linhas_cloud("Compras")
    
    grafico_base64 = dashboard.gerar_grafico_evolucao(compras, item)
    
    # render inline
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

@app.route("/dados", methods=["GET"])
def dados_route():
    if not session.get("dados_privados"):
        return redirect(url_for("index"))
        
    compras = obter_linhas_cloud("Compras")
    lojas = obter_linhas_cloud("Lojas") # essencial para cruzar os IDs com os Nomes
    
    g_vendas, g_lucro, g_cat, g_preco, g_dist_cat = dashboard.gerar_graficos_comparativos(compras, lojas)
    
    return render_template("dados.html", g_vendas=g_vendas, g_lucro=g_lucro, g_cat=g_cat, g_preco=g_preco, g_dist_cat=g_dist_cat)
    
    return render_template("dados.html", g_vendas=g_vendas, g_lucro=g_lucro, g_cat=g_cat, g_preco=g_preco)

@app.route("/exportar_json", methods=["GET"])
def exportar_json():
    if not session.get("dados_privados"):
        return jsonify({"erro": "Acesso nao autorizado"}), 401
    
    # envia todas as compras
    compras = obter_linhas_cloud("Compras")
    return jsonify(compras)

@app.route("/integridade", methods=["GET"])
def integridade_route():
    if not session.get("integridade_admin"):
        return redirect(url_for("index"))
        
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
    # validar autorizacao para a tabela especifica
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
