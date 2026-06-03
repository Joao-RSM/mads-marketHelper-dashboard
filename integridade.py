def executar_auditoria_cloud(dados_totais):
    erros = []
    
    utilizadores = dados_totais.get("Utilizadores", [])
    lojas = dados_totais.get("Lojas", [])
    compras = dados_totais.get("Compras", [])
    categorias = ["Padaria", "Talho", "Peixaria", "Supermercado"]

    nifs_validos = set()
    ids_lojas_validas = set()

    for idx, user in enumerate(utilizadores, start=2):
        nif = str(user.get("NIF", "")).strip()
        nifs_validos.add(nif)
        if not nif or len(nif) != 9 or not nif.isdigit():
            erros.append({"tabela": "Utilizadores", "linha": idx, "descricao": f"NIF inválido: {nif}", "tipo": "Formato"})
        
        genero = str(user.get("Sexo", "")).strip().upper()
        if genero not in ["M", "F", "O"]:
            erros.append({"tabela": "Utilizadores", "linha": idx, "descricao": f"Género inválido: {genero}", "tipo": "Domínio"})

    for idx, loja in enumerate(lojas, start=2):
        id_loja = str(loja.get("ID Loja", "")).strip()
        ids_lojas_validas.add(id_loja)
        
        especialidade = str(loja.get("Especialidade", "")).strip()
        if especialidade not in categorias:
            erros.append({"tabela": "Lojas", "linha": idx, "descricao": f"Especialidade fora da lista fechada: {especialidade}", "tipo": "Domínio"})
            
        nome = str(loja.get("Nome", "")).strip()
        loc = str(loja.get("Localização", "")).strip()
        if not nome or not loc:
            erros.append({"tabela": "Lojas", "linha": idx, "descricao": "Nome ou Localização vazios.", "tipo": "Nulo"})

    for idx, compra in enumerate(compras, start=2):
        nif_compra = str(compra.get("NIF Utilizador", "")).strip()
        if nif_compra not in nifs_validos:
            erros.append({"tabela": "Compras", "linha": idx, "descricao": f"NIF {nif_compra} órfão (não existe em Utilizadores).", "tipo": "Chave Estrangeira"})
        
        id_loja_compra = str(compra.get("ID Loja", "")).strip()
        if id_loja_compra not in ids_lojas_validas:
            erros.append({"tabela": "Compras", "linha": idx, "descricao": f"Loja {id_loja_compra} órfã (não existe em Lojas).", "tipo": "Chave Estrangeira"})

        try:
            preco = float(str(compra.get("Preço", "0")).replace(',', '.'))
            if preco <= 0:
                erros.append({"tabela": "Compras", "linha": idx, "descricao": f"Preço deve ser > 0. Valor: {preco}", "tipo": "Regra de Negócio"})
        except:
            erros.append({"tabela": "Compras", "linha": idx, "descricao": "Preço não numérico.", "tipo": "Tipo Dado"})
            
        produto = str(compra.get("Produto", ""))
        if produto != produto.lower():
            erros.append({"tabela": "Compras", "linha": idx, "descricao": f"O produto '{produto}' não está em minúsculas.", "tipo": "Regra de Negócio"})

    return erros
