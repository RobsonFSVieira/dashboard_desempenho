import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def mostrar_aba(dados, filtros):
    """Mostra a aba de Ranking de Desempenho"""
    st.header("Ranking de Desempenho")
    
    try:
        df = dados['base']
        
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            indicador = st.selectbox(
                "Indicador",
                ["Produtividade", "Tempo Médio", "Geral"],
                help="Selecione o indicador para ranking"
            )
        
        with col2:
            periodo = st.radio(
                "Período",
                ["Último Período", "Comparativo"],
                horizontal=True
            )
        
        # Calcular métricas por colaborador
        metricas = calcular_metricas_colaborador(df, filtros, indicador)
        
        # Criar e mostrar gráfico
        fig = criar_grafico_ranking(metricas, periodo)
        st.plotly_chart(fig, use_container_width=True)
        
        # Mostrar insights
        mostrar_insights(metricas)
        
    except Exception as e:
        st.error("Erro ao gerar o ranking de desempenho")
        st.exception(e)

def calcular_metricas_colaborador(df, filtros, indicador):
    """Calcula métricas de desempenho por colaborador"""
    # Aplicar filtros de data
    mask = (
        (df['retirada'].dt.date >= filtros['periodo2']['inicio']) &
        (df['retirada'].dt.date <= filtros['periodo2']['fim'])
    )
    df_filtrado = df[mask]
    
    # Agrupar por colaborador
    if indicador == "Produtividade":
        metricas = df_filtrado.groupby('usuário')['id'].count().reset_index()
        metricas.columns = ['colaborador', 'valor']
    elif indicador == "Tempo Médio":
        metricas = df_filtrado.groupby('usuário')['tpatend'].mean().reset_index()
        metricas.columns = ['colaborador', 'valor']
        metricas['valor'] = metricas['valor'] / 60  # Converter para minutos
    else:  # Geral - combina múltiplos indicadores
        metricas = df_filtrado.groupby('usuário').agg({
            'id': 'count',
            'tpatend': 'mean',
            'tpesper': 'mean'
        }).reset_index()
        metricas.columns = ['colaborador', 'atendimentos', 'tempo_atend', 'tempo_espera']
        # Normalizar e combinar métricas
        metricas['valor'] = (
            metricas['atendimentos'] / metricas['atendimentos'].max() * 0.5 +
            (1 - metricas['tempo_atend'] / metricas['tempo_atend'].max()) * 0.3 +
            (1 - metricas['tempo_espera'] / metricas['tempo_espera'].max()) * 0.2
        ) * 100
    
    return metricas.sort_values('valor', ascending=False)

def criar_grafico_ranking(metricas, periodo):
    """Cria gráfico de ranking"""
    fig = go.Figure()
    
    # Adicionar barras
    fig.add_trace(go.Bar(
        y=metricas['colaborador'],
        x=metricas['valor'],
        orientation='h',
        text=metricas['valor'].round(1),
        textposition='auto',
        marker_color='royalblue'
    ))
    
    # Atualizar layout
    fig.update_layout(
        title="Ranking de Desempenho",
        xaxis_title="Pontuação",
        yaxis_title="Colaborador",
        height=max(400, len(metricas) * 30)
    )
    
    return fig

def mostrar_insights(metricas):
    """Mostra insights sobre o ranking"""
    st.subheader("📊 Análise do Ranking")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("#### 🏆 Top 3 Performers")
        top3 = metricas.head(3)
        for i, row in top3.iterrows():
            st.write(f"**{i+1}º** {row['colaborador']}: {row['valor']:.1f} pontos")
    
    with col2:
        st.write("#### 📈 Estatísticas")
        st.write(f"**Média geral:** {metricas['valor'].mean():.1f}")
        st.write(f"**Mediana:** {metricas['valor'].median():.1f}")
        st.write(f"**Desvio padrão:** {metricas['valor'].std():.1f}")
