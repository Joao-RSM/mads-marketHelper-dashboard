import io
import base64
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

def obter_valor(dicionario, possiveis_chaves):
    # limpa as chaves manhosas do excel
    dic_limpo = {str(k).strip().lower(): v for k, v in dicionario.items()}
    for chave in possiveis_chaves:
        if chave in dic_limpo:
            return dic_limpo[chave]
    return ""

def filtrar_e_ordenar(compras, filtro_tipo, filtro_valor, ordem):
    # filtros do dashboard de pesquisa
    if not compras: return []
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
    # grafico da pagina de item simples
    if not compras or not produto: return None
    compras_produto = [c for c in compras if produto.lower() in str(obter_valor(c, ['produto'])).lower()]
    if not compras_produto: return None
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
        if not dados_grafico: return None
        
        # ordena datas
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

def gerar_graficos_comparativos(compras, lojas):
    # motor principal do dashboard novo
    if not compras and not lojas:
        return None, None, None, None, None

    mapa_lojas = {}
    mapa_categorias = {}
    dist_lojas_cat = defaultdict(int)

    # cruzar ids com nomes reais
    if lojas:
        for loja in lojas:
            id_l = str(obter_valor(loja, ['id loja', 'id', 'loja'])).strip()
            nome_l = str(obter_valor(loja, ['nome', 'loja'])).strip()
            cat_l = str(obter_valor(loja, ['especialidade', 'categoria'])).strip()
            
            if not id_l: continue
            if not nome_l: nome_l = f"Loja {id_l}"
            if not cat_l: cat_l = "Diversos"
            
            mapa_lojas[id_l] = nome_l
            mapa_categorias[id_l] = cat_l
            dist_lojas_cat[cat_l] += 1

    vendas_loja = defaultdict(int) 
    lucro_loja = defaultdict(float) 
    vendas_categoria = defaultdict(float) 
    precos_produto = defaultdict(list)

    if compras:
        for c in compras:
            try:
                preco_bruto = str(obter_valor(c, ['preço', 'preco']))
                
                # saltar lixo e datas mal formatadas do excel
                if "-" in preco_bruto and ":" in preco_bruto: continue
                    
                preco_str = preco_bruto.replace('€', '').replace('R$', '').replace(' ', '').replace(',', '.')
                if not preco_str: continue
                preco = float(preco_str)

                id_l = str(obter_valor(c, ['id loja', 'loja'])).strip()
                
                # vai buscar os nomes ao dicionario
                nome_loja = mapa_lojas.get(id_l, f"Loja {id_l}")
                categoria = mapa_categorias.get(id_l, "Diversos")
                
                produto = str(obter_valor(c, ['produto'])).strip()
                if not produto: continue

                # soma os totais
                vendas_loja[nome_loja] += 1
                lucro_loja[nome_loja] += preco
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

    # 1. vendas por loja (barras horizontais azul)
    g_vendas = None
    if vendas_loja:
        # ordenar para ficar a maior em cima
        lojas_ord_v = sorted(vendas_loja.items(), key=lambda x: x[1])
        n_lojas = [x[0] for x in lojas_ord_v]
        v_lojas = [x[1] for x in lojas_ord_v]
        
        fig1 = plt.figure(figsize=(6, 5))
        ax1 = fig1.add_subplot(111)
        ax1.barh(n_lojas, v_lojas, color='#4682b4')
        ax1.set_title('QUANTIDADE DE COMPRAS POR LOJA', fontsize=10, fontweight='bold', loc='left', pad=15)
        ax1.set_xlabel('Número de Compras')
        
        # formatacao limpa igual a imagem
        ax1.grid(axis='x', color='#eeeeee', linestyle='-')
        ax1.set_axisbelow(True)
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        ax1.spines['left'].set_visible(False)
        
        plt.tight_layout()
        g_vendas = to_base64(fig1)

    # 2. lucro por loja (barras horizontais laranja)
    g_lucro = None
    if lucro_loja:
        lojas_ord_l = sorted(lucro_loja.items(), key=lambda x: x[1])
        n_lojas_l = [x[0] for x in lojas_ord_l]
        v_lojas_l = [x[1] for x in lojas_ord_l]
        
        fig2 = plt.figure(figsize=(6, 5))
        ax2 = fig2.add_subplot(111)
        ax2.barh(n_lojas_l, v_lojas_l, color='#ff7f50')
        ax2.set_title('VOLUME DE VENDAS POR LOJA', fontsize=10, fontweight='bold', loc='left', pad=15)
        ax2.set_xlabel('Valor (€)')
        
        ax2.grid(axis='x', color='#eeeeee', linestyle='-')
        ax2.set_axisbelow(True)
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.spines['left'].set_visible(False)
        
        plt.tight_layout()
        g_lucro = to_base64(fig2)

    # 3. vendas por categoria (tarte)
    g_cat = None
    if vendas_categoria:
        fig3 = plt.figure(figsize=(6, 4))
        plt.pie(list(vendas_categoria.values()), labels=list(vendas_categoria.keys()), autopct='%1.1f%%', startangle=140)
        plt.title('Volume de Vendas por Categoria')
        plt.tight_layout()
        g_cat = to_base64(fig3)

    # 4. preco medio (barras verticais, max 10)
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
        
    # 5. distribuicao lojas (tarte)
    g_dist_cat = None
    if dist_lojas_cat:
        fig5 = plt.figure(figsize=(6, 4))
        plt.pie(list(dist_lojas_cat.values()), labels=list(dist_lojas_cat.keys()), autopct='%1.1f%%', startangle=90, colors=plt.cm.Set3.colors)
        plt.title('Distribuição de Lojas por Especialidade')
        plt.tight_layout()
        g_dist_cat = to_base64(fig5)

    return g_vendas, g_lucro, g_cat, g_preco, g_dist_cat
