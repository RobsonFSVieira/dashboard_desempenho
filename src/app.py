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
dados_path = os.path.join("dados", "base.xlsx")  # Ajuste o nome do arquivo conforme necessário

# Carregamento dos dados
try:
    if os.path.exists(dados_path):
        df = pd.read_excel(dados_path)
        st.title("Dashboard de Atendimento")
        # ... resto do seu código ...
    else:
        st.error(f"❌ Arquivo não encontrado: {dados_path}")
        st.info("📊 Carregue os dados e selecione os filtros para visualizar o dashboard.")
except Exception as e:
    st.error(f"❌ Erro ao carregar base: {str(e)}")
    st.info("📊 Carregue os dados e selecione os filtros para visualizar o dashboard.")
