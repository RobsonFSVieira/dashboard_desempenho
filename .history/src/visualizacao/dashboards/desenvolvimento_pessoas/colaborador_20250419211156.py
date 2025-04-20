import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import timedelta

def analisar_colaborador(dados, filtros, colaborador):
    """Analisa dados de um colaborador específico"""
    df = dados['base']
    
    # Aplicar filtros de data
    mask = (
        (df['retirada'].dt.date >= filtros['periodo2']['inicio']) &
        (df['retirada'].dt.date <= filtros['periodo2']['fim'])
    )
    df_filtrado = df[mask & (df['usuário'] == colaborador)]
    
    # Métricas por operação
    metricas_op = df_filtrado.groupby('OPERAÇÃO').agg({
        'id': 'count',
        'tpatend': 'mean',
        'tpesper': 'mean'
    }).reset_index()
    
    # Converter tempos para minutos
    metricas_op['tpatend'] = metricas_op['tpatend'] / 60
    metricas_op['tpesper'] = metricas_op['tpesper'] / 60
    
    # Adicionar médias esperadas
    df_medias = dados['medias']
    metricas_op = pd.merge(
        metricas_op,
        df_medias[['OPERAÇÃO', 'Total Geral']],
        on='OPERAÇÃO',
        how='left'
    )
    
    # Calcular variação
    metricas_op['variacao'] = ((metricas_op['tpatend'] - metricas_op['Total Geral']) / 
                              metricas_op['Total Geral'] * 100)
    
    return metricas_op

def criar_grafico_operacoes(metricas_op):
    """Cria gráfico comparativo por operação"""
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Quantidade de Atendimentos", "Tempo Médio vs Meta"),
        specs=[[{"type": "bar"}, {"type": "bar"}]]
    )
    
    # Gráfico de quantidade
    fig.add_trace(
        go.Bar(
            x=metricas_op['OPERAÇÃO'],
            y=metricas_op['id'],
            name="Atendimentos",
            text=metricas_op['id'],
            textposition='auto',
            marker_color='royalblue'
        ),
        row=1, col=1
    )
    
    # Gráfico de tempo médio vs meta
    fig.add_trace(
        go.Bar(
            x=metricas_op['OPERAÇÃO'],
            y=metricas_op['tpatend'],
            name="Tempo Médio",
            text=metricas_op['tpatend'].round(1),
            textposition='auto',
            marker_color='lightblue'
        ),
        row=1, col=2
    )
    
    fig.add_trace(
        go.Scatter(
            x=metricas_op['OPERAÇÃO'],
            y=metricas_op['Total Geral'],
            name="Meta",
            mode='lines+markers',
            line=dict(color='red', dash='dash')
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        height=400,
        showlegend=True,
        title_text="Análise por Operação"
    )
    
    return fig

def criar_grafico_evolucao_diaria(dados, filtros, colaborador):
    """Cria gráfico de evolução diária"""
    df = dados['base']
    
    # Aplicar filtros de data
    mask = (
        (df['retirada'].dt.date >= filtros['periodo2']['inicio']) &
        (df['retirada'].dt.date <= filtros['periodo2']['fim'])
    )
    df_filtrado = df[mask & (df['usuário'] == colaborador)]
    
    # Agrupar por dia
    evolucao = df_filtrado.groupby(df_filtrado['retirada'].dt.date).agg({
        'id': 'count',
        'tpatend': 'mean'
    }).reset_index()
    
    evolucao['tpatend'] = evolucao['tpatend'] / 60
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Atendimentos por Dia", "Tempo Médio por Dia"),
        specs=[[{"type": "scatter"}, {"type": "scatter"}]]
    )
    
    fig.add_trace(
        go.Scatter(
            x=evolucao['retirada'],
            y=evolucao['id'],
            mode='lines+markers',
            name="Atendimentos",
            line=dict(color='royalblue')
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=evolucao['retirada'],
            y=evolucao['tpatend'],
            mode='lines+markers',
            name="Tempo Médio",
            line=dict(color='lightblue')
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        height=400,
        showlegend=True,
        title_text="Evolução Diária"
    )
    
    return fig

def mostrar_aba(dados, filtros):
    """Mostra a aba de análise individual do colaborador"""
    st.header("Análise Individual do Colaborador")
    
    try:
        # Seletor de colaborador
        colaboradores = sorted(dados['base']['usuário'].unique())
        colaborador = st.selectbox(
            "Selecione o Colaborador",
            options=colaboradores,
            help="Escolha um colaborador para análise detalhada"
        )
        
        if colaborador:
            # Análise do colaborador
            metricas_op = analisar_colaborador(dados, filtros, colaborador)
            
            # Métricas principais
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total de Atendimentos",
                    metricas_op['id'].sum()
                )
            
            with col2:
                tempo_medio = metricas_op['tpatend'].mean()
                st.metric(
                    "Tempo Médio",
                    f"{tempo_medio:.1f} min"
                )
            
            with col3:
                meta_media = metricas_op['Total Geral'].mean()
                variacao = ((tempo_medio - meta_media) / meta_media * 100)
                st.metric(
                    "Variação da Meta",
                    f"{variacao:+.1f}%",
                    delta_color="inverse"
                )
            
            with col4:
                tempo_espera = metricas_op['tpesper'].mean()
                st.metric(
                    "Tempo Médio de Espera",
                    f"{tempo_espera:.1f} min"
                )
            
            # Gráficos
            st.plotly_chart(criar_grafico_operacoes(metricas_op), use_container_width=True)
            st.plotly_chart(criar_grafico_evolucao_diaria(dados, filtros, colaborador), use_container_width=True)
            
            # Análise Detalhada
            st.subheader("📊 Análise Detalhada")
            with st.expander("Ver análise", expanded=True):
                # Performance por operação
                st.write("#### Performance por Operação")
                for _, row in metricas_op.iterrows():
                    status = "✅" if abs(row['variacao']) <= 10 else "⚠️"
                    st.write(
                        f"**{row['OPERAÇÃO']}** {status}\n\n"
                        f"- Atendimentos: {row['id']}\n"
                        f"- Tempo Médio: {row['tpatend']:.1f} min\n"
                        f"- Meta: {row['Total Geral']:.1f} min\n"
                        f"- Variação: {row['variacao']:+.1f}%"
                    )
                
                # Insights gerais
                st.write("#### 📈 Insights")
                
                # Identificar pontos fortes
                melhor_op = metricas_op.loc[metricas_op['variacao'].abs().idxmin()]
                st.write(
                    f"- Melhor performance em **{melhor_op['OPERAÇÃO']}** "
                    f"(variação de {melhor_op['variacao']:+.1f}%)"
                )
                
                # Identificar pontos de melhoria
                pior_op = metricas_op.loc[metricas_op['variacao'].abs().idxmax()]
                if abs(pior_op['variacao']) > 10:
                    st.write(
                        f"- Oportunidade de melhoria em **{pior_op['OPERAÇÃO']}** "
                        f"(variação de {pior_op['variacao']:+.1f}%)"
                    )
                
    except Exception as e:
        st.error("Erro ao analisar dados do colaborador")
        st.exception(e)
