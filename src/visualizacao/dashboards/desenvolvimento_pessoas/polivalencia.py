import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import plotly.graph_objects as go

def calcular_polivalencia(dados, filtros):
    """Calcula métricas de polivalência por colaborador"""
    df = dados['base']
    
    # Aplicar filtros de período
    mask = (
        (df['retirada'].dt.date >= filtros['periodo2']['inicio']) &
        (df['retirada'].dt.date <= filtros['periodo2']['fim'])
    )
    df_filtrado = df[mask]
    
    # Calcular métricas por colaborador
    metricas_colaborador = []
    
    for usuario in df_filtrado['usuário'].unique():
        df_user = df_filtrado[df_filtrado['usuário'] == usuario]
        
        # Métricas por operação
        ops_count = df_user['OPERAÇÃO'].value_counts()
        ops_tempo = df_user.groupby('OPERAÇÃO')['tpatend'].mean() / 60
        
        # Métricas por cliente
        clientes_count = df_user['CLIENTE'].value_counts()
        clientes_tempo = df_user.groupby('CLIENTE')['tpatend'].mean() / 60
        
        # Calcular turno predominante
        df_user['turno'] = df_user['inicio'].dt.hour.map(
            lambda x: 'TURNO A' if 6 <= x < 14 else ('TURNO B' if 14 <= x < 22 else 'TURNO C')
        )
        turno_pred = df_user['turno'].mode().iloc[0]
        
        # Calcular scores de polivalência
        score_ops = len(ops_count)  # Número de operações diferentes
        score_clientes = len(clientes_count)  # Número de clientes diferentes
        
        # Calcular distribuição de atendimentos
        distribuicao_ops = (ops_count / ops_count.sum() * 100).std()  # Desvio padrão da distribuição
        distribuicao_clientes = (clientes_count / clientes_count.sum() * 100).std()
        
        metricas_colaborador.append({
            'colaborador': usuario,
            'turno': turno_pred,
            'num_operacoes': score_ops,
            'num_clientes': score_clientes,
            'distribuicao_ops': distribuicao_ops,
            'distribuicao_clientes': distribuicao_clientes,
            'total_atendimentos': len(df_user),
            'tempo_medio': df_user['tpatend'].mean() / 60,
            'operacoes': ops_count.to_dict(),
            'clientes': clientes_count.to_dict(),
            'tempos_ops': ops_tempo.to_dict(),
            'tempos_clientes': clientes_tempo.to_dict()
        })
    
    return pd.DataFrame(metricas_colaborador)

def calcular_ranking_polivalencia(metricas_df):
    """Calcula o ranking de polivalência"""
    # Normalizar as métricas
    metricas_df['ops_norm'] = (metricas_df['num_operacoes'] - metricas_df['num_operacoes'].min()) / (metricas_df['num_operacoes'].max() - metricas_df['num_operacoes'].min())
    metricas_df['clientes_norm'] = (metricas_df['num_clientes'] - metricas_df['num_clientes'].min()) / (metricas_df['num_clientes'].max() - metricas_df['num_clientes'].min())
    metricas_df['vol_norm'] = (metricas_df['total_atendimentos'] - metricas_df['total_atendimentos'].min()) / (metricas_df['total_atendimentos'].max() - metricas_df['total_atendimentos'].min())
    
    # Calcular score final (média ponderada)
    metricas_df['score_polivalencia'] = (
        metricas_df['ops_norm'] * 0.4 +
        metricas_df['clientes_norm'] * 0.4 +
        metricas_df['vol_norm'] * 0.2
    )
    
    return metricas_df.sort_values('score_polivalencia', ascending=False)

def calcular_nivel_polivalencia_operacoes(dados_colab):
    """Calcula o nível de polivalência por operação considerando volume e tempo"""
    operacoes = dados_colab['operacoes']
    tempos_ops = dados_colab['tempos_ops']
    
    # Normalizar volumes (0 a 1)
    vol_max = max(operacoes.values())
    volumes_norm = {op: vol/vol_max for op, vol in operacoes.items()}
    
    # Normalizar tempos (inverso, pois menor tempo é melhor)
    tempo_max = max(tempos_ops.values())
    tempos_norm = {op: 1 - (tempo/tempo_max) for op, tempo in tempos_ops.items()}
    
    # Calcular score final (70% tempo, 30% volume)
    scores = {}
    for op in operacoes.keys():
        scores[op] = (0.7 * tempos_norm[op]) + (0.3 * volumes_norm[op])
    
    return scores

def calcular_nivel_polivalencia_clientes(dados_colab):
    """Calcula o nível de polivalência por cliente considerando volume e tempo"""
    clientes = dados_colab['clientes']
    tempos_clientes = dados_colab['tempos_clientes']
    
    # Normalizar volumes (0 a 1)
    vol_max = max(clientes.values())
    volumes_norm = {cli: vol/vol_max for cli, vol in clientes.items()}
    
    # Normalizar tempos (inverso, pois menor tempo é melhor)
    tempo_max = max(tempos_clientes.values())
    tempos_norm = {cli: 1 - (tempo/tempo_max) for cli, tempo in tempos_clientes.items()}
    
    # Calcular score final (70% tempo, 30% volume)
    scores = {}
    for cli in clientes.keys():
        scores[cli] = (0.7 * tempos_norm[cli]) + (0.3 * volumes_norm[cli])
    
    return scores

def mostrar_detalhes_colaborador(colaborador, metricas):
    """Mostra análise detalhada de um colaborador"""
    dados_colab = metricas[metricas['colaborador'] == colaborador].iloc[0]
    
    st.subheader(f"📊 Análise Detalhada - {colaborador}")
    
    # Métricas principais
    cols = st.columns(4)
    with cols[0]:
        st.metric("Ranking Geral", f"#{dados_colab.name + 1}")
    with cols[1]:
        st.metric("Score de Polivalência", f"{dados_colab['score_polivalencia']:.2f}")
    with cols[2]:
        st.metric("Operações", dados_colab['num_operacoes'])
    with cols[3]:
        st.metric("Clientes", dados_colab['num_clientes'])
    
    # Criar layout de duas colunas para os gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico radar para clientes
        scores_clientes = calcular_nivel_polivalencia_clientes(dados_colab)
        
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=list(scores_clientes.values()),
            theta=list(scores_clientes.keys()),
            fill='toself',
            name='Nível de Polivalência'
        ))
        
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1],
                    gridcolor="rgba(255, 255, 255, 0.1)",  # Grid mais suave
                    tickfont=dict(color="#cccccc")  # Cor dos números
                ),
                angularaxis=dict(
                    gridcolor="rgba(255, 255, 255, 0.1)",  # Grid mais suave
                    tickfont=dict(color="#cccccc")  # Cor dos rótulos
                ),
                bgcolor="rgba(32, 32, 32, 0.95)"  # Fundo escuro semi-transparente
            ),
            paper_bgcolor="rgba(0,0,0,0)",  # Fundo transparente
            plot_bgcolor="rgba(0,0,0,0)",   # Fundo transparente
            showlegend=False,
            title=dict(
                text="Perfil de Polivalência por Cliente",
                font=dict(color="#cccccc", size=16)
            ),
            height=500,  # Aumentado para 500
            margin=dict(t=50, b=50, l=30, r=30)  # Margens ajustadas
        )
        st.plotly_chart(fig_radar, use_container_width=True)
    
    with col2:
        # Gráfico de barras horizontal para operações
        scores_operacoes = calcular_nivel_polivalencia_operacoes(dados_colab)
        
        df_ops = pd.DataFrame({
            'Operação': list(scores_operacoes.keys()),
            'Score': list(scores_operacoes.values()),
            'Volume': list(dados_colab['operacoes'].values())
        }).sort_values('Score', ascending=True)
        
        fig_bars = go.Figure()
        fig_bars.add_trace(go.Bar(
            x=df_ops['Score'],
            y=df_ops['Operação'],
            orientation='h',
            marker=dict(
                color=df_ops['Score'],
                colorscale=['#E3F2FD', '#90CAF9', '#42A5F5', '#1E88E5', '#1565C0'],  # Tons de azul
                showscale=True,
                colorbar=dict(
                    title=dict(
                        text="Nível",
                        side="right"
                    ),
                    x=1.02
                )
            )
        ))
        
        fig_bars.update_layout(
            title=dict(
                text="Performance por Operação",
                font=dict(size=16)
            ),
            height=500,  # Aumentado para 500
            xaxis_title="Nível de Polivalência",
            yaxis=dict(title=""),
            margin=dict(t=50, b=50, l=30, r=30)  # Margens ajustadas
        )
        st.plotly_chart(fig_bars, use_container_width=True)

def mostrar_aba(dados, filtros):
    """Mostra a aba de análise de polivalência individual"""
    st.header(f"Análise de Polivalência Individual ({filtros['periodo2']['inicio'].strftime('%d/%m/%Y')} até {filtros['periodo2']['fim'].strftime('%d/%m/%Y')})")
    
    try:
        # Calcular métricas e ranking
        metricas = calcular_polivalencia(dados, filtros)
        ranking = calcular_ranking_polivalencia(metricas)
        
        # Filtros e seleção na ordem correta
        col1, col2, col3 = st.columns(3)
        
        with col1:
            colaborador_selecionado = st.selectbox(
                "Selecionar Colaborador",
                options=[""] + sorted(ranking['colaborador'].unique().tolist())
            )
            
        with col2:
            turno_filtro = st.selectbox(
                "Selecionar Turno",
                options=["Todos"] + sorted(ranking['turno'].unique().tolist())
            )
            
        with col3:
            cliente_filtro = st.selectbox(
                "Selecionar Cliente",
                options=["Todos"] + sorted(dados['base']['CLIENTE'].unique().tolist())
            )

        if not colaborador_selecionado:
            st.info("Selecione um colaborador para visualizar sua análise detalhada")
            return

        # Mostrar detalhes do colaborador selecionado
        mostrar_detalhes_colaborador(colaborador_selecionado, ranking)

    except Exception as e:
        st.error("Erro ao analisar dados de polivalência")
        st.exception(e)
