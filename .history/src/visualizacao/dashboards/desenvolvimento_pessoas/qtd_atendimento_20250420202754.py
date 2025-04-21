import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
from datetime import datetime

def detectar_tema():
    """Detecta se o tema atual é claro ou escuro"""
    try:
        theme_param = st.query_params.get('theme', None)
        if theme_param:
            return json.loads(theme_param)['base']
        else:
            return st.config.get_option('theme.base')
    except:
        return 'light'

def obter_cores_tema():
    """Retorna as cores baseadas no tema atual"""
    is_dark = detectar_tema() == 'dark'
    return {
        'primaria': '#1a5fb4' if is_dark else '#1864ab',
        'secundaria': '#4dabf7' if is_dark else '#83c9ff',
        'texto': '#ffffff' if is_dark else '#2c3e50',
        'fundo': '#0e1117' if is_dark else '#ffffff',
        'grid': '#2c3e50' if is_dark else '#e9ecef',
        'sucesso': '#2dd4bf' if is_dark else '#29b09d',
        'erro': '#ff6b6b' if is_dark else '#ff5757'
    }

def calcular_atendimentos_por_periodo(dados, filtros, periodo):
    """Calcula a quantidade de atendimentos por colaborador no período especificado"""
    # ...resto do código copiado do arquivo original...

def criar_grafico_comparativo(dados_p1, dados_p2, filtros):
    """Cria o gráfico comparativo de atendimentos"""
    # ...resto do código copiado do arquivo original...

def gerar_insights_atendimentos(atend_p1, atend_p2):
    """Gera insights sobre os atendimentos dos colaboradores"""
    # ...resto do código copiado do arquivo original...

def mostrar_aba(dados, filtros):
    """Mostra a aba de Quantidade de Atendimento"""
    st.header("Quantidade de Atendimento")
    
    try:
        # Adiciona um key único que muda quando o tema muda
        st.session_state['tema_atual'] = detectar_tema()
        
        # Calcula atendimentos para os dois períodos
        atend_p1 = calcular_atendimentos_por_periodo(dados, filtros, 'periodo1')
        atend_p2 = calcular_atendimentos_por_periodo(dados, filtros, 'periodo2')
        
        if atend_p1.empty or atend_p2.empty:
            st.warning("Não há dados para exibir no período selecionado.")
            return
        
        # Cria e exibe o gráfico comparativo
        fig = criar_grafico_comparativo(atend_p1, atend_p2, filtros)
        if fig:
            st.plotly_chart(
                fig, 
                use_container_width=True, 
                key=f"grafico_atendimento_{st.session_state['tema_atual']}"
            )
            
        # Adiciona insights abaixo do gráfico
        st.markdown("---")
        st.subheader("📈 Análise Detalhada")
        with st.expander("Ver análise detalhada", expanded=True):
            gerar_insights_atendimentos(atend_p1, atend_p2)
    
    except Exception as e:
        st.error(f"Erro ao mostrar aba: {str(e)}")
        st.exception(e)
