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

def criar_grafico_ranking(metricas):
    """Cria gráfico de ranking dos top 10 colaboradores"""
    top_10 = metricas.head(10)
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Quantidade de Atendimentos", "Tempo Médio de Atendimento"),
        specs=[[{"type": "bar"}, {"type": "bar"}]]
    )
    
    # Gráfico de quantidade de atendimentos
    fig.add_trace(
        go.Bar(
            x=top_10['colaborador'],
            y=top_10['qtd_atendimentos'],
            text=top_10['qtd_atendimentos'],
            textposition='auto',
            name="Atendimentos",
            marker_color='royalblue'
        ),
        row=1, col=1
    )
    
    # Gráfico de tempo médio
    fig.add_trace(
        go.Bar(
            x=top_10['colaborador'],
            y=top_10['tempo_medio'],
            text=top_10['tempo_medio'].round(1),
            textposition='auto',
            name="Tempo Médio (min)",
            marker_color='lightblue'
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        title="Top 10 Colaboradores por Performance",
        showlegend=True,
        height=500,
        xaxis_tickangle=-45,
        xaxis2_tickangle=-45
    )
    
    return fig

def criar_grafico_score(metricas):
    """Cria gráfico de score geral dos colaboradores"""
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=metricas['colaborador'],
        x=metricas['score'],
        orientation='h',
        text=metricas['score'].round(1),
        textposition='auto',
        marker_color=metricas['score'],
        marker_colorscale='RdYlGn',
        name="Score"
    ))
    
    fig.update_layout(
        title="Score de Performance dos Colaboradores",
        xaxis_title="Score (0-100)",
        yaxis_title="Colaborador",
        height=max(400, len(metricas) * 25)
    )
    
    return fig

def criar_grafico_top_atendimentos(dados, filtros):
    """Cria gráfico dos top 10 colaboradores por atendimentos"""
    df = dados['base']
    mask = (df['retirada'].dt.date >= filtros['periodo2']['inicio']) & 
           (df['retirada'].dt.date <= filtros['periodo2']['fim'])
    df = df[mask]

    df_atend = df.groupby('usuário')['id'].count().reset_index()
    df_atend.columns = ['colaborador', 'quantidade']
    df_atend = df_atend.nlargest(10, 'quantidade')

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df_atend['colaborador'],
        x=df_atend['quantidade'],
        orientation='h',
        text=df_atend['quantidade'],
        textposition='inside',
        marker_color='#1a5fb4'
    ))
    
    fig.update_layout(
        title='Top 10 Colaboradores por Volume',
        height=300,
        showlegend=False
    )
    return fig

def criar_grafico_tempo_medio(dados, filtros):
    """Cria gráfico dos 10 melhores tempos médios"""
    df = dados['base']
    mask = (df['retirada'].dt.date >= filtros['periodo2']['inicio']) & 
           (df['retirada'].dt.date <= filtros['periodo2']['fim'])
    df = df[mask]

    df_tempo = df.groupby('usuário')['tpatend'].mean().reset_index()
    df_tempo['tpatend'] = df_tempo['tpatend'] / 60  # Converter para minutos
    df_tempo = df_tempo.nsmallest(10, 'tpatend')  # Menores tempos = melhores

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df_tempo['usuário'],
        x=df_tempo['tpatend'],
        orientation='h',
        text=[f"{x:.1f} min" for x in df_tempo['tpatend']],
        textposition='inside',
        marker_color='#4dabf7'
    ))
    
    fig.update_layout(
        title='Top 10 Menores Tempos Médios',
        height=300,
        showlegend=False
    )
    return fig

def criar_grafico_ociosidade(dados, filtros):
    """Cria gráfico dos 10 menores tempos de ociosidade"""
    df = dados['base']
    mask = (df['retirada'].dt.date >= filtros['periodo2']['inicio']) & 
           (df['retirada'].dt.date <= filtros['periodo2']['fim'])
    df = df[mask]

    ociosidade = []
    for usuario in df['usuário'].unique():
        df_user = df[df['usuário'] == usuario].copy()
        df_user = df_user.sort_values('inicio')
        
        tempo_ocioso = 0
        for i in range(len(df_user)-1):
            intervalo = (df_user.iloc[i+1]['inicio'] - df_user.iloc[i]['fim']).total_seconds()
            if 0 < intervalo <= 7200:  # Entre 0 e 2 horas
                tempo_ocioso += intervalo
                
        if len(df_user) > 0:
            ociosidade.append({
                'colaborador': usuario,
                'tempo_ocioso': tempo_ocioso / (len(df_user) * 60)  # Média em minutos
            })

    df_ocio = pd.DataFrame(ociosidade)
    df_ocio = df_ocio.nsmallest(10, 'tempo_ocioso')

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df_ocio['colaborador'],
        x=df_ocio['tempo_ocioso'],
        orientation='h',
        text=[f"{x:.1f} min" for x in df_ocio['tempo_ocioso']],
        textposition='inside',
        marker_color='#ff6b6b'
    ))
    
    fig.update_layout(
        title='Top 10 Menor Ociosidade',
        height=300,
        showlegend=False
    )
    return fig

def mostrar_aba(dados, filtros):
    """Mostra a aba de Visão Geral"""
    st.header("Visão Geral de Performance")
    
    try:
        # Métricas principais
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_atendimentos = len(dados['base'])
            st.metric(
                "Total de Atendimentos",
                f"{total_atendimentos:,}",
                help="Número total de atendimentos no período"
            )
        
        with col2:
            tempo_medio = dados['base']['tpatend'].mean() / 60
            st.metric(
                "Tempo Médio",
                f"{tempo_medio:.1f} min",
                help="Tempo médio de atendimento"
            )
        
        with col3:
            total_colaboradores = dados['base']['usuário'].nunique()
            st.metric(
                "Total de Colaboradores",
                total_colaboradores,
                help="Número de colaboradores ativos"
            )

        # Seção dos três gráficos
        st.markdown("### 📊 Análise de Performance")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            fig_atend = criar_grafico_top_atendimentos(dados, filtros)
            st.plotly_chart(fig_atend, use_container_width=True)
        
        with col2:
            fig_tempo = criar_grafico_tempo_medio(dados, filtros)
            st.plotly_chart(fig_tempo, use_container_width=True)
        
        with col3:
            fig_ocio = criar_grafico_ociosidade(dados, filtros)
            st.plotly_chart(fig_ocio, use_container_width=True)

        # Análise Detalhada
        st.subheader("📊 Análise Detalhada")
        with st.expander("Ver análise", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("#### 🏆 Top 3 Colaboradores")
                for i, row in calcular_performance(dados, filtros).head(3).iterrows():
                    st.write(
                        f"**{i+1}º {row['colaborador']}**\n\n"
                        f"- Score: {row['score']:.1f}\n"
                        f"- Atendimentos: {row['qtd_atendimentos']}\n"
                        f"- Tempo Médio: {row['tempo_medio']:.1f} min"
                    )
            
            with col2:
                st.write("#### ⚠️ Pontos de Atenção")
                baixa_perf = calcular_performance(dados, filtros)[calcular_performance(dados, filtros)['score'] < calcular_performance(dados, filtros)['score'].mean()]
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
            metricas = calcular_performance(dados, filtros)
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
