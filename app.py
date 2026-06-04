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
        
    # falhou autenticacao
    flash("Chave de acesso inválida.", "error")
    return redirect(url_for("index"))
