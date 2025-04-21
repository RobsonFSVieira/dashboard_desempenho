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
    df = dados['base']
    
    if df.empty:
        st.warning("Base de dados está vazia")
        return pd.DataFrame()
    
    # Aplicar filtros de data
    mask = (
        (df['retirada'].dt.date >= filtros[periodo]['inicio']) &
        (df['retirada'].dt.date <= filtros[periodo]['fim'])
    )
    df_filtrado = df[mask]
    
    # Aplicar filtros adicionais
    if filtros['cliente'] != ['Todos']:
        df_filtrado = df_filtrado[df_filtrado['CLIENTE'].isin(filtros['cliente'])]
        
    if filtros['operacao'] != ['Todas']:
        df_filtrado = df_filtrado[df_filtrado['OPERAÇÃO'].isin(filtros['operacao'])]
        
    if filtros['turno'] != ['Todos']:
        def get_turno(hour):
            if 7 <= hour < 15:
                return 'TURNO A'
            elif 15 <= hour < 23:
                return 'TURNO B'
            else:
                return 'TURNO C'
        df_filtrado = df_filtrado[df_filtrado['retirada'].dt.hour.apply(get_turno).isin(filtros['turno'])]
    
    # Agrupar por colaborador
    atendimentos = df_filtrado.groupby('COLABORADOR')['id'].count().reset_index()
    atendimentos.columns = ['colaborador', 'quantidade']
    
    return atendimentos

def criar_grafico_comparativo(dados_p1, dados_p2, filtros):
    """Cria o gráfico comparativo de atendimentos"""
    # Implementação do gráfico comparativo
    try:
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=dados_p1['colaborador'],
            y=dados_p1['quantidade'],
            name=f"Período {filtros['periodo1']['inicio']} - {filtros['periodo1']['fim']}",
            marker_color=obter_cores_tema()['primaria']
        ))
        
        fig.add_trace(go.Bar(
            x=dados_p2['colaborador'],
            y=dados_p2['quantidade'],
            name=f"Período {filtros['periodo2']['inicio']} - {filtros['periodo2']['fim']}",
            marker_color=obter_cores_tema()['secundaria']
        ))
        
        fig.update_layout(
            title="Comparativo de Atendimentos por Colaborador",
            xaxis_title="Colaborador",
            yaxis_title="Quantidade de Atendimentos",
            barmode='group',
            template='plotly_white',
            plot_bgcolor=obter_cores_tema()['fundo'],
            paper_bgcolor=obter_cores_tema()['fundo'],
            font=dict(color=obter_cores_tema()['texto'])
        )
        
        return fig
    except Exception as e:
        st.error(f"Erro ao criar gráfico: {str(e)}")
        return None

def gerar_insights_atendimentos(atend_p1, atend_p2):
    """Gera insights sobre os atendimentos dos colaboradores"""
    try:
        st.write("### Insights sobre os atendimentos")
        
        total_p1 = atend_p1['quantidade'].sum()
        total_p2 = atend_p2['quantidade'].sum()
        
        st.write(f"**Total de atendimentos no período 1:** {total_p1}")
        st.write(f"**Total de atendimentos no período 2:** {total_p2}")
        
        variacao = total_p2 - total_p1
        st.write(f"**Variação total:** {variacao} atendimentos")
        
        if variacao > 0:
            st.success("Houve um aumento nos atendimentos.")
        elif variacao < 0:
            st.error("Houve uma diminuição nos atendimentos.")
        else:
            st.info("O número de atendimentos permaneceu constante.")
    except Exception as e:
        st.error(f"Erro ao gerar insights: {str(e)}")

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