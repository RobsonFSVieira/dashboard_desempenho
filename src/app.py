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

# Tentativa 1: Usando caminho relativo simples
dados_path = "dados/base.xlsx"

# Debug info expandido
with st.expander("🔍 Informações de Debug"):
    st.write("Método 1 - Caminho relativo simples:", dados_path)
    st.write("Arquivo existe?", os.path.exists(dados_path))
    
    # Tentativa 2: Usando Path
    path_alt = Path(__file__).parent.parent / "dados" / "base.xlsx"
    st.write("Método 2 - Usando Path:", str(path_alt))
    st.write("Arquivo existe?", path_alt.exists())
    
    # Listar arquivos no diretório atual
    st.write("Arquivos no diretório atual:", os.listdir())
    st.write("Diretório atual:", os.getcwd())

# Carregamento dos dados
try:
    if os.path.exists(dados_path):
        df = pd.read_excel(dados_path)
        st.title("Dashboard de Atendimento")
        # ... resto do seu código ...
    else:
        alt_path = Path(__file__).parent.parent / "dados" / "base.xlsx"
        if alt_path.exists():
            df = pd.read_excel(alt_path)
            st.title("Dashboard de Atendimento")
            # ... resto do seu código ...
        else:
            st.error("❌ Arquivo não encontrado em nenhum dos caminhos testados")
            st.info(f"📊 Caminhos tentados:\n1. {dados_path}\n2. {alt_path}")
except Exception as e:
    st.error(f"❌ Erro ao carregar base: {str(e)}")
    st.info(f"📊 Tipo do erro: {type(e).__name__}")
    st.info(f"📊 Detalhes completos do erro: {e}")
