import streamlit as st
from visualizacao.dashboards.desenvolvimento_pessoas.ranking import create_ranking_layout

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Atendimento",
    page_icon="📊",
    layout="wide"
)

# Título do dashboard
st.title("Dashboard de Atendimento")

# Layout principal
create_ranking_layout()
