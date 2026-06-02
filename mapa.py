import io
import base64
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

def filtrar_e_ordenar(compras, filtro_tipo, filtro_valor, ordem):
    if not compras:
        return []
        
    resultado = compras
    
    if filtro_tipo and filtro_valor:
        termo = str(filtro_valor).lower()
        if filtro_tipo == "produto":
            resultado = [c for c in resultado if termo in str(c.get('Produto', '')).lower()]
        elif filtro_tipo == "loja":
            resultado = [c for c in resultado if termo in str(c.get('ID Loja', '')).lower()]
        elif filtro_tipo == "nif":
            resultado = [c for c in resultado if termo in str(c.get('NIF Utilizador', '')).lower()]
        elif filtro_tipo == "pagamento":
            resultado = [c for c in resultado if termo == str(c.get('Tipo Pagamento', '')).lower()]

    if ordem == "desc":
        resultado.reverse()
        
    return resultado

def gerar_grafico_evolucao(compras, produto):
    if not compras or not produto:
        return None
        
    compras_produto = [c for c in compras if produto.lower() in str(c.get('Produto', '')).lower()]
    if not compras_produto:
        return None
        
    try:
        dados_grafico = []
        for c in compras_produto:
            try:
                preco = float(str(c.get('Preço', '0')).replace(',', '.'))
                data = str(c.get('Data_compra', ''))
                if data and preco > 0:
                    dados_grafico.append((data, preco))
            except:
                continue
                
        if not dados_grafico:
            return None
            
        dados_grafico.sort(key=lambda x: x[0])
        datas = [d[0] for d in dados_grafico]
        precos = [d[1] for d in dados_grafico]

        plt.figure(figsize=(8, 4))
        plt.plot(datas, precos, marker='o', linestyle='-', color='b')
        plt.title(f'Evolução de Preço: {produto.title()}')
        plt.xlabel('Data')
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
        return None
