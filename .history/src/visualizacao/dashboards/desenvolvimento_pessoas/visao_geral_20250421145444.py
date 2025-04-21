import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def calcular_performance(dados, filtros):
    """Calcula métricas de performance por colaborador"""
    df = dados['base']
    
    # Aplicar filtros de data
    mask = (
        (df['retirada'].dt.date >= filtros['periodo2']['inicio']) &
        (df['retirada'].dt.date <= filtros['periodo2']['fim'])
    )
    
    # Aplicar filtros adicionais se existirem
    if filtros['turno'] != ['Todos']:
        turno_map = {'TURNO A': 'A', 'TURNO B': 'B', 'TURNO C': 'C'}
        df['turno'] = df['inicio'].dt.hour.map(
            lambda x: 'A' if 6 <= x < 14 else ('B' if 14 <= x < 22 else 'C')
        )
        turnos = [turno_map[t] for t in filtros['turno'] if t in turno_map]
        mask &= df['turno'].isin(turnos)
    
    df_filtrado = df[mask]
    
    # Calcular métricas por colaborador
    metricas = df_filtrado.groupby('usuário').agg({
        'id': 'count',
        'tpatend': ['mean', 'std'],
        'tpesper': 'mean'
    }).reset_index()
    
    # Renomear colunas
    metricas.columns = ['colaborador', 'qtd_atendimentos', 'tempo_medio', 'desvio_padrao', 'tempo_espera']
    
    # Converter para minutos
    metricas['tempo_medio'] = metricas['tempo_medio'] / 60
    metricas['tempo_espera'] = metricas['tempo_espera'] / 60
    
    # Calcular score de performance (normalizado)
    max_atend = metricas['qtd_atendimentos'].max()
    min_tempo = metricas['tempo_medio'].min()
    
    metricas['score'] = (
        (metricas['qtd_atendimentos'] / max_atend * 0.7) + 
        (min_tempo / metricas['tempo_medio'] * 0.3)
    ) * 100
    
    return metricas.sort_values('score', ascending=False)

def criar_grafico_atendimentos(metricas):
    """Cria gráfico dos top 10 colaboradores por atendimentos"""
    # Pegar os 10 melhores em quantidade
    top_10 = metricas.nlargest(10, 'qtd_atendimentos')
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=top_10['colaborador'],
        x=top_10['qtd_atendimentos'],
        orientation='h',
        text=top_10['qtd_atendimentos'],
        textposition='inside',
        marker_color='#1a5fb4',
        name='Quantidade'
    ))
    
    fig.update_layout(
        title='Top 10 Colaboradores por Volume',
        height=300,
        showlegend=False
    )
    return fig

def criar_grafico_tempo(metricas):
    """Cria gráfico dos 10 melhores tempos médios"""
    # Pegar os 10 melhores tempos (menores)
    top_10 = metricas.nsmallest(10, 'tempo_medio')
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=top_10['colaborador'],
        x=top_10['tempo_medio'],
        orientation='h',
        text=[f"{x:.1f} min" for x in top_10['tempo_medio']],
        textposition='inside',
        marker_color='#4dabf7',
        name='Tempo Médio'
    ))
    
    fig.update_layout(
        title='Top 10 Menores Tempos Médios',
        height=300,
        showlegend=False
    )
    return fig

def criar_grafico_score(metricas):
    """Cria gráfico dos 10 melhores scores"""
    # Pegar os 10 melhores scores
    top_10 = metricas.nlargest(10, 'score')
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=top_10['colaborador'],
        x=top_10['score'],
        orientation='h',
        text=[f"{x:.1f}%" for x in top_10['score']],
        textposition='inside',
        marker_color='#ff6b6b',
        name='Score'
    ))
    
    fig.update_layout(
        title='Top 10 Melhores Scores',
        height=300,
        showlegend=False
    )
    return fig

def criar_grafico_ociosidade(metricas):
    """Cria gráfico dos 10 menores tempos de ociosidade"""
    # Pegar os 10 menores tempos de ociosidade
    top_10 = metricas.nsmallest(10, 'tempo_ocioso')
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=top_10['colaborador'],
        x=top_10['tempo_ocioso'],
        orientation='h',
        text=[f"{x:.1f} min" for x in top_10['tempo_ocioso']],
        textposition='inside',
        marker_color='#ff6b6b',
        name='Ociosidade'
    ))
    
    fig.update_layout(
        title='Top 10 Menor Tempo de Ociosidade', # Título corrigido
        height=300,
        showlegend=False
    )
    return fig

def mostrar_aba(dados, filtros):
    """Mostra a aba de Visão Geral"""
    st.header("Visão Geral de Performance")
    
    try:
        # Calcular métricas de performance
        metricas = calcular_performance(dados, filtros)
        
        # Mostrar métricas gerais
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Total de Colaboradores",
                len(metricas),
                help="Número de colaboradores ativos no período"
            )
        
        with col2:
            media_atend = metricas['qtd_atendimentos'].mean()
            st.metric(
                "Média de Atendimentos",
                f"{media_atend:.1f}",
                help="Média de atendimentos por colaborador"
            )
        
        with col3:
            media_tempo = metricas['tempo_medio'].mean()
            st.metric(
                "Tempo Médio de Atendimento",
                f"{media_tempo:.1f} min",
                help="Tempo médio de atendimento por colaborador"
            )
        
        # Seção dos três gráficos
        st.markdown("### 📊 Performance dos Colaboradores")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            fig_atend = criar_grafico_atendimentos(metricas)
            st.plotly_chart(fig_atend, use_container_width=True)
        
        with col2:
            fig_tempo = criar_grafico_tempo(metricas)
            st.plotly_chart(fig_tempo, use_container_width=True)
        
        with col3:
            fig_score = criar_grafico_score(metricas)
            st.plotly_chart(fig_score, use_container_width=True)

        # Análise Detalhada
        st.subheader("📊 Análise Detalhada")
        with st.expander("Ver análise", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("#### 🏆 Top 3 Colaboradores")
                for i, row in metricas.head(3).iterrows():
                    st.write(
                        f"**{i+1}º {row['colaborador']}**\n\n"
                        f"- Score: {row['score']:.1f}\n"
                        f"- Atendimentos: {row['qtd_atendimentos']}\n"
                        f"- Tempo Médio: {row['tempo_medio']:.1f} min"
                    )
            
            with col2:
                st.write("#### ⚠️ Pontos de Atenção")
                baixa_perf = metricas[metricas['score'] < metricas['score'].mean()]
                if not baixa_perf.empty:
                    for _, row in baixa_perf.head(3).iterrows():
                        st.write(
                            f"**{row['colaborador']}**\n\n"
                            f"- Score: {row['score']:.1f}\n"
                            f"- Atendimentos: {row['qtd_atendimentos']}\n"
                            f"- Tempo Médio: {row['tempo_medio']:.1f} min"
                        )
            
            # Insights gerais
            st.write("#### 📈 Insights Gerais")
            st.write(
                f"- Média geral de score: {metricas['score'].mean():.1f}\n"
                f"- Desvio padrão do score: {metricas['score'].std():.1f}\n"
                f"- {len(metricas[metricas['score'] > metricas['score'].mean()])} "
                f"colaboradores acima da média\n"
                f"- {len(metricas[metricas['score'] < metricas['score'].mean()])} "
                f"colaboradores abaixo da média"
            )
            
    except Exception as e:
        st.error("Erro ao gerar a visão geral")
        st.exception(e)
