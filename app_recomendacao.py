import streamlit as st
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import requests

st.set_page_config(page_title="Recomendações de Filmes", layout="wide")
st.title("🍿 Meu Motor de Recomendação")
st.write("Conectado ao TMDB e filtrando dados históricos do Letterboxd")

# 1. Carregando a sua base histórica
@st.cache_data
def carregar_base_vistos():
    df = pd.read_csv("filmes_prontos_modelo.csv")
    # Força a tipagem do ID para texto para evitar falhas no filtro
    df['TMDB_Id'] = df['TMDB_Id'].fillna(0).astype(int).astype(str)
    return df

# 2. Buscando o catálogo dinâmico ao vivo
@st.cache_data
def buscar_catalogo_tmdb(api_key):
    url_generos = f"https://api.themoviedb.org/3/genre/movie/list?api_key={api_key}&language=en-US"
    try:
        mapa_generos = {item['id']: item['name'] for item in requests.get(url_generos).json().get('genres', [])}
    except:
        return pd.DataFrame() # Retorna vazio se a API falhar
        
    filmes_catalogo = []
    # Busca 4 páginas dos filmes mais bem avaliados da história
    for pagina in range(1, 5):
        url_busca = f"https://api.themoviedb.org/3/discover/movie?api_key={api_key}&language=en-US&sort_by=vote_count.desc&page={pagina}"
        resposta = requests.get(url_busca).json()
        if 'results' in resposta:
            for filme in resposta['results']:
                generos_texto = [mapa_generos.get(g_id, "Desconhecido") for g_id in filme.get('genre_ids', [])]
                filmes_catalogo.append({
                    'TMDB_Id': str(filme['id']),
                    'Titulo': filme['title'],
                    'Generos_Texto': generos_texto
                })
                
    df_cat = pd.DataFrame(filmes_catalogo)
    if not df_cat.empty:
        # One-Hot Encoding automático
        df_cat['Generos_String'] = df_cat['Generos_Texto'].apply(lambda x: '|'.join(x))
        df_binario = df_cat['Generos_String'].str.get_dummies(sep='|')
        df_cat = pd.concat([df_cat, df_binario], axis=1)
    return df_cat

# 3. Busca a imagem do pôster
def buscar_poster(tmdb_id, api_key):
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={api_key}&language=pt-BR" # Aqui mantemos pt-BR para o pôster vir em português!
    try:
        resposta = requests.get(url).json()
        if resposta.get('poster_path'):
            return f"https://image.tmdb.org/t/p/w500{resposta['poster_path']}"
    except:
        pass
    return "https://via.placeholder.com/500x750?text=Sem+Poster"

# 4. Interface Lateral
with st.sidebar:
    st.header("Configurações")
    api_key_input = st.text_input("Insira sua API Key do TMDB:", type="password")
    
    st.divider()
    st.write("O sistema guarda os dados na memória para ser mais rápido.")
    if st.button("Limpar Cache (Atualizar Catálogo)"):
        st.cache_data.clear()
        st.success("Cache limpo! Na próxima geração, os dados serão baixados novamente.")

# 5. Processamento e Tela Principal
if st.button("Gerar Recomendações"):
    if not api_key_input:
        st.warning("Por favor, insira sua API Key no menu lateral primeiro.")
    else:
        with st.spinner("Analisando seu gosto matemático e cruzando com a API..."):
            df_vistos = carregar_base_vistos()
            df_catalogo = buscar_catalogo_tmdb(api_key_input)
            
            if df_catalogo.empty:
                st.error("Falha ao buscar o catálogo. Verifique sua chave da API.")
            else:
                colunas_ignoradas = ['Titulo', 'Ano', 'Minha_Nota', 'TMDB_Id', 'Nota_Publico', 'Popularidade', 'Generos_Texto']
                colunas_generos = [c for c in df_vistos.columns if c not in colunas_ignoradas]
                
                features = df_vistos[colunas_generos]
                notas = df_vistos['Minha_Nota']
                perfil_usuario = features.T.dot(notas).values.reshape(1, -1)
                
                for col in colunas_generos:
                    if col not in df_catalogo.columns:
                        df_catalogo[col] = 0
                        
                # O Filtro Duplo blindado
                ids_vistos = df_vistos['TMDB_Id'].tolist()
                titulos_vistos = [str(t).lower() for t in df_vistos['Titulo'].tolist()]
                
                df_catalogo = df_catalogo[~df_catalogo['TMDB_Id'].isin(ids_vistos)]
                df_catalogo = df_catalogo[~df_catalogo['Titulo'].str.lower().isin(titulos_vistos)]
                
                df_catalogo_features = df_catalogo[colunas_generos]
                
                # Cálculo da Similaridade
                similaridades = cosine_similarity(perfil_usuario, df_catalogo_features.values)
                df_catalogo['Score'] = similaridades[0]
                
                df_top4 = df_catalogo.sort_values(by='Score', ascending=False).head(10)
                
                st.subheader("Filmes recomendados para o fim de semana:")
                colunas_interface = st.columns(10)
                
                for index, row in enumerate(df_top4.itertuples()):
                    url_imagem = buscar_poster(row.TMDB_Id, api_key_input)
                    with colunas_interface[index]:
                        st.image(url_imagem, use_container_width=True)
                        st.markdown(f"**{row.Titulo}**")