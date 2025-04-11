import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots  # Adicionando o import necessário
from datetime import datetime

def calcular_metricas_colaborador(dados, filtros, turno=None):
    """Calcula métricas de performance por colaborador"""
    df = dados['base']
    
    # Aplicar filtros de data para período 2
    mask = (
        (df['retirada'].dt.date >= filtros['periodo2']['inicio']) &
        (df['retirada'].dt.date <= filtros['periodo2']['fim'])
    )
    df_filtrado = df[mask]
    
    # Identificar turno dos atendimentos
    df_filtrado['turno'] = df_filtrado['inicio'].dt.hour.apply(
        lambda x: 'A' if 7 <= x < 15 else ('B' if 15 <= x < 23 else 'C')
    )
    
    # Filtrar por turno se especificado
    if turno and turno != "Todos":
        df_filtrado = df_filtrado[df_filtrado['turno'] == turno]
    
    # Calcular métricas por colaborador
    metricas = df_filtrado.groupby('usuário').agg({
        'id': 'count',
        'tpatend': ['mean', 'std'],
        'tpesper': 'mean'
    }).reset_index()
    
    # Renomear colunas
    metricas.columns = ['colaborador', 'atendimentos', 'tempo_medio', 'desvio_padrao', 'tempo_espera']
    
    # Converter tempos para minutos
    metricas['tempo_medio'] = metricas['tempo_medio'] / 60
    metricas['desvio_padrao'] = metricas['desvio_padrao'] / 60
    metricas['tempo_espera'] = metricas['tempo_espera'] / 60
    
    # Calcular média geral para comparação
    media_geral = metricas['tempo_medio'].mean()
    metricas['variacao_media'] = ((metricas['tempo_medio'] - media_geral) / media_geral * 100)
    
    return metricas

def criar_grafico_performance(metricas):
    """Cria gráfico de performance dos colaboradores"""
    # Ordenar por quantidade de atendimentos
    df = metricas.sort_values('atendimentos', ascending=True)
    
    # Criar figura com eixo secundário
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Adicionar barras de quantidade de atendimentos
    fig.add_trace(
        go.Bar(
            name='Quantidade de Atendimentos',
            x=df['atendimentos'],
            y=df['colaborador'],
            orientation='h',
            marker_color='lightblue'
        ),
        secondary_y=False
    )
    
    # Adicionar linha de tempo médio
    fig.add_trace(
        go.Scatter(
            name='Tempo Médio (min)',
            x=df['tempo_medio'],
            y=df['colaborador'],
            mode='markers',
            marker=dict(
                color=df['variacao_media'],
                colorscale='RdYlGn_r',
                size=10,
                showscale=True,
                colorbar=dict(title="Variação da Média (%)")
            )
        ),
        secondary_y=True
    )
    
    # Atualizar layout
    fig.update_layout(
        title="Performance por Colaborador",
        height=400 + (len(df) * 20),
        showlegend=True,
        xaxis_title="Quantidade de Atendimentos",
        yaxis_title="Colaborador"
    )
    
    fig.update_yaxes(title_text="Tempo Médio (min)", secondary_y=True)
    
    return fig

def mostrar_aba(dados, filtros):
    """Mostra a aba de Performance de Atendimento"""
    st.header("Performance de Atendimento")
    st.write("Análise da performance individual dos colaboradores")
    
    try:
        # Seleção do turno
        turno = st.selectbox(
            "Selecione o Turno:",
            ["Todos", "A", "B", "C"]
        )
        
        # Calcular métricas
        metricas = calcular_metricas_colaborador(dados, filtros, turno)
        
        # Exibir gráfico
        fig = criar_grafico_performance(metricas)
        st.plotly_chart(fig, use_container_width=True)
        
        # Top 10 Colaboradores
        st.subheader("🏆 Top 10 Colaboradores")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("#### Por Quantidade de Atendimentos")
            top_qtd = metricas.nlargest(10, 'atendimentos')
            for idx, row in top_qtd.iterrows():
                st.write(f"- {row['colaborador']}: {int(row['atendimentos'])} atendimentos")
        
        with col2:
            st.write("#### Por Tempo Médio de Atendimento")
            top_tempo = metricas.nsmallest(10, 'tempo_medio')
            for idx, row in top_tempo.iterrows():
                st.write(f"- {row['colaborador']}: {row['tempo_medio']:.1f} min")
        
        # Insights
        st.subheader("📊 Insights")
        with st.expander("Ver insights"):
            media_atend = metricas['atendimentos'].mean()
            media_tempo = metricas['tempo_medio'].mean()
            
            st.write("#### Principais Observações:")
            st.write(f"**Média de Atendimentos:** {media_atend:.1f}")
            st.write(f"**Tempo Médio de Atendimento:** {media_tempo:.1f} min")
            
            # Identificar outliers
            desvio_atend = metricas['atendimentos'].std()
            abaixo_media = metricas[metricas['atendimentos'] < (media_atend - desvio_atend)]
            
            if not abaixo_media.empty:
                st.write("\n**Colaboradores Abaixo da Média:**")
                for _, row in abaixo_media.iterrows():
                    st.write(f"- {row['colaborador']}: {int(row['atendimentos'])} atendimentos")
    
    except Exception as e:
        st.error("Erro ao gerar a aba de Performance de Atendimento")
        st.exception(e)