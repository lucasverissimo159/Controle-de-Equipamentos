"""
Helper de cores para gráficos
"""

def get_rainbow_colors(n):
    """
    Retorna n cores usando paleta expandida + gradientes
    
    Paleta base de 15 cores:
    Azul-marinho, Vermelho, Amarelo, Laranja, Azul-claro, Violeta, 
    Verde, Marrom, Cinza, Rosa, Magenta, Lilás, Ciano, Esmeralda, Dourado
    
    Se n > 15, usa gradientes entre as cores base
    """
    # Cores base RGB para Plotly
    base_colors_rgb = [
        'rgb(0, 0, 128)',      # Azul-marinho
        'rgb(255, 0, 0)',      # Vermelho
        'rgb(255, 255, 0)',    # Amarelo
        'rgb(255, 165, 0)',    # Laranja
        'rgb(135, 206, 250)',  # Azul-claro
        'rgb(138, 43, 226)',   # Violeta
        'rgb(0, 128, 0)',      # Verde
        'rgb(139, 69, 19)',    # Marrom
        'rgb(128, 128, 128)',  # Cinza
        'rgb(255, 192, 203)',  # Rosa
        'rgb(255, 0, 255)',    # Magenta
        'rgb(200, 162, 200)',  # Lilás
        'rgb(0, 255, 255)',    # Ciano
        'rgb(80, 200, 120)',   # Esmeralda
        'rgb(255, 215, 0)',    # Dourado
    ]
    
    if n <= 15:
        return base_colors_rgb[:n]
    
    # Se precisar de mais cores, criar gradientes
    colors = list(base_colors_rgb)
    
    # Extrair valores RGB das cores base
    def parse_rgb(rgb_str):
        # "rgb(r, g, b)" -> (r, g, b)
        vals = rgb_str.replace('rgb(', '').replace(')', '').split(',')
        return tuple(int(v.strip()) for v in vals)
    
    base_rgb_tuples = [parse_rgb(c) for c in base_colors_rgb]
    
    # Gerar cores intermediárias (gradientes)
    while len(colors) < n:
        for i in range(len(base_rgb_tuples) - 1):
            if len(colors) >= n:
                break
            # Cor intermediária entre i e i+1
            r1, g1, b1 = base_rgb_tuples[i]
            r2, g2, b2 = base_rgb_tuples[i + 1]
            
            r_mid = (r1 + r2) // 2
            g_mid = (g1 + g2) // 2
            b_mid = (b1 + b2) // 2
            
            colors.append(f'rgb({r_mid}, {g_mid}, {b_mid})')
    
    return colors[:n]


def get_rainbow_colors_hex(n):
    """
    Retorna n cores em formato HEX para Matplotlib
    """
    # Cores base HEX
    base_colors_hex = [
        '#000080',  # Azul-marinho
        '#FF0000',  # Vermelho
        '#FFFF00',  # Amarelo
        '#FFA500',  # Laranja
        '#87CEFA',  # Azul-claro
        '#8A2BE2',  # Violeta
        '#008000',  # Verde
        '#8B4513',  # Marrom
        '#808080',  # Cinza
        '#FFC0CB',  # Rosa
        '#FF00FF',  # Magenta
        '#C8A2C8',  # Lilás
        '#00FFFF',  # Ciano
        '#50C878',  # Esmeralda
        '#FFD700',  # Dourado
    ]
    
    if n <= 15:
        return base_colors_hex[:n]
    
    # Se precisar de mais cores, criar gradientes
    colors = list(base_colors_hex)
    
    # Extrair valores RGB das cores base
    def hex_to_rgb(hex_str):
        hex_str = hex_str.lstrip('#')
        return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
    
    def rgb_to_hex(r, g, b):
        return f'#{r:02x}{g:02x}{b:02x}'
    
    base_rgb_tuples = [hex_to_rgb(c) for c in base_colors_hex]
    
    # Gerar cores intermediárias
    while len(colors) < n:
        for i in range(len(base_rgb_tuples) - 1):
            if len(colors) >= n:
                break
            r1, g1, b1 = base_rgb_tuples[i]
            r2, g2, b2 = base_rgb_tuples[i + 1]
            
            r_mid = (r1 + r2) // 2
            g_mid = (g1 + g2) // 2
            b_mid = (b1 + b2) // 2
            
            colors.append(rgb_to_hex(r_mid, g_mid, b_mid))
    
    return colors[:n]