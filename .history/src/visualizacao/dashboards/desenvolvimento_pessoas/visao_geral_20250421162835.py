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
    # Pegar os 10 melhores em quantidade (maiores valores)
    top_10 = metricas.nlargest(10, 'qtd_atendimentos')
    # Ordenar do menor para o maior para exibição (invertido para mostrar maiores no topo)
    top_10 = top_10.sort_values('qtd_atendimentos', ascending=False)
    
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
        title={
            'text': 'Top 10 Colaboradores por Volume',
            'font': {'size': 20, 'color': 'white', 'family': 'Arial'}
        },
        height=450,  # Aumentado para 450
        showlegend=False,
        yaxis={
            'autorange': 'reversed',
            'tickfont': {'size': 14}  # Aumenta fonte dos labels do eixo Y
        },
        xaxis={
            'tickfont': {'size': 14}  # Aumenta fonte dos labels do eixo X
        },
        margin=dict(r=120, l=100, t=50, b=20)  # Ajuste fino das margens
    )

    # Aumenta o tamanho do texto e posiciona os rótulos dentro das barras
    fig.update_traces(
        textfont={'size': 14, 'color': 'black'},  # Fonte maior e preta
        textposition='inside',
    )
    
    return fig

def criar_grafico_tempo(metricas):
    """Cria gráfico dos 10 melhores tempos médios"""
    # Pegar os 10 melhores tempos (menores valores)
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
        title={
            'text': 'Top 10 Menores Tempos Médios',
            'font': {'size': 20, 'color': 'white', 'family': 'Arial'}
        },
        height=450,  # Aumentado para 450
        showlegend=False,
        yaxis={
            'autorange': 'reversed',
            'tickfont': {'size': 14}  # Aumenta fonte dos labels do eixo Y
        },
        xaxis={
            'tickfont': {'size': 14},  # Aumenta fonte dos labels do eixo X
            'title': {'text': 'Minutos', 'font': {'size': 14}}
        },
        margin=dict(r=120, l=100, t=50, b=20)  # Ajuste fino das margens
    )

    # Aumenta o tamanho do texto e posiciona os rótulos dentro das barras
    fig.update_traces(
        textfont={'size': 14, 'color': 'black'},  # Fonte maior e preta
        textposition='inside',
    )
    
    return fig

def criar_grafico_ociosidade(metricas):
    """Cria gráfico dos 10 menores tempos de ociosidade"""
    df = metricas.copy()
    
    # Calcular ociosidade
    ociosidade = []
    for _, row in df.iterrows():
        tempo_ocioso = (row['tempo_espera'] + row['tempo_medio']) / 2
        ociosidade.append({
            'colaborador': row['colaborador'],
            'tempo_ocioso': tempo_ocioso
        })
    
    df_ocio = pd.DataFrame(ociosidade)
    # Pegar os 10 menores tempos de ociosidade
    top_10 = df_ocio.nsmallest(10, 'tempo_ocioso')
    
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
        title={
            'text': 'Top 10 Menores Tempos de Ociosidade',
            'font': {'size': 20, 'color': 'white', 'family': 'Arial'}
        },
        height=450,  # Aumentado para 450
        showlegend=False,
        yaxis={
            'autorange': 'reversed',
            'tickfont': {'size': 14}  # Aumenta fonte dos labels do eixo Y
        },
        xaxis={
            'tickfont': {'size': 14},  # Aumenta fonte dos labels do eixo X
            'title': {'text': 'Minutos', 'font': {'size': 14}}
        },
        margin=dict(r=120, l=100, t=50, b=20)  # Ajuste fino das margens
    )

    # Aumenta o tamanho do texto e posiciona os rótulos dentro das barras
    fig.update_traces(
        textfont={'size': 14, 'color': 'black'},  # Fonte maior e preta
        textposition='inside',
    )
    
    return fig

def mostrar_aba(dados, filtros):
    """Mostra a aba de Visão Geral"""
    # Formatar período para exibição
    periodo = (f"{filtros['periodo2']['inicio'].strftime('%d/%m/%Y')} a "
              f"{filtros['periodo2']['fim'].strftime('%d/%m/%Y')}")
    
    st.header(f"Visão Geral de Performance ({periodo})")
    
    # Adicionar seção explicativa
    with st.expander("ℹ️ Como funciona?", expanded=False):
        st.markdown("""
        ### Cálculo de Performance
        
        O sistema avalia a performance dos colaboradores considerando 3 métricas principais:
        
        1. **Volume de Atendimentos (40%)**
           - Quantidade total de atendimentos realizados
           - Quanto maior o volume, melhor a pontuação
        
        2. **Tempo Médio de Atendimento (30%)**
           - Média de tempo gasto em cada atendimento
           - Quanto menor o tempo, melhor a pontuação
        
        3. **Tempo de Ociosidade (30%)**
           - Média entre tempo de espera e tempo de atendimento
           - Quanto menor a ociosidade, melhor a pontuação
        
        ### Cálculo do Score
        
        O score final é calculado através de uma média ponderada normalizada:
        - Volume: (atendimentos_colaborador / maior_volume) * 0.4
        - Tempo: (menor_tempo / tempo_colaborador) * 0.3
        - Ociosidade: (menor_ociosidade / ociosidade_colaborador) * 0.3
        
        ### Visualizações
        
        - **Gráficos de Performance**: Top 10 colaboradores em cada métrica
        - **Ranking dos 5 Melhores**: Considerando todas as métricas
        - **Pontos de Atenção**: Colaboradores abaixo da média
        - **Insights Gerais**: Estatísticas gerais da equipe
        """)
    
    try:
        # Adicionar filtros adicionais
        col1, col2, col3 = st.columns(3)
        
        with col1:
            turnos = ["Todos", "TURNO A", "TURNO B", "TURNO C"]
            turno = st.selectbox(
                "Selecione o Turno",
                options=turnos,
                key="visao_geral_turno"
            )
            
        with col2:
            clientes = ["Todos"] + sorted(dados['base']['CLIENTE'].unique().tolist())
            cliente = st.selectbox(
                "Selecione o Cliente",
                options=clientes,
                key="visao_geral_cliente"
            )

        with col3:
            # Obter lista de datas disponíveis no período
            mask_periodo = (
                (dados['base']['retirada'].dt.date >= filtros['periodo2']['inicio']) &
                (dados['base']['retirada'].dt.date <= filtros['periodo2']['fim'])
            )
            datas_disponiveis = sorted(dados['base'][mask_periodo]['retirada'].dt.date.unique())
            datas_opcoes = ["Todas"] + [data.strftime("%d/%m/%Y") for data in datas_disponiveis]
            
            data_selecionada = st.selectbox(
                "Selecione a Data",
                options=datas_opcoes,
                key="visao_geral_data"
            )
        
        # Processar data
        data_especifica = None
        if data_selecionada != "Todas":
            dia, mes, ano = map(int, data_selecionada.split('/'))
            data_especifica = pd.to_datetime(f"{ano}-{mes}-{dia}").date()
        
        # Filtros adicionais
        adicional_filters = {
            'turno': turno,
            'cliente': cliente,
            'data_especifica': data_especifica
        }
        
        # Aplicar filtros à base de dados
        df = dados['base'].copy()
        if turno != "Todos":
            df['turno'] = df['inicio'].dt.hour.map(
                lambda x: 'A' if 6 <= x < 14 else ('B' if 14 <= x < 22 else 'C')
            )
            df = df[df['turno'].map({'A': 'TURNO A', 'B': 'TURNO B', 'C': 'TURNO C'}) == turno]
            
        if cliente != "Todos":
            df = df[df['CLIENTE'] == cliente]
            
        if data_especifica:
            df = df[df['retirada'].dt.date == data_especifica]
        
        # Atualizar dados com filtros aplicados
        dados_filtrados = {'base': df}
        
        # Calcular métricas com dados filtrados
        metricas = calcular_performance(dados_filtrados, filtros)
        
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
        
        # Seção dos gráficos - 2 em cima, 1 embaixo
        st.markdown("### 📊 Performance dos Colaboradores")
        
        # Primeira linha com 2 gráficos
        col1, col2 = st.columns(2)
        
        with col1:
            fig_atend = criar_grafico_atendimentos(metricas)
            st.plotly_chart(fig_atend, use_container_width=True)
        
        with col2:
            fig_tempo = criar_grafico_tempo(metricas)
            st.plotly_chart(fig_tempo, use_container_width=True)
        
        # Segunda linha com 1 gráfico centralizado
        col = st.columns([0.1, 0.8, 0.1])[1]  # Usa coluna do meio com margens
        with col:
            fig_ocio = criar_grafico_ociosidade(metricas)
            st.plotly_chart(fig_ocio, use_container_width=True)

        # Análise Detalhada
        st.subheader("📊 Análise Detalhada")
        with st.expander("Ver análise", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("#### 🏆 Ranking dos 5 Melhores")
                st.write("*Score considera: 40% volume + 30% tempo médio + 30% ociosidade*")
                
                # Normalizar as métricas para criar um ranking composto
                df_rank = pd.DataFrame()
                df_rank['colaborador'] = metricas['colaborador']
                
                # Normalizar volume (maior é melhor)
                df_rank['rank_volume'] = metricas['qtd_atendimentos'] / metricas['qtd_atendimentos'].max()
                
                # Normalizar tempo médio (menor é melhor)
                df_rank['rank_tempo'] = metricas['tempo_medio'].min() / metricas['tempo_medio']
                
                # Normalizar ociosidade (menor é melhor)
                df_rank['rank_ocio'] = (metricas['tempo_espera'].min() + metricas['tempo_medio'].min()) / (metricas['tempo_espera'] + metricas['tempo_medio'])
                
                # Calcular score final (média ponderada)
                df_rank['score_final'] = (
                    df_rank['rank_volume'] * 0.4 +  # 40% peso volume
                    df_rank['rank_tempo'] * 0.3 +   # 30% peso tempo
                    df_rank['rank_ocio'] * 0.3      # 30% peso ociosidade
                ) * 100
                
                # Pegar top 5
                top_5 = df_rank.nlargest(5, 'score_final').reset_index(drop=True)  # Reset do índice
                
                # Mostrar ranking
                for idx, row in top_5.iterrows():
                    colaborador = metricas[metricas['colaborador'] == row['colaborador']].iloc[0]
                    posicao = ["🥇 1º", "🥈 2º", "🥉 3º", "4º", "5º"][idx]  # Medalhas para os 3 primeiros
                    st.markdown(f"""
                    **{posicao} Lugar - {row['colaborador']}**
                    - 🎯 Score: {row['score_final']:.1f}
                    - 📊 Volume: {colaborador['qtd_atendimentos']} atendimentos
                    - ⏱️ Tempo Médio: {colaborador['tempo_medio']:.1f} min
                    - ⌛ Ociosidade: {(colaborador['tempo_espera'] + colaborador['tempo_medio'])/2:.1f} min
                    ---
                    """)
                
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
            
            with col3:
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
