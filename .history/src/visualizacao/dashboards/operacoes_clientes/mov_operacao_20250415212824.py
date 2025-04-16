import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json

def formatar_data(data):
    """Formata a data para o padrão dd/mm/aaaa"""
    if isinstance(data, datetime):
        return data.strftime('%d/%m/%Y')
    return data

def calcular_movimentacao_por_periodo(dados, filtros, periodo):
    """Calcula a movimentação de cada operação no período especificado"""
    df = dados['base']
    
    # Validação inicial dos dados
    if df.empty:
        st.warning("Base de dados está vazia")
        return pd.DataFrame()
    
    # Identificar período disponível nos dados
    data_mais_antiga = df['retirada'].dt.date.min()
    data_mais_recente = df['retirada'].dt.date.max()
    
    # Validar se as datas estão dentro do período disponível
    if (filtros[periodo]['inicio'] < data_mais_antiga or 
        filtros[periodo]['fim'] > data_mais_recente):
        st.error(f"""
            ⚠️ Período selecionado fora do intervalo disponível!
            
            Período disponível na base de dados:
            • De: {data_mais_antiga.strftime('%d/%m/%Y')}
            • Até: {data_mais_recente.strftime('%d/%m/%Y')}
            
            Período selecionado:
            • De: {filtros[periodo]['inicio'].strftime('%d/%m/%Y')}
            • Até: {filtros[periodo]['fim'].strftime('%d/%m/%Y')}
            
            Por favor, selecione datas dentro do período disponível.
        """)
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
        
    if filtros['turno'] != ['Todos']:
        def get_turno(hour):
            if 7 <= hour < 15:
                return 'TURNO A'
            elif 15 <= hour < 23:
                return 'TURNO B'
            else:
                return 'TURNO C'
        df_filtrado = df_filtrado[df_filtrado['retirada'].dt.hour.apply(get_turno).isin(filtros['turno'])]
        
    if filtros['operacao'] != ['Todas']:
        df_filtrado = df_filtrado[df_filtrado['OPERAÇÃO'].isin(filtros['operacao'])]
    
    # Se não houver dados após os filtros
    if len(df_filtrado) == 0:
        st.warning("Nenhum registro encontrado com os filtros selecionados")
        return pd.DataFrame()
    
    # Agrupar por operação
    movimentacao = df_filtrado.groupby('OPERAÇÃO')['id'].count().reset_index()
    movimentacao.columns = ['operacao', 'quantidade']
    
    return movimentacao

def detectar_tema():
    """Detecta se o tema atual é claro ou escuro"""
    # Verifica o tema através do query params do Streamlit
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
        'primaria': '#1a5fb4' if is_dark else '#1864ab',      # Azul mais escuro para período 1
        'secundaria': '#4dabf7' if is_dark else '#83c9ff',    # Azul mais claro para período 2
        'texto': '#ffffff' if is_dark else '#2c3e50',         # Cor do texto
        'fundo': '#0e1117' if is_dark else '#ffffff',         # Cor de fundo
        'grid': '#2c3e50' if is_dark else '#e9ecef',         # Cor da grade
        'sucesso': '#2dd4bf' if is_dark else '#29b09d',      # Verde
        'erro': '#ff6b6b' if is_dark else '#ff5757'          # Vermelho
    }

def criar_grafico_comparativo(dados_p1, dados_p2, filtros):
    try:
        # Merge e prepara dados
        df_comp = pd.merge(
            dados_p1, 
            dados_p2, 
            on='operacao',  # Usando operacao ao invés de cliente
            suffixes=('_p1', '_p2')
        )
        
        # Calcula total e variação percentual
        df_comp['total'] = df_comp['quantidade_p1'] + df_comp['quantidade_p2']
        df_comp['variacao'] = ((df_comp['quantidade_p2'] - df_comp['quantidade_p1']) / 
                              df_comp['quantidade_p1'] * 100)
        
        # Ordena por total crescente (menores no topo)
        df_comp = df_comp.sort_values('total', ascending=True)
        
        # Obtém cores do tema atual
        cores_tema = obter_cores_tema()
        
        # Prepara legendas com data formatada
        legenda_p1 = (f"Período 1 ({filtros['periodo1']['inicio'].strftime('%d/%m/%Y')} "
                      f"a {filtros['periodo1']['fim'].strftime('%d/%m/%Y')})")
        legenda_p2 = (f"Período 2 ({filtros['periodo2']['inicio'].strftime('%d/%m/%Y')} "
                      f"a {filtros['periodo2']['fim'].strftime('%d/%m/%Y')})")
        
        # Cria o gráfico
        fig = go.Figure()
        
        # Calcula o tamanho do texto baseado na largura das barras
        max_valor = max(df_comp['quantidade_p1'].max(), df_comp['quantidade_p2'].max())
        
        def calcular_tamanho_fonte(valor, tipo='barra'):
            # Define tamanhos fixos para melhor visibilidade
            if tipo == 'barra':
                return 16  # Aumentado para 16
            else:  # tipo == 'porcentagem'
                return 14

        # Adiciona barras para período 1
        fig.add_trace(go.Bar(
            name=legenda_p1,
            y=df_comp['operacao'],
            x=df_comp['quantidade_p1'],
            orientation='h',
            text=df_comp['quantidade_p1'],
            textposition='inside',
            marker_color=cores_tema['primaria'],
            textfont={
                'size': df_comp['quantidade_p1'].apply(lambda x: calcular_tamanho_fonte(x, 'barra')),
                'color': '#ffffff',
                'family': 'Arial Black'  # Adiciona fonte em negrito
            },
            opacity=0.85
        ))
        
        # Adiciona barras para período 2
        fig.add_trace(go.Bar(
            name=legenda_p2,
            y=df_comp['operacao'],
            x=df_comp['quantidade_p2'],
            orientation='h',
            text=df_comp['quantidade_p2'],
            textposition='inside',
            marker_color=cores_tema['secundaria'],
            textfont={
                'size': df_comp['quantidade_p2'].apply(lambda x: calcular_tamanho_fonte(x, 'barra')),
                'color': '#000000',
                'family': 'Arial Black'  # Adiciona fonte em negrito
            },
            opacity=0.85
        ))

        # Adiciona anotações de variação percentual
        df_comp['posicao_total'] = df_comp['quantidade_p1'] + df_comp['quantidade_p2']
        for i, row in df_comp.iterrows():
            cor = cores_tema['sucesso'] if row['variacao'] >= 0 else cores_tema['erro']
            
            fig.add_annotation(
                y=row['operacao'],
                x=row['posicao_total'],
                text=f"{row['variacao']:+.1f}%",
                showarrow=False,
                font=dict(color=cor, size=14),  # Tamanho fixo de 14
                xanchor='left',
                yanchor='middle',
                xshift=10
            )
        
        # Atualiza layout
        fig.update_layout(
            title={
                'text': 'Comparativo de Movimentação por Operação',  # Alterado título
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
                'x': 1,
                'font': {'color': cores_tema['texto']},
                'traceorder': 'normal',
                'itemsizing': 'constant'
            },
            margin=dict(l=20, r=160, t=80, b=40),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor=cores_tema['fundo']
        )
        
        # Atualiza eixos
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
            title='Operação',  # Alterado título do eixo
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

def gerar_insights_operacao(mov_p1, mov_p2):
    """Gera insights sobre a movimentação das operações"""
    # Merge dos dados
    df_comp = pd.merge(
        mov_p1, mov_p2,
        on='operacao',
        suffixes=('_p1', '_p2')
    )
    df_comp['variacao'] = ((df_comp['quantidade_p2'] - df_comp['quantidade_p1']) / df_comp['quantidade_p1'] * 100)
    df_comp['total'] = df_comp['quantidade_p1'] + df_comp['quantidade_p2']

    # Insights principais
    total_p1 = df_comp['quantidade_p1'].sum()
    total_p2 = df_comp['quantidade_p2'].sum()
    variacao_total = ((total_p2 - total_p1) / total_p1 * 100)
    
    # Operações com maior crescimento e queda
    maior_crescimento = df_comp.nlargest(1, 'variacao').iloc[0]
    maior_queda = df_comp.nsmallest(1, 'variacao').iloc[0]
    top_volume = df_comp.nlargest(3, 'total')
    # Operações mais movimentadas
    mais_movimentada = df_comp.nlargest(1, 'total').iloc[0]
    col1, col2 = st.columns(2)
    col1, col2 = st.columns(2)
    with col1:
    with col1:header("📈 Visão Geral")
        st.subheader("📊 Visão Geral")
        st.markdown(f"""
        - Volume total no período 1: **{total_p1:,}** atendimentos
        - Volume total no período 2: **{total_p2:,}** atendimentos()):,}**
        - Variação total: **{variacao_total:,.1f}%**
        """)# Período 2
        - Total de atendimentos: **{total_p2:,}**
        st.subheader("🔝 Destaques")(df_comp['quantidade_p2'].mean()):,}**
        st.markdown(f""": **{variacao_total:+.1f}%** {'📈' if variacao_total > 0 else '📉'}
        - Operação mais movimentada: **{mais_movimentada['operacao']}** 
          (total de {mais_movimentada['total']:,} atendimentos)
        """)2:
        st.subheader("🔝 Maiores Volumes")
    with col2: row in top_volume.iterrows():
        st.subheader("📈 Maiores Variações")ow['quantidade_p1']) / row['quantidade_p1'] * 100)
        st.markdown(f"""f"""
        - Maior crescimento: **{maior_crescimento['operacao']}** 
          ({maior_crescimento['variacao']:,.1f}%)* atendimentos
        - Maior queda: **{maior_queda['operacao']}** var > 0 else '📉'}
          ({maior_queda['variacao']:,.1f}%)tal']/(total_p1 + total_p2)*100):.1f}%**
        """)""")
        
        # Recomendações baseadas nos dados
        st.subheader("💡 Recomendações")
        if maior_queda['variacao'] < -20:")
            st.markdown(f"""2)
            - Investigar a queda significativa em **{maior_queda['operacao']}**
            - Verificar possíveis causas: demanda, recursos, processos
            """)ader("🔼 Maiores Crescimentos")
        if maior_crescimento['variacao'] > 50:():
            st.markdown(f"""
            - Analisar o sucesso de **{maior_crescimento['operacao']}**
            - Considerar aplicar práticas bem-sucedidas em outras operações
            """)- De {row['quantidade_p1']:,} para {row['quantidade_p2']:,}
                - Aumento de **{row['quantidade_p2'] - row['quantidade_p1']:,}** atendimentos
def mostrar_aba(dados, filtros):
    """Mostra a aba de Movimentação por Operação"""
    st.header("Movimentação por Operação")
        st.subheader("🔽 Maiores Reduções")
    try:for _, row in top_queda.iterrows():
        # Adiciona um key único que muda quando o tema muda
        st.session_state['tema_atual'] = detectar_tema()
                - Redução: **{row['variacao']:.1f}%** 📉
        # Calcula movimentação para os dois períodosrow['quantidade_p2']:,}
        mov_p1 = calcular_movimentacao_por_periodo(dados, filtros, 'periodo1') atendimentos
        mov_p2 = calcular_movimentacao_por_periodo(dados, filtros, 'periodo2')
        
        if mov_p1.empty or mov_p2.empty:
            st.warning("Não há dados para exibir no período selecionado.")
            return💡 Recomendações")
        , col6 = st.columns(2)
        # Cria e exibe o gráfico comparativo
        fig = criar_grafico_comparativo(mov_p1, mov_p2, filtros)
        if fig:down("#### Ações Imediatas")
            st.plotly_chart(riacao'] < -20):
                fig, _criticas = top_queda[top_queda['variacao'] < -20]['operacao'].tolist()
                use_container_width=True, 
                key=f"grafico_operacao_{st.session_state['tema_atual']}"
            )   {', '.join(f'**{op}**' for op in operacoes_criticas)}
            - Avaliar recursos e processos
        # Adiciona insights abaixo do gráfico
        st.markdown("---")
        st.subheader("📊 Análise Detalhada")
        with st.expander("Ver análise detalhada", expanded=True):        st.markdown("""
            gerar_insights_operacao(mov_p1, mov_p2)riações bruscas
    
    except Exception as e:istribuição de recursos


        st.exception(e)        st.error(f"Erro ao mostrar aba: {str(e)}")            """)

    with col6:
        st.markdown("#### Ações Preventivas")
        if any(top_crescimento['variacao'] > 50):
            ops_sucesso = top_crescimento[top_crescimento['variacao'] > 50]['operacao'].tolist()
            st.markdown(f"""
            - 🌟 Replicar práticas de sucesso:
                {', '.join(f'**{op}**' for op in ops_sucesso)}
            - Padronizar processos eficientes
            - Implementar melhorias contínuas
            """)
        else:
            st.markdown("""
            - Planejar capacidade futura
            - Otimizar processos existentes
            - Preparar para crescimento
            """)

def mostrar_aba(dados, filtros):
    """Mostra a aba de Movimentação por Operação"""
    st.header("Movimentação por Operação")
    
    try:
        # Adiciona um key único que muda quando o tema muda
        st.session_state['tema_atual'] = detectar_tema()
        
        # Calcula movimentação para os dois períodos
        mov_p1 = calcular_movimentacao_por_periodo(dados, filtros, 'periodo1')
        mov_p2 = calcular_movimentacao_por_periodo(dados, filtros, 'periodo2')
        
        if mov_p1.empty or mov_p2.empty:
            st.warning("Não há dados para exibir no período selecionado.")
            return
        
        # Cria e exibe o gráfico comparativo
        fig = criar_grafico_comparativo(mov_p1, mov_p2, filtros)
        if fig:
            st.plotly_chart(
                fig, 
                use_container_width=True, 
                key=f"grafico_operacao_{st.session_state['tema_atual']}"
            )
            
        # Adiciona insights abaixo do gráfico
        st.markdown("---")
        gerar_insights_operacao(mov_p1, mov_p2)
    
    except Exception as e:
        st.error(f"Erro ao mostrar aba: {str(e)}")
        st.exception(e)