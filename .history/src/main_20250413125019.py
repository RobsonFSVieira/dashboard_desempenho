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
    
    # Remover todos os espaços extras
    st.write(
        """
        <style>
            div[data-testid="stTitle"] {
                padding: 0 !important;
                margin: 0 !important;
            }
            
            .block-container {
                padding-top: 1rem !important;
                padding-bottom: 0rem !important;
                margin-top: -4rem !important;
            }

            section[data-testid="stSidebar"] > div {
                padding-top: 1rem !important;
            }

            .element-container {
                margin: 0 !important;
                padding: 0 !important;
            }

            div.stTabs > div > div > div > div.stMarkdown {
                margin-top: 0 !important;
                padding-top: 0 !important;
            }

            div[data-testid="stElementContainer"] iframe {
                height: 0 !important;
                min-height: 0 !important;
                display: none !important;
            }
        </style>
        """,
        unsafe_allow_html=True
    )
    
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