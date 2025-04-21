import streamlit as st
import pandas as pd
import os
from pathlib import Path

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Atendimento",
    page_icon="📊",
    layout="wide"
)

# Caminho relativo para os dados usando Path
current_dir = Path(__file__).parent.parent
dados_path = current_dir / "dados" / "base.xlsx"

# Debug info
st.write("Debug - Caminho tentado:", str(dados_path))
st.write("Debug - Arquivo existe?", os.path.exists(dados_path))
st.write("Debug - Diretório atual:", os.getcwd())

# Carregamento dos dados
try:
    if os.path.exists(dados_path):
        df = pd.read_excel(dados_path)
        st.title("Dashboard de Atendimento")
        # ... resto do seu código ...
    else:
        st.error(f"❌ Arquivo não encontrado: {dados_path}")
        st.info("📊 Verifique se o arquivo está na pasta correta.")
except Exception as e:
    st.error(f"❌ Erro ao carregar base: {str(e)}")
    st.info(f"📊 Erro detalhado: {type(e).__name__}")
