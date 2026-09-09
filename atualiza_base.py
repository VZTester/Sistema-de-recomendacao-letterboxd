import feedparser
import pandas as pd
import requests
import os

# 1. Configurações Iniciais
api_key = "133a38d257bf8625b4ed339a01dd67af"
arquivo_base = "filmes_prontos_modelo.csv"

print("🔄 1. Lendo base atual...")
df_atual = pd.read_csv(arquivo_base)
# Convertendo para minúsculo para garantir que o filtro não falhe por causa de letras maiúsculas
titulos_existentes = [str(t).lower() for t in df_atual['Titulo'].tolist()]

print("📡 2. Consultando RSS do Letterboxd...")
url_rss = "https://letterboxd.com/vztx/rss/"
feed = feedparser.parse(url_rss)

novos_filmes = []

# 3. Filtrando apenas filmes inéditos
for entrada in feed.entries:
    titulo = entrada.get('letterboxd_filmtitle')
    nota = entrada.get('letterboxd_memberrating')
    ano = entrada.get('letterboxd_filmyear')

    if titulo and str(titulo).lower() not in titulos_existentes and nota:
        novos_filmes.append({
            'Titulo': titulo,
            'Ano': ano,
            'Minha_Nota': float(nota)
        })

# 4. Enriquecimento e Carga
if not novos_filmes:
    print("✅ Sua base já está 100% sincronizada com o Letterboxd.")
else:
    print(f"⚠️ Encontrados {len(novos_filmes)} filmes novos! Iniciando enriquecimento via TMDB...\n")
    
    url_generos = f"https://api.themoviedb.org/3/genre/movie/list?api_key={api_key}&language=en-US"
    mapa_generos = {item['id']: item['name'] for item in requests.get(url_generos).json().get('genres', [])}
    
    dados_enriquecidos = []
    
    for filme in novos_filmes:
        titulo = filme['Titulo']
        ano = filme['Ano']
        
        # Bate na API de busca para achar o ID e gêneros do filme novo
        url_busca = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={titulo}&primary_release_year={ano}&language=en-US"
        resposta = requests.get(url_busca).json()
        
        if resposta.get('results'):
            tmdb_data = resposta['results'][0]
            generos_texto = [mapa_generos.get(g_id, "Desconhecido") for g_id in tmdb_data.get('genre_ids', [])]
            
            filme_completo = {
                'Titulo': titulo,
                'Ano': ano,
                'Minha_Nota': filme['Minha_Nota'],
                'TMDB_Id': tmdb_data['id'],
                'Nota_Publico': tmdb_data.get('vote_average', 0),
                'Popularidade': tmdb_data.get('popularity', 0),
                'Generos_Texto': generos_texto
            }
            dados_enriquecidos.append(filme_completo)
            print(f" [+] Processado e adicionado: {titulo}")
        else:
            print(f" [-] Falha ao encontrar no TMDB: {titulo}")
            
    if dados_enriquecidos:
        print("\n⚙️ Aplicando transformações (One-Hot Encoding)...")
        df_novos = pd.DataFrame(dados_enriquecidos)
        
        df_novos['Generos_String'] = df_novos['Generos_Texto'].apply(lambda x: '|'.join(x))
        df_binario = df_novos['Generos_String'].str.get_dummies(sep='|')
        df_novos = pd.concat([df_novos, df_binario], axis=1)
        
        # Garante que os novos filmes tenham as exatas mesmas colunas do CSV antigo (preenchendo com 0)
        for col in df_atual.columns:
            if col not in df_novos.columns:
                df_novos[col] = 0
                
        # Alinha a ordem das colunas e junta as duas tabelas
        df_novos = df_novos[df_atual.columns]
        df_final = pd.concat([df_atual, df_novos], ignore_index=True)
        
        # Sobrescreve o arquivo CSV com a base atualizada
        df_final.to_csv(arquivo_base, index=False)
        print(f"🚀 Sucesso! {len(dados_enriquecidos)} novos filmes foram salvos no CSV.")