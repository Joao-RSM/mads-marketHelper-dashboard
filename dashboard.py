import io
import base64
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

def obter_valor(dicionario, possiveis_chaves):
    # normalizar dic
    dic_limpo = {str(k).strip().lower(): v for k, v in dicionario.items()}
    for chave in possiveis_chaves:
        if chave in dic_limpo:
            return dic_limpo[chave]
    return ""

def filtrar_e_ordenar(compras, filtro_tipo, filtro_valor, ordem):
    if not compras:
        return []
    resultado = compras
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
    if ordem == "desc":
        resultado.reverse()
    return resultado

def gerar_grafico_evolucao(compras, produto):
    if not compras or not produto:
        return None
    compras_produto = [c for c in compras if produto.lower() in str(obter_valor(c, ['produto'])).lower()]
    if not compras_produto:
        return None
    try:
        dados_grafico = []
        for c in compras_produto:
            try:
                preco_bruto = str(obter_valor(c, ['preço', 'preco']))
                data_bruta = str(obter_valor(c, ['data_compra', 'data compra', 'data']))
                preco_limpo = preco_bruto.replace('€', '').replace('R$', '').replace(' ', '').replace(',', '.')
                preco = float(preco_limpo)
                data = data_bruta.strip()
                if data and preco > 0:
                    dados_grafico.append((data, preco))
            except Exception:
                continue
        if not dados_grafico:
            return None
        dados_grafico.sort(key=lambda x: x[0])
        datas = [d[0] for d in dados_grafico]
        precos = [d[1] for d in dados_grafico]
        plt.figure(figsize=(8, 4))
        plt.plot(datas, precos, marker='o', linestyle='-', color='#0d6efd', linewidth=2)
        plt.title(f'Evolução de Preço: {produto.title()}')
        plt.xlabel('Data da Compra')
        plt.ylabel('Preço (€)')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.xticks(rotation=45)
        plt.tight_layout()
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        img.seek(0)
        plt.close()
        return base64.b64encode(img.getvalue()).decode('utf-8')
    except Exception as e:
        print(f"Erro a gerar grafico: {str(e)}")
        return None

def gerar_graficos_comparativos(compras):
    # gera painel comparativo 2x2
    if not compras:
        return None, None, None, None

    vendas_loja = defaultdict(int) 
    lucro_loja = defaultdict(float) 
    vendas_categoria = defaultdict(float) 
    precos_produto = defaultdict(list)

    for c in compras:
        try:
            preco_str = str(obter_valor(c, ['preço', 'preco'])).replace('€', '').replace('R$', '').replace(' ', '').replace(',', '.')
            if not preco_str: continue
            preco = float(preco_str)

            loja = str(obter_valor(c, ['id loja', 'loja'])).strip()
            if not loja: loja = "Desconhecida"
            
            categoria = str(obter_valor(c, ['categoria', 'categoria loja'])).strip()
            if not categoria: categoria = "Diversos"
            
            produto = str(obter_valor(c, ['produto'])).strip()
            if not produto: continue

            vendas_loja[loja] += 1
            lucro_loja[loja] += preco
            vendas_categoria[categoria] += preco
            precos_produto[produto].append(preco)
        except Exception:
            continue

    def to_base64(fig):
        img = io.BytesIO()
        fig.savefig(img, format='png', bbox_inches='tight')
        img.seek(0)
        plt.close(fig)
        return base64.b64encode(img.getvalue()).decode('utf-8')

    # 1. vendas por loja
    g_vendas = None
    if vendas_loja:
        fig1 = plt.figure(figsize=(6, 4))
        plt.bar(list(vendas_loja.keys()), list(vendas_loja.values()), color='#1f77b4')
        plt.title('Vendas por Loja (Qtd)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        g_vendas = to_base64(fig1)

    # 2. lucro por loja
    g_lucro = None
    if lucro_loja:
        fig2 = plt.figure(figsize=(6, 4))
        plt.bar(list(lucro_loja.keys()), list(lucro_loja.values()), color='#2ca02c')
        plt.title('Lucro por Loja (€)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        g_lucro = to_base64(fig2)

    # 3. vendas por categoria
    g_cat = None
    if vendas_categoria:
        fig3 = plt.figure(figsize=(6, 4))
        plt.pie(list(vendas_categoria.values()), labels=list(vendas_categoria.keys()), autopct='%1.1f%%', startangle=140)
        plt.title('Vendas por Categoria')
        plt.tight_layout()
        g_cat = to_base64(fig3)

    # 4. preco medio
    g_preco = None
    if precos_produto:
        fig4 = plt.figure(figsize=(8, 4))
        medias = [(p, sum(precos)/len(precos)) for p, precos in precos_produto.items()]
        medias.sort(key=lambda x: x[1], reverse=True)
        medias = medias[:10]
        plt.bar([x[0] for x in medias], [x[1] for x in medias], color='#ff7f0e')
        plt.title('Preço Médio por Produto (€)')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        g_preco = to_base64(fig4)

    return g_vendas, g_lucro, g_cat, g_preco
