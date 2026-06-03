import io
import base64
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

def obter_valor(dicionario, possiveis_chaves):
    # normalizar chaves do dic (tira espacos e mete em minusculas)
    dic_limpo = {str(k).strip().lower(): v for k, v in dicionario.items()}
    for chave in possiveis_chaves:
        if chave in dic_limpo:
            return dic_limpo[chave]
    return ""

def filtrar_e_ordenar(compras, filtro_tipo, filtro_valor, ordem):
    if not compras:
        return []
        
    resultado = compras
    
    # aplicar filtros
    if filtro_tipo and filtro_valor:
        termo = str(filtro_valor).lower()
        if filtro_tipo == "produto":
            resultado = [c for c in resultado if termo in str(obter_valor(c, ['produto'])).lower()]
        elif filtro_tipo == "loja":
            resultado = [c for c in resultado if termo in str(obter_valor(c, ['id loja', 'loja'])).lower()]
        elif filtro_tipo == "nif":
            resultado = [c for c in resultado if termo in str(obter_valor(c, ['nif utilizador', 'nif'])).lower()]
        elif filtro_tipo == "pagamento":
            resultado = [c for c in resultado if termo == str(obter_valor(c, ['tipo pagamento', 'pagamento'])).lower()]

    # ordenacao
    if ordem == "desc":
        resultado.reverse()
        
    return resultado

def gerar_grafico_evolucao(compras, produto):
    if not compras or not produto:
        return None
        
    # filtra so os dados deste produto
    compras_produto = [c for c in compras if produto.lower() in str(obter_valor(c, ['produto'])).lower()]
    if not compras_produto:
        return None
        
    try:
        dados_grafico = []
        for c in compras_produto:
            try:
                # apanhar colunas com nomes parecidos
                preco_bruto = str(obter_valor(c, ['preço', 'preco']))
                data_bruta = str(obter_valor(c, ['data_compra', 'data compra', 'data']))
                
                # limpar formatacao do preco (euros, espacos, virgulas)
                preco_limpo = preco_bruto.replace('€', '').replace('R$', '').replace(' ', '').replace(',', '.')
                preco = float(preco_limpo)
                data = data_bruta.strip()
                
                if data and preco > 0:
                    dados_grafico.append((data, preco))
            except Exception:
                continue
                
        if not dados_grafico:
            return None
            
        # ordenar por data (crescente)
        dados_grafico.sort(key=lambda x: x[0])
        datas = [d[0] for d in dados_grafico]
        precos = [d[1] for d in dados_grafico]

        # config e render do grafico
        plt.figure(figsize=(8, 4))
        plt.plot(datas, precos, marker='o', linestyle='-', color='#0d6efd', linewidth=2)
        plt.title(f'Evolução de Preço: {produto.title()}')
        plt.xlabel('Data da Compra')
        plt.ylabel('Preço (€)')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.xticks(rotation=45)
        plt.tight_layout()

        # converter imagem p/ html
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        img.seek(0)
        plt.close()
        
        return base64.b64encode(img.getvalue()).decode('utf-8')
    except Exception as e:
        print(f"Erro a gerar grafico: {str(e)}")
        return None
