import streamlit as st
import pandas as pd
from processamento.carregar_dados import carregar_dados
from visualizacao.filtros import criar_filtros
from visualizacao.gerar_dashboard import criar_dashboard

def main():
    """Função principal do dashboard"""
    st.set_page_config(
        page_title="Dashboard de Atendimento",
        page_icon="📊",
        layout="wide"
    )
    
    # CSS atualizado para remover espaços desnecessários
    st.markdown("""
        <style>
        .block-container {
            padding: 0 !important;
            margin-top: -4rem !important;
        }
        div.block-container > div:first-child {
            margin: 0 !important;
            padding: 0 !important;
        }
        header {
            margin: 0 !important;
            padding: 0 !important;
        }
        [data-testid="stTitle"] {
            margin: 0 !important;
            padding: 0 !important;
        }
        .stTitle > h1 {
            margin: 0 !important;
            padding: 0 !important;
        }
        .main > div:first-child {
            margin-top: -2rem !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Título principal
    st.title("Dashboard de Atendimento 📊")
    
    # Inicializar estado da sessão
    if 'dados' not in st.session_state:
        st.session_state.dados = None
    
    # Carregar dados
    dados = carregar_dados()
    if dados:
        st.session_state.dados = dados
    
    # Criar filtros
    filtros = criar_filtros()
    
    # Seleção do tipo de dashboard
    tipo_dashboard = st.sidebar.radio(
        "Selecione o Dashboard:",
        ["Performance Cliente/Operação", "Desenvolvimento de Pessoas"]
    )
    
    # Criar dashboard
    criar_dashboard(dados, filtros, tipo_dashboard)

if __name__ == "__main__":
    main()