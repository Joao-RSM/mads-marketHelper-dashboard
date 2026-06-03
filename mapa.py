import folium

def gerar_mapa_lojas(lojas):
    if not lojas:
        return "<div class='text-center p-4 text-muted'>Nenhuma loja para mostrar no mapa.</div>"
    
    # Cria o mapa centrado em Portugal com um nível de zoom ideal
    mapa = folium.Map(location=[39.5, -8.0], zoom_start=6)
    
    # Percorre todas as lojas do teu Excel
    for loja in lojas:
        try:
            # Vai buscar a Lat e Lon e converte a vírgula para ponto automaticamente
            lat_str = str(loja.get('Lat', '')).strip().replace(',', '.')
            lon_str = str(loja.get('Lon', '')).strip().replace(',', '.')
            
            # Se a loja não tiver coordenadas preenchidas, salta para a próxima
            if not lat_str or not lon_str:
                continue
                
            lat = float(lat_str)
            lon = float(lon_str)
            
            nome = loja.get('Nome', 'Loja Desconhecida')
            especialidade = loja.get('Especialidade', '')
            localizacao = loja.get('Localização', '')
            
            # Constrói o balão de informação que aparece quando clicas no pino
            popup_html = f"<b>{nome}</b><br><span style='color: gray;'>{especialidade}</span><br><i>{localizacao}</i>"
            
            # Espeta o pino azul no mapa
            folium.Marker(
                [lat, lon], 
                popup=popup_html, 
                tooltip=nome,
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(mapa)
            
        except ValueError:
            # Se houver algum erro de formatação numa linha, o código ignora e não crasha o site
            continue
            
    # Transforma o mapa em código HTML para o teu site conseguir exibi-lo
    return mapa._repr_html_()
