#  Letterboxd Recommendation Engine (Data Pipeline & Web App)

Um pipeline de dados *end-to-end* que extrai histórico de consumo de filmes (Letterboxd), enriquece metadados consumindo a API REST do The Movie Database (TMDB) e gera recomendações matemáticas personalizadas em uma interface web pública.

🔗 **[Acesse a Aplicação ao Vivo Aqui](https://vzanonit-recomendador-filmes.streamlit.app/)**

##  Arquitetura do Projeto (Pipeline ETL)

O projeto foi desenhado com foco em automação e consistência de *Master Data*:
*   **Extract:** Rotina de carga incremental (Delta Load) via parsing de feed RSS (XML) do Letterboxd para capturar apenas novas interações do usuário, otimizando o tempo de execução.
*   **Transform:** Tratamento de dados nulos, conversão estrita de tipagem (chaves primárias), tratamento de strings e aplicação de *One-Hot Encoding* para transformar variáveis categóricas (gêneros) em matrizes binárias.
*   **Load / Serve:** Disponibilização da interface interativa via Streamlit Cloud. O algoritmo calcula a distância vetorial (*Cosine Similarity*) entre o perfil histórico do usuário e o catálogo dinâmico da API para sugerir os filmes com maior afinidade geométrica.

## 🛠️ Stack Tecnológico
*   **Linguagem:** Python
*   **Processamento e Modelagem:** Pandas, Scikit-Learn
*   **Integração e Orquestração:** Requests, Feedparser
*   **Frontend e Deploy:** Streamlit, Streamlit Community Cloud, Git/GitHub

##  Desafios de Engenharia Resolvidos
1. **Inconsistência de Idiomas e Duplicidades:** O cruzamento da base original (títulos em inglês) com o catálogo da API (títulos traduzidos) gerava falhas no sistema de recomendação. A solução foi padronizar a taxonomia das requisições REST (`language=en-US`) e implementar um "filtro duplo" (cruzamento por Título e TMDB_Id tipado) para garantir a exclusão perfeita de filmes já assistidos.
2. **Falhas de Coleta na API (Tratamento de Exceções):** Alguns filmes antigos não retornavam na busca exata por Título + Ano. Foi implementada uma lógica de *Fallback* inteligente: o script tenta a busca estrita; em caso de falha, relaxa os parâmetros iterativamente para garantir o enriquecimento do dado.

##  Como Executar Localmente

1. Clone o repositório:
##  Como Executar Localmente

1. Clone o repositório:
```bash
git clone [https://github.com/VZTester/Sistema-de-recomendacao-letterboxd.git](https://github.com/VZTester/Sistema-de-recomendacao-letterboxd.git)
```
1. Instale as dependências
```bash
pip install -r requirements.txt
```
2.Execute a aplicação na sua máquina
```bash
streamlit run app_recomendacao.py
```
(Nota: É necessário possuir uma chave gratuita da API do TMDB).
