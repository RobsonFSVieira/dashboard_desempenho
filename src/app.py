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
with st.expander("🔍 Informações de Debug", expanded=True):
    st.write("### Informações do Ambiente")
    st.write("• Diretório atual:", os.getcwd())
    st.write("• Arquivos no diretório:", os.listdir())
    st.write("• Variáveis de ambiente:", {k: v for k, v in os.environ.items() if k.startswith(('STREAMLIT', 'PATH'))})
    
    st.write("\n### Tentativas de Carregamento")
    # Tentativa 1: Caminho relativo simples
    st.write("**Método 1 - Caminho relativo**")
    st.write(f"• Caminho: {dados_path}")
    st.write(f"• Existe? {'✅' if os.path.exists(dados_path) else '❌'}")
    
    # Tentativa 2: Usando Path
    path_alt = Path(__file__).parent.parent / "dados" / "base.xlsx"
    st.write("\n**Método 2 - Usando Path**")
    st.write(f"• Caminho: {path_alt}")
    st.write(f"• Existe? {'✅' if path_alt.exists() else '❌'}")
    
    # Tentativa 3: Caminho absoluto
    path_abs = os.path.abspath(dados_path)
    st.write("\n**Método 3 - Caminho Absoluto**")
    st.write(f"• Caminho: {path_abs}")
    st.write(f"• Existe? {'✅' if os.path.exists(path_abs) else '❌'}")

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
    st.error(f"""
    ❌ Erro ao carregar base de dados:
    
    **Detalhes do Erro**
    • Tipo: {type(e).__name__}
    • Mensagem: {str(e)}
    
    **Caminhos Tentados**
    • Relativo: {dados_path}
    • Path: {path_alt}
    • Absoluto: {path_abs}
    
    **Ambiente**
    • Diretório atual: {os.getcwd()}
    • Rodando em: {'Streamlit Cloud' if os.getenv('STREAMLIT_CLOUD') == 'true' else 'Local'}
    """)
