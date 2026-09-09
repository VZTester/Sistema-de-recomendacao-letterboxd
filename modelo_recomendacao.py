import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import requests
import numpy as np

api_key = "Insira_sua_API"

print("1. Carregando seu perfil de filmes assistidos...")
df_assistidos = pd.read_csv("filmes_prontos_modelo.csv")
colunas_ignoradas = ['Titulo', 'Ano', 'Minha_Nota', 'TMDB_Id', 'Nota_Publico', 'Popularidade', 'Generos_Texto']
colunas_generos = [c for c in df_assistidos.columns if c not in colunas_ignoradas]

# Calculando o Perfil do Usuário
features = df_assistidos[colunas_generos]
notas = df_assistidos['Minha_Nota']
perfil_usuario = features.T.dot(notas)

print("2. Buscando filmes populares no TMDB para o novo catálogo...")
# Pegamos o dicionário de gêneros primeiro para traduzir os IDs
url_generos = f"https://api.themoviedb.org/3/genre/movie/list?api_key={api_key}&language=en-US"
mapa_generos = {item['id']: item['name'] for item in requests.get(url_generos).json()['genres']}

# Agora buscamos 2 páginas de filmes populares (aprox. 40 filmes)
# Aumentei para 5 páginas (100 filmes) para dar um catálogo bem rico ao algoritmo
filmes_catalogo = []
for pagina in range(1, 6):
    
    # Busca os filmes mais avaliados da história (não importa a data de lançamento)
    url_busca = f"https://api.themoviedb.org/3/discover/movie?api_key={api_key}&language=en-US&sort_by=vote_count.desc&page={pagina}"
    
    resposta = requests.get(url_busca).json()
    
    for filme in resposta['results']:
        generos_texto = [mapa_generos.get(g_id, "Desconhecido") for g_id in filme.get('genre_ids', [])]
        
        filmes_catalogo.append({
            'TMDB_Id': filme['id'],
            'Titulo': filme['title'],
            'Generos_Texto': generos_texto
        })

df_catalogo = pd.DataFrame(filmes_catalogo)

print("3. Processando os dados do catálogo novo...")
# Transformando a lista de gêneros em colunas binárias (One-Hot Encoding)
df_catalogo['Generos_String'] = df_catalogo['Generos_Texto'].apply(lambda x: '|'.join(x))
df_binario_catalogo = df_catalogo['Generos_String'].str.get_dummies(sep='|')
df_catalogo = pd.concat([df_catalogo, df_binario_catalogo], axis=1)

# GARANTIA DE ENGENHARIA: Alinhando as colunas do catálogo com as colunas do seu perfil
for col in colunas_generos:
    if col not in df_catalogo.columns:
        df_catalogo[col] = 0 # Preenche com 0 se o gênero não existir nos filmes em alta
# 1. Tratamento e filtro pelo ID
df_assistidos['TMDB_Id'] = df_assistidos['TMDB_Id'].fillna(0).astype(int).astype(str)
df_catalogo['TMDB_Id'] = df_catalogo['TMDB_Id'].astype(str)

ids_vistos = df_assistidos['TMDB_Id'].tolist()
df_catalogo = df_catalogo[~df_catalogo['TMDB_Id'].isin(ids_vistos)]

# 2. Tratamento e filtro por Título (Backup caso o ID tenha falhado na extração)
# Convertendo tudo para minúsculo para evitar que "Parasita" seja lido diferente de "parasita"
titulos_vistos = [str(t).lower() for t in df_assistidos['Titulo'].tolist()]
df_catalogo = df_catalogo[~df_catalogo['Titulo'].str.lower().isin(titulos_vistos)]

# Selecionamos apenas as colunas numéricas de gêneros, na exata mesma ordem do perfil
df_catalogo_features = df_catalogo[colunas_generos]

print("4. Calculando a similaridade...")
perfil_array = perfil_usuario.values.reshape(1, -1)
catalogo_array = df_catalogo_features.values

similaridades = cosine_similarity(perfil_array, catalogo_array)

df_catalogo['Score_Afinidade'] = similaridades[0]
df_resultados = df_catalogo[['Titulo', 'Score_Afinidade']].sort_values(by='Score_Afinidade', ascending=False).head(10)

print("\n🍿 SEU TOP 10 RECOMENDAÇÕES (Baseado nos filmes em alta):")
print(df_resultados.to_string(index=False))
