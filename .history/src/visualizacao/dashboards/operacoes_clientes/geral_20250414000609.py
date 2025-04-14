import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

def formatar_tempo(minutos):
    """Formata o tempo de minutos para o formato mm:ss"""
    minutos_parte = int(minutos)
    segundos_parte = int((minutos - minutos_parte) * 60)
    return f"{minutos_parte:02d}:{segundos_parte:02d} min"

def calcular_metricas_gerais(dados, filtros):
    """Calcula métricas gerais para o período selecionado"""
    df = dados['base']
    
    # Aplicar filtros de data
    mask = (
        (df['retirada'].dt.date >= filtros['periodo2']['inicio']) &
        (df['retirada'].dt.date <= filtros['periodo2']['fim'])
    )
    
    # Aplicar filtros adicionais
    if filtros['cliente'] != ['Todos']:
        mask &= df['CLIENTE'].isin(filtros['cliente'])
    if filtros['operacao'] != ['Todas']:
        mask &= df['OPERAÇÃO'].isin(filtros['operacao'])
    if filtros['turno'] != ['Todos']:
        mask &= df['retirada'].dt.hour.apply(lambda x: 'A' if 7 <= x < 15 else ('B' if 15 <= x < 23 else 'C')).isin(filtros['turno'])
    
    df_filtrado = df[mask]
    
    # Cálculo das métricas
    total_atendimentos = len(df_filtrado)
    media_tempo_atendimento = df_filtrado['tpatend'].mean() / 60  # em minutos
    media_tempo_espera = df_filtrado['tpesper'].mean() / 60  # em minutos
    media_permanencia = df_filtrado['tempo_permanencia'].mean() / 60  # em minutos
    
    return {
        'total_atendimentos': total_atendimentos,
        'media_tempo_atendimento': media_tempo_atendimento,
        'media_tempo_espera': media_tempo_espera,
        'media_permanencia': media_permanencia
    }

def criar_grafico_atendimentos_diarios(dados, filtros):
    """Cria gráfico de atendimentos diários"""
    df = dados['base']
    
    # Agrupa dados por data
    df_diario = df.groupby(df['retirada'].dt.date).size().reset_index()
    df_diario.columns = ['data', 'quantidade']
    
    # Cria o gráfico
    fig = px.line(
        df_diario, 
        x='data', 
        y='quantidade',
        title='Atendimentos Diários',
        labels={'data': 'Data', 'quantidade': 'Quantidade de Atendimentos'}
    )
    
    return fig

def criar_grafico_top_clientes(dados, filtros):
    """Cria gráfico dos top 10 clientes"""
    df = dados['base']
    
    # Agrupa dados por cliente
    df_clientes = df.groupby('CLIENTE').size().reset_index()
    df_clientes.columns = ['cliente', 'quantidade']
    df_clientes = df_clientes.sort_values('quantidade', ascending=True).tail(10)
    
    # Cria o gráfico
    fig = px.bar(
        df_clientes,
        x='quantidade',
        y='cliente',
        title='Top 10 Clientes',
        orientation='h',
        labels={
            'quantidade': 'Quantidade de Atendimentos',
            'cliente': 'Cliente'
        },
        text='quantidade'  # Adiciona os valores nas barras
    )
    
    # Atualiza o layout para garantir que os rótulos apareçam
    fig.update_layout(
        xaxis_title="Quantidade de Atendimentos",
        yaxis_title="Cliente",
        title_x=0.5,
        margin=dict(l=10, r=120, t=40, b=10),  # Aumenta margem direita para 120
        height=400,  # Define altura fixa
        uniformtext=dict(minsize=10, mode='show')  # Garante visibilidade uniforme do texto
    )
    
    # Atualiza os eixos e o formato do texto
    fig.update_traces(
        textposition='outside',
        textangle=0,  # Mantém o texto horizontal
        cliponaxis=False  # Impede que o texto seja cortado
    )
    fig.update_xaxes(showgrid=True)
    fig.update_yaxes(showgrid=False)
    
    return fig

def gerar_insights_gerais(dados, filtros, metricas):
    """Gera insights sobre as operações gerais"""
    df = dados['base']
    
    # Aplicar filtros de data
    mask = (
        (df['retirada'].dt.date >= filtros['periodo2']['inicio']) &
        (df['retirada'].dt.date <= filtros['periodo2']['fim'])
    )
    
    # Aplicar filtros adicionais
    if filtros['cliente'] != ['Todos']:
        mask &= df['CLIENTE'].isin(filtros['cliente'])
    if filtros['operacao'] != ['Todas']:
        mask &= df['OPERAÇÃO'].isin(filtros['operacao'])
    if filtros['turno'] != ['Todos']:
        mask &= df['retirada'].dt.hour.apply(lambda x: 'A' if 7 <= x < 15 else ('B' if 15 <= x < 23 else 'C')).isin(filtros['turno'])
    
    df = df[mask]
    
    # Análise por períodos do dia
    df['hora'] = df['retirada'].dt.hour
    manha = df[df['hora'].between(6, 11)]['id'].count()
    tarde = df[df['hora'].between(12, 17)]['id'].count()
    noite = df[df['hora'].between(18, 23)]['id'].count()
    total = manha + tarde + noite
    
    # Evitar divisão por zero
    total = max(total, 1)  # Se total for 0, usa 1 para evitar divisão por zero
    
    # Análise de eficiência
    tempo_meta = filtros.get('meta_permanencia', 30)
    atendimentos_eficientes = df[df['tempo_permanencia'] <= tempo_meta * 60]['id'].count()
    taxa_eficiencia = (atendimentos_eficientes / len(df) * 100) if len(df) > 0 else 0
    
    # Análise de pontos fora da meta
    tempo_meta_segundos = tempo_meta * 60
    df['status_meta'] = df['tempo_permanencia'].apply(lambda x: 'Dentro' if x <= tempo_meta_segundos else 'Fora')
    pontos_fora = df[df['status_meta'] == 'Fora']

    # ... existing comboio analysis code ...

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Visão Geral do Período Filtrado")
        st.markdown(f"""
        <div style='border:1px solid #ddd; border-radius:5px; padding:15px; margin-bottom:20px;'>
            📌 Atendimentos no período: {len(df):,} atendimentos
            <br>⏱️ Tempo médio total: {formatar_tempo(df['tempo_permanencia'].mean() / 60)}
            <br>📈 Taxa de eficiência: {taxa_eficiencia:.1f}%
        </div>
        """, unsafe_allow_html=True)
        
        st.subheader("📈 Indicadores de Tempo no Período")
        st.markdown(f"""
        <div style='border:1px solid #ddd; border-radius:5px; padding:15px; margin-bottom:20px;'>
            ⏳ Tempo médio de espera: {formatar_tempo(df['tpesper'].mean() / 60)}
            <br>⚡ Tempo médio de atendimento: {formatar_tempo(df['tpatend'].mean() / 60)}
            <br>🎯 Meta de permanência: {tempo_meta}:00 min
        </div>
        """, unsafe_allow_html=True)

    # ... rest of the existing code ...

def mostrar_aba(dados, filtros):
    """Mostra a aba Geral do dashboard"""
    st.header("Visão Geral das Operações")
    
    try:
        # Cálculo das métricas gerais
        metricas = calcular_metricas_gerais(dados, filtros)
        
        # Layout das métricas em colunas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total de Atendimentos",
                f"{metricas['total_atendimentos']:,} atendimentos",
                help="Número total de atendimentos no período"
            )
        
        with col2:
            st.metric(
                "Tempo Médio de Atendimento",
                formatar_tempo(metricas['media_tempo_atendimento']),
                help="Tempo médio de atendimento no período"
            )
        
        with col3:
            st.metric(
                "Tempo Médio de Espera",
                formatar_tempo(metricas['media_tempo_espera']),
                help="Tempo médio de espera em fila no período"
            )
        
        with col4:
            st.metric(
                "Tempo Médio de Permanência",
                formatar_tempo(metricas['media_permanencia']),
                help="Tempo médio total (espera + atendimento)"
            )
        
        # Gráficos
        col_left, col_right = st.columns(2)
        
        with col_left:
            fig_diario = criar_grafico_atendimentos_diarios(dados, filtros)
            st.plotly_chart(fig_diario, use_container_width=True)
        
        with col_right:
            fig_clientes = criar_grafico_top_clientes(dados, filtros)
            st.plotly_chart(fig_clientes, use_container_width=True)
        
        # Insights
        st.markdown("---")
        st.subheader("📈 Análise Detalhada")
        with st.expander("Ver análise completa", expanded=True):
            gerar_insights_gerais(dados, filtros, metricas)
    
    except Exception as e:
        st.error("Erro ao gerar a aba Geral")
        st.exception(e)