import streamlit as st
import pandas as pd
import os

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Atendimento",
    page_icon="📊",
    layout="wide"
)

# Caminho relativo para os dados
dados_path = os.path.join("..", "dados", "seu_arquivo.xlsx")

# Carregamento dos dados
try:
    df = pd.read_excel(dados_path)
    st.title("Dashboard de Atendimento")
    # ... resto do seu código ...
except Exception as e:
    st.error(f"Erro ao carregar os dados: {e}")
    st.write("Caminho tentado:", dados_path)
