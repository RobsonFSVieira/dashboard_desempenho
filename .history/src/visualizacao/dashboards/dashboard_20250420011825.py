import streamlit as st
from datetime import datetime, timedelta
from .operacoes_clientes import (
    visao_geral, tempo_atend, permanencia, mov_cliente, espera, comboio_i
)
from .desenvolvimento_pessoas import (
    colaborador, tempo_atend as dp_tempo_atend
)

def mostrar_dashboard(dados):
    """Mostra o dashboard principal"""
    st.title("Dashboard de Análise")
    
    # Configurar período na sidebar
    with st.sidebar:
        st.header("Configurações")
        
        # Período 1
        st.subheader("Período 1 (Referência)")
        data_inicio1 = st.date_input(
            "Data Inicial",
            datetime.now().date() - timedelta(days=14),
            key="data_inicio1"
        )
        data_fim1 = st.date_input(
            "Data Final",
            datetime.now().date() - timedelta(days=7),
            key="data_fim1"
        )
        
        # Período 2
        st.subheader("Período 2 (Comparação)")
        data_inicio2 = st.date_input(
            "Data Inicial",
            datetime.now().date() - timedelta(days=7),
            key="data_inicio2"
        )
        data_fim2 = st.date_input(
            "Data Final",
            datetime.now().date(),
            key="data_fim2"
        )
    
    # Criar dicionário de filtros
    filtros = {
        'periodo1': {'inicio': data_inicio1, 'fim': data_fim1},
        'periodo2': {'inicio': data_inicio2, 'fim': data_fim2}
    }
    
    # Criar abas
    tab1, tab2, tab3 = st.tabs([
        "👥 Visão Geral",
        "⌚ Tempo de Atendimento",
        "👤 Análise Individual"
    ])
    
    # Conteúdo das abas
    with tab1:
        visao_geral.mostrar_aba(dados, filtros)
    
    with tab2:
        dp_tempo_atend.mostrar_aba(dados, filtros)
    
    with tab3:
        colaborador.mostrar_aba(dados, filtros)
