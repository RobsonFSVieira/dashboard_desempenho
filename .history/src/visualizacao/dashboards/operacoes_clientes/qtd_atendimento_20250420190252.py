import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
from datetime import datetime

def detectar_tema():
    """Detecta se o tema atual é claro ou escuro"""
    try:
        theme_param = st.query_params.get('theme', None)
        if theme_param:
            return json.loads(theme_param)['base']
        else:
            return st.config.get_option('theme.base')
    except:
        return 'light'

def obter_cores_tema():
    """Retorna as cores baseadas no tema atual"""
    is_dark = detectar_tema() == 'dark'
    return {
        'primaria': '#1a5fb4' if is_dark else '#1864ab',
        'secundaria': '#4dabf7' if is_dark else '#83c9ff',
        'texto': '#ffffff' if is_dark else '#2c3e50',
        'fundo': '#0e1117' if is_dark else '#ffffff',
        'grid': '#2c3e50' if is_dark else '#e9ecef',
        'sucesso': '#2dd4bf' if is_dark else '#29b09d',
        'erro': '#ff6b6b' if is_dark else '#ff5757'
    }

def calcular_atendimentos_por_periodo(dados, filtros, periodo):
    """Calcula a quantidade de atendimentos por colaborador no período especificado"""
    df = dados['base']
    
    if df.empty:
        st.warning("Base de dados está vazia")
        return pd.DataFrame()
    
    # Aplicar filtros de data
    mask = (
        (df['retirada'].dt.date >= filtros[periodo]['inicio']) &
        (df['retirada'].dt.date <= filtros[periodo]['fim'])
    )
    df_filtrado = df[mask]
    
    # Aplicar filtros adicionais
    if filtros['cliente'] != ['Todos']:
        df_filtrado = df_filtrado[df_filtrado['CLIENTE'].isin(filtros['cliente'])]
        
    if filtros['operacao'] != ['Todas']:
        df_filtrado = df_filtrado[df_filtrado['OPERAÇÃO'].isin(filtros['operacao'])]
        
    if filtros['turno'] != ['Todos']:
        def get_turno(hour):
            if 7 <= hour < 15:
                return 'TURNO A'
            elif 15 <= hour < 23:
                return 'TURNO B'
            else:
                return 'TURNO C'
        df_filtrado = df_filtrado[df_filtrado['retirada'].dt.hour.apply(get_turno).isin(filtros['turno'])]
    
    # Agrupar por colaborador
    atendimentos = df_filtrado.groupby('COLABORADOR')['id'].count().reset_index()
    atendimentos.columns = ['colaborador', 'quantidade']
    
    return atendimentos

def criar_grafico_comparativo(dados_p1, dados_p2, filtros):
    try:
        # Merge dos dados
        df_comp = pd.merge(
            dados_p1, 
            dados_p2, 
            on='colaborador',
            suffixes=('_p1', '_p2'),
            how='outer'
        ).fillna(0)
        
        # Ordena por quantidade do período 2 (decrescente)
        df_comp = df_comp.sort_values('quantidade_p2', ascending=True)
        
        # Calcula variação percentual
        df_comp['variacao'] = ((df_comp['quantidade_p2'] - df_comp['quantidade_p1']) / 
                              df_comp['quantidade_p1'] * 100).replace([float('inf')], 100)
        
        cores_tema = obter_cores_tema()
        
        # Prepara legendas
        legenda_p1 = (f"Período 1 ({filtros['periodo1']['inicio'].strftime('%d/%m/%Y')} "
                      f"a {filtros['periodo1']['fim'].strftime('%d/%m/%Y')})")
        legenda_p2 = (f"Período 2 ({filtros['periodo2']['inicio'].strftime('%d/%m/%Y')} "
                      f"a {filtros['periodo2']['fim'].strftime('%d/%m/%Y')})")
        
        # Cria o gráfico
        fig = go.Figure()
        
        def calcular_tamanho_fonte(valor):
            return 16
        
        # Adiciona barras para período 1
        fig.add_trace(go.Bar(
            name=legenda_p1,
            y=df_comp['colaborador'],
            x=df_comp['quantidade_p1'],
            orientation='h',
            text=df_comp['quantidade_p1'].astype(int),
            textposition='inside',
            marker_color=cores_tema['primaria'],
            textfont={
                'size': df_comp['quantidade_p1'].apply(calcular_tamanho_fonte),
                'color': '#ffffff',
                'family': 'Arial Black'
            },
            opacity=0.85
        ))
        
        # Adiciona barras para período 2
        fig.add_trace(go.Bar(
            name=legenda_p2,
            y=df_comp['colaborador'],
            x=df_comp['quantidade_p2'],
            orientation='h',
            text=df_comp['quantidade_p2'].astype(int),
            textposition='inside',
            marker_color=cores_tema['secundaria'],
            textfont={
                'size': df_comp['quantidade_p2'].apply(calcular_tamanho_fonte),
                'color': '#000000',
                'family': 'Arial Black'
            },
            opacity=0.85
        ))
        
        # Adiciona anotações de variação percentual
        df_comp['posicao_total'] = df_comp['quantidade_p1'] + df_comp['quantidade_p2']
        for i, row in df_comp.iterrows():
            cor = cores_tema['sucesso'] if row['variacao'] >= 0 else cores_tema['erro']
            fig.add_annotation(
                y=row['colaborador'],
                x=row['posicao_total'],
                text=f"{row['variacao']:+.1f}%",
                showarrow=False,
                font=dict(color=cor, size=14),
                xanchor='left',
                yanchor='middle',
                xshift=10
            )
        
        # Atualiza layout
        fig.update_layout(
            title={
                'text': 'Comparativo de Quantidade de Atendimentos por Colaborador',
                'font': {'size': 16, 'color': cores_tema['texto']}
            },
            barmode='stack',
            bargap=0.15,
            bargroupgap=0.1,
            height=max(600, len(df_comp) * 45),
            font={'size': 12, 'color': cores_tema['texto']},
            showlegend=True,
            legend={
                'orientation': 'h',
                'yanchor': 'bottom',
                'y': 1.02,
                'xanchor': 'right',
                'x': 1
            },
            margin=dict(l=20, r=160, t=80, b=40),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor=cores_tema['fundo']
        )
        
        fig.update_xaxes(
            title='Quantidade de Atendimentos',
            title_font={'color': cores_tema['texto']},
            tickfont={'color': cores_tema['texto']},
            gridcolor=cores_tema['grid'],
            showline=True,
            linewidth=1,
            linecolor=cores_tema['grid'],
            zeroline=False
        )
        
        fig.update_yaxes(
            title='Colaborador',
            title_font={'color': cores_tema['texto']},
            tickfont={'color': cores_tema['texto']},
            gridcolor=cores_tema['grid'],
            showline=True,
            linewidth=1,
            linecolor=cores_tema['grid'],
            zeroline=False
        )
        
        return fig
    except Exception as e:
        st.error(f"Erro ao criar gráfico: {str(e)}")
        return None

def gerar_insights_atendimentos(atend_p1, atend_p2):
    """Gera insights sobre os atendimentos dos colaboradores"""
    # Merge dos dados
    df_comp = pd.merge(
        atend_p1, atend_p2,
        on='colaborador',
        suffixes=('_p1', '_p2')
    )
    df_comp['variacao'] = ((df_comp['quantidade_p2'] - df_comp['quantidade_p1']) / df_comp['quantidade_p1'] * 100)
    
    # Cálculos principais
    total_p1 = df_comp['quantidade_p1'].sum()
    total_p2 = df_comp['quantidade_p2'].sum()
    variacao_total = ((total_p2 - total_p1) / total_p1 * 100)
    
    # 1. Visão Geral
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Indicadores Gerais")
        media_p1 = df_comp['quantidade_p1'].mean()
        media_p2 = df_comp['quantidade_p2'].mean()
        
        st.markdown(f"""
        ##### Volume Total
        - Período 1: **{total_p1:,}** atendimentos
        - Período 2: **{total_p2:,}** atendimentos
        - Variação: **{variacao_total:+.1f}%** {'📈' if variacao_total > 0 else '📉'}
        
        ##### Média por Colaborador
        - Período 1: **{int(media_p1):,}** atendimentos
        - Período 2: **{int(media_p2):,}** atendimentos
        - Variação: **{((media_p2 - media_p1) / media_p1 * 100):+.1f}%**
        """)
    
    with col2:
        st.subheader("🔝 Colaboradores Destaque")
        top_colaboradores = df_comp.nlargest(3, 'quantidade_p2')
        
        for _, row in top_colaboradores.iterrows():
            var = ((row['quantidade_p2'] - row['quantidade_p1']) / row['quantidade_p1'] * 100)
            st.markdown(f"""
            - **{row['colaborador']}**:
                - Total P2: **{int(row['quantidade_p2']):,}** atendimentos
                - Participação P2: **{(row['quantidade_p2']/total_p2*100):.1f}%**
                - Variação: **{var:+.1f}%** {'📈' if var > 0 else '📉'}
            """)

    # 2. Análise de Variações
    st.markdown("---")
    st.subheader("📊 Análise de Variações")
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("🔼 Maiores Aumentos")
        aumentos = df_comp.nlargest(3, 'variacao')
        for _, row in aumentos.iterrows():
            aumento = row['quantidade_p2'] - row['quantidade_p1']
            st.markdown(f"""
            - **{row['colaborador']}**:
                - Crescimento: **{row['variacao']:+.1f}%** 📈
                - De {row['quantidade_p1']:,} para {row['quantidade_p2']:,}
                - Aumento de **{aumento:,}** atendimentos
            """)

    with col4:
        st.subheader("🔽 Maiores Reduções")
        reducoes = df_comp.nsmallest(3, 'variacao')
        for _, row in reducoes.iterrows():
            reducao = row['quantidade_p1'] - row['quantidade_p2']
            st.markdown(f"""
            - **{row['colaborador']}**:
                - Redução: **{row['variacao']:.1f}%** 📉
                - De {row['quantidade_p1']:,} para {row['quantidade_p2']:,}
                - Queda de **{reducao:,}** atendimentos
            """)

def mostrar_aba(dados, filtros):
    """Mostra a aba de Quantidade de Atendimento"""
    st.header("Quantidade de Atendimento")
    
    try:
        # Adiciona um key único que muda quando o tema muda
        st.session_state['tema_atual'] = detectar_tema()
        
        # Calcula atendimentos para os dois períodos
        atend_p1 = calcular_atendimentos_por_periodo(dados, filtros, 'periodo1')
        atend_p2 = calcular_atendimentos_por_periodo(dados, filtros, 'periodo2')
        
        if atend_p1.empty or atend_p2.empty:
            st.warning("Não há dados para exibir no período selecionado.")
            return
        
        # Cria e exibe o gráfico comparativo
        fig = criar_grafico_comparativo(atend_p1, atend_p2, filtros)
        if fig:
            st.plotly_chart(
                fig, 
                use_container_width=True, 
                key=f"grafico_atendimento_{st.session_state['tema_atual']}"
            )
            
        # Adiciona insights abaixo do gráfico
        st.markdown("---")
        st.subheader("📈 Análise Detalhada")
        with st.expander("Ver análise detalhada", expanded=True):
            gerar_insights_atendimentos(atend_p1, atend_p2)
    
    except Exception as e:
        st.error(f"Erro ao mostrar aba: {str(e)}")
        st.exception(e)
