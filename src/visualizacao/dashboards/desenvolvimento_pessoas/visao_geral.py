import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import unicodedata

def normalizar_nome(nome):
    """Normaliza o nome do usuário para evitar duplicações"""
    # Remove acentos e converte para maiúsculo
    nome = unicodedata.normalize('NFKD', nome).encode('ASCII', 'ignore').decode('ASCII').upper()
    # Remove espaços extras
    nome = ' '.join(nome.split())
    return nome

def calcular_performance(dados, filtros):
    """Calcula métricas de performance por colaborador"""
    df = dados['base'].copy()
    
    # Normalizar nomes dos usuários
    df['usuário_norm'] = df['usuário'].apply(normalizar_nome)
    
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
    
    # Calcular métricas por colaborador (agora usando nome normalizado)
    metricas = df_filtrado.groupby('usuário_norm').agg({
        'id': 'count',
        'tpatend': ['mean', 'std'],
        'tpesper': 'mean',
        'usuário': 'first'  # Mantém o nome original para exibição
    }).reset_index()
    
    # Renomear colunas
    metricas.columns = ['usuario_norm', 'qtd_atendimentos', 'tempo_medio', 'desvio_padrao', 'tempo_espera', 'colaborador']
    
    # Filtrar apenas colaboradores com mais de 15 atendimentos
    metricas = metricas[metricas['qtd_atendimentos'] >= 15]
    
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
        textfont={'size': 18, 'color': 'black', 'family': 'Arial Black'},  # Fonte maior e preta
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
        textfont={'size': 18, 'color': 'black', 'family': 'Arial Black'},  # Fonte maior e preta
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
        textfont={'size': 18, 'color': 'black', 'family': 'Arial Black'},  # Fonte maior e preta
        textposition='inside',
    )
    
    return fig

def mostrar_aba(dados, filtros_master):
    """Mostra a aba de Visão Geral"""
    # Formatar período para exibição
    periodo = (f"{filtros_master['periodo2']['inicio'].strftime('%d/%m/%Y')} a "
              f"{filtros_master['periodo2']['fim'].strftime('%d/%m/%Y')}")
    
    st.header(f"Visão Geral de Performance ({periodo})")
    
    # Seção explicativa
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
        # Aplicar filtros master primeiro
        df = dados['base'].copy()
        mask_master = (
            (df['retirada'].dt.date >= filtros_master['periodo2']['inicio']) &
            (df['retirada'].dt.date <= filtros_master['periodo2']['fim'])
        )
        
        # Filtrar clientes baseado no filtro master
        if 'cliente' in filtros_master and "Todos" not in filtros_master['cliente']:
            mask_master &= df['CLIENTE'].isin(filtros_master['cliente'])
            # Lista de clientes disponíveis após filtro master
            clientes_permitidos = sorted(filtros_master['cliente'])
        else:
            # Se não houver filtro master, usar todos os clientes
            clientes_permitidos = sorted(df[mask_master]['CLIENTE'].fillna('Não Informado').astype(str).unique().tolist())
            
        if 'operacao' in filtros_master and "Todas" not in filtros_master['operacao']:
            mask_master &= df['OPERAÇÃO'].isin(filtros_master['operacao'])
        
        df = df[mask_master]
        
        # Filtros locais
        col1, col2, col3 = st.columns(3)
        
        with col1:
            turnos = ["Todos", "TURNO A", "TURNO B", "TURNO C"]
            turno_local = st.selectbox(
                "Filtrar por Turno",
                options=turnos,
                key="visao_geral_turno_local"
            )
            
        with col2:
            # Usar apenas clientes permitidos pelo filtro master
            clientes = ["Todos"] + clientes_permitidos
            cliente_local = st.selectbox(
                "Filtrar por Cliente",
                options=clientes,
                key="visao_geral_cliente_local"
            )
        
        with col3:
            datas_disponiveis = sorted(dados['base']['retirada'].dt.date.unique())
            datas_opcoes = ["Todas"] + [data.strftime("%d/%m/%Y") for data in datas_disponiveis]
            data_local = st.selectbox(
                "Filtrar por Data",
                options=datas_opcoes,
                key="visao_geral_data_local"
            )

        # Aplicar filtros locais
        if turno_local != "Todos":
            df['turno'] = df['inicio'].dt.hour.map(
                lambda x: 'TURNO A' if 6 <= x < 14 else ('TURNO B' if 14 <= x < 22 else 'TURNO C')
            )
            df = df[df['turno'] == turno_local]
            
        if cliente_local != "Todos":
            df = df[df['CLIENTE'] == cliente_local]
            
        if data_local != "Todas":
            data_especifica = pd.to_datetime(data_local, format="%d/%m/%Y").date()
            df = df[df['retirada'].dt.date == data_especifica]
        
        # Atualizar dados filtrados
        dados_filtrados = {'base': df}
        
        # Calcular métricas com dados filtrados
        metricas = calcular_performance(dados_filtrados, filtros_master)
        
        # Mostrar métricas gerais
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Total de Colaboradores", 
                f"{len(metricas)} atendentes",
                help="Número de colaboradores ativos no período"
            )
        
        with col2:
            total_atend = metricas['qtd_atendimentos'].sum()
            st.metric(
                "Total de Atendimentos",
                f"{total_atend:,.0f} atendimentos".replace(",", "."),  # Formato brasileiro
                help="Total de atendimentos no período"
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
            
    except Exception as e:
        st.error("Erro ao gerar a visão geral")
        if st.session_state.debug:
            st.exception(e)
