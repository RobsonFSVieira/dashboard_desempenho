import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from utils.tema import TemaDashboard  # Adicionada importação do TemaDashboard

def calcular_metricas_gerais(dados, filtros):
    """Calcula métricas gerais para o período selecionado"""
    df = dados['base']
    
    # Aplicar filtros de data para período 2 (mais recente)
    mask = (
        (df['retirada'].dt.date >= filtros['periodo2']['inicio']) &
        (df['retirada'].dt.date <= filtros['periodo2']['fim'])
    )
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
    fig = go.Figure()  # Usar go.Figure ao invés de px
    cores = TemaDashboard.get_cores_tema()
    
    # Agrupa dados por data
    df_diario = df.groupby(df['retirada'].dt.date).size().reset_index()
    df_diario.columns = ['data', 'quantidade']
    
    # Adiciona linha
    fig.add_trace(
        go.Scatter(
            x=df_diario['data'],
            y=df_diario['quantidade'],
            mode='lines+markers+text',
            name='Atendimentos',
            line=dict(color=cores['principal'], width=3),
            marker=dict(size=8),
            text=df_diario['quantidade'],
            textposition='top center',
            textfont=dict(size=14, color='white')
        )
    )
    
    # Layout específico
    fig.update_layout(
        title=dict(text=''),
        plot_bgcolor='#262730',
        paper_bgcolor='#262730',
        height=400,
        margin=dict(l=80, r=50, t=80, b=50, pad=10),
        xaxis=dict(
            showgrid=True,
            gridcolor='#404040',
            zeroline=False,
            tickfont=dict(size=14, color='white'),
            tickangle=45
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#404040',
            zeroline=False,
            tickfont=dict(size=14, color='white')
        ),
        font=dict(
            family="Helvetica Neue, Arial, sans-serif",
            size=14,
            color='white'
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor='#262730',
            font=dict(size=14, color='white')
        ),
        modebar=dict(
            bgcolor='rgba(0,0,0,0)',
            color='white',
            activecolor='white',
            remove=[
                'zoom', 'pan', 'select', 'lasso2d', 'zoomIn2d', 
                'zoomOut2d', 'autoScale2d', 'resetScale2d',
                'hoverClosestCartesian', 'hoverCompareCartesian',
                'toggleSpikelines'
            ]
        )
    )
    
    return fig

def criar_grafico_top_clientes(dados, filtros):
    """Cria gráfico dos top 10 clientes"""
    fig = go.Figure()
    cores = TemaDashboard.get_cores_tema()
    
    # Agrupa dados por cliente
    df_clientes = df.groupby('CLIENTE').size().reset_index()
    df_clientes.columns = ['cliente', 'quantidade']
    df_clientes = df_clientes.sort_values('quantidade', ascending=True).tail(10)
    
    # Adiciona barras
    fig.add_trace(
        go.Bar(
            x=df_clientes['quantidade'],
            y=df_clientes['cliente'],
            orientation='h',
            marker_color=cores['principal'],
            text=df_clientes['quantidade'],
            textposition='outside',
            textfont=dict(size=14, color='white')
        )
    )
    
    # Layout específico
    fig.update_layout(
        title=dict(text=''),
        plot_bgcolor='#262730',
        paper_bgcolor='#262730',
        height=400,
        margin=dict(l=200, r=100, t=80, b=50, pad=10),
        xaxis=dict(
            showgrid=True,
            gridcolor='#404040',
            zeroline=False,
            tickfont=dict(size=14, color='white')
        ),
        yaxis=dict(
            showgrid=False,
            tickfont=dict(size=14, color='white')
        ),
        font=dict(
            family="Helvetica Neue, Arial, sans-serif",
            size=14,
            color='white'
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor='#262730',
            font=dict(size=14, color='white')
        ),
        modebar=dict(
            bgcolor='rgba(0,0,0,0)',
            color='white',
            activecolor='white',
            remove=[
                'zoom', 'pan', 'select', 'lasso2d', 'zoomIn2d', 
                'zoomOut2d', 'autoScale2d', 'resetScale2d',
                'hoverClosestCartesian', 'hoverCompareCartesian',
                'toggleSpikelines'
            ]
        )
    )
    
    return fig

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
                f"{metricas['total_atendimentos']:,}",
                help="Número total de atendimentos no período"
            )
        
        with col2:
            st.metric(
                "Tempo Médio de Atendimento",
                f"{metricas['media_tempo_atendimento']:.1f} min",
                help="Tempo médio de atendimento no período"
            )
        
        with col3:
            st.metric(
                "Tempo Médio de Espera",
                f"{metricas['media_tempo_espera']:.1f} min",
                help="Tempo médio de espera em fila no período"
            )
        
        with col4:
            st.metric(
                "Tempo Médio de Permanência",
                f"{metricas['media_permanencia']:.1f} min",
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
        st.subheader("📊 Insights")
        with st.expander("Ver insights"):
            # Cálculo de insights baseados nos dados
            df = dados['base']
            hora_pico = df.groupby(df['retirada'].dt.hour)['id'].count().idxmax()
            
            st.write("#### Principais Observações:")
            st.write(f"- Horário de pico de atendimentos: {hora_pico}:00h")
            st.write(f"- Média diária de atendimentos: {metricas['total_atendimentos']/30:.0f}")
            
            if metricas['media_permanencia'] > filtros['meta_permanencia']:
                st.warning(f"⚠️ Tempo médio de permanência acima da meta de {filtros['meta_permanencia']} minutos")
    
    except Exception as e:
        st.error("Erro ao gerar a aba Geral")
        st.exception(e)