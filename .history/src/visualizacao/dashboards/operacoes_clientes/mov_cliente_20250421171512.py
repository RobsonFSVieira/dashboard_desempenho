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
    """Calcula a movimentação de cada cliente no período especificado"""
    df = dados['base']
    
    # Validação inicial dos dados
    if df.empty:
        st.warning("DataFrame está vazio")
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
    
    # Criar uma cópia do DataFrame para não modificar o original
    df_filtrado = df.copy()
    
    # Converter datas para datetime se necessário
    if not pd.api.types.is_datetime64_any_dtype(df_filtrado['retirada']):
        df_filtrado['retirada'] = pd.to_datetime(df_filtrado['retirada'])
    
    # Aplicar filtros de data
    mask_data = (
        (df_filtrado['retirada'].dt.date >= filtros[periodo]['inicio']) &
        (df_filtrado['retirada'].dt.date <= filtros[periodo]['fim'])
    )
    df_filtrado = df_filtrado[mask_data]
    
    # Aplicar filtros adicionais
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
        
    if filtros['cliente'] != ['Todos']:
        df_filtrado = df_filtrado[df_filtrado['CLIENTE'].isin(filtros['cliente'])]
    
    # Se não houver dados após os filtros
    if len(df_filtrado) == 0:
        st.warning("Nenhum registro encontrado com os filtros selecionados")
        return pd.DataFrame()
    
    # Agrupar por cliente
    movimentacao = df_filtrado.groupby('CLIENTE')['id'].count().reset_index()
    movimentacao.columns = ['cliente', 'quantidade']
    
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
            on='cliente', 
            suffixes=('_p1', '_p2')
        )
        
        # Calcula total e variação percentual
        df_comp['total'] = df_comp['quantidade_p1'] + df_comp['quantidade_p2']
        df_comp['variacao'] = ((df_comp['quantidade_p2'] - df_comp['quantidade_p1']) / 
                              df_comp['quantidade_p1'] * 100)
        
        # Ordena por total decrescente (maiores volumes no topo)
        df_comp = df_comp.sort_values('total', ascending=True)  # ascending=True pois o eixo y é invertido
        
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
                return 16  # Tamanho fixo para todas as barras
            else:  # tipo == 'porcentagem'
                return 14  # Tamanho fixo para as porcentagens

        # Adiciona barras para período 1
        fig.add_trace(go.Bar(
            name=legenda_p1,
            y=df_comp['cliente'],
            x=df_comp['quantidade_p1'],
            orientation='h',
            text=df_comp['quantidade_p1'],
            textposition='inside',
            marker_color=cores_tema['primaria'],
            textfont={
                'size': df_comp['quantidade_p1'].apply(lambda x: calcular_tamanho_fonte(x, 'barra')),
                'color': '#ffffff',
                'family': 'Arial Black'
            },
            opacity=0.85
        ))
        
        # Adiciona barras para período 2
        fig.add_trace(go.Bar(
            name=legenda_p2,
            y=df_comp['cliente'],
            x=df_comp['quantidade_p2'],
            orientation='h',
            text=df_comp['quantidade_p2'],
            textposition='inside',
            marker_color=cores_tema['secundaria'],
            textfont={
                'size': df_comp['quantidade_p2'].apply(lambda x: calcular_tamanho_fonte(x, 'barra')),
                'color': '#000000',
                'family': 'Arial Black'
            },
            opacity=0.85
        ))

        # Calcula a posição total para as anotações de variação
        df_comp['posicao_total'] = df_comp['quantidade_p1'] + df_comp['quantidade_p2']
        
        # Adiciona anotações de variação percentual
        for i, row in df_comp.iterrows():
            cor = cores_tema['sucesso'] if row['variacao'] >= 0 else cores_tema['erro']
            
            fig.add_annotation(
                y=row['cliente'],
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
                'text': 'Comparativo de Movimentação por Cliente',
                'font': {'size': 16, 'color': cores_tema['texto']}
            },
            barmode='stack',
            bargap=0.15,
            bargroupgap=0.1,
            height=max(600, len(df_comp) * 45),  # Aumentado altura base e multiplicador
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
            margin=dict(l=20, r=160, t=80, b=40),  # Aumentado margens right, top e bottom
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor=cores_tema['fundo']
        )
        
        # Atualiza eixos com cores mais contrastantes
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
            title='Cliente',
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

def gerar_insights_cliente(mov_p1, mov_p2):
    """Gera insights sobre a movimentação dos clientes"""
    # Merge dos dados
    df_comp = pd.merge(
        mov_p1, mov_p2,
        on='cliente',
        suffixes=('_p1', '_p2')
    )
    df_comp['variacao'] = ((df_comp['quantidade_p2'] - df_comp['quantidade_p1']) / df_comp['quantidade_p1'] * 100)
    df_comp['total'] = df_comp['quantidade_p1'] + df_comp['quantidade_p2']

    # Cálculos principais
    total_p1 = df_comp['quantidade_p1'].sum()
    total_p2 = df_comp['quantidade_p2'].sum()
    variacao_total = ((total_p2 - total_p1) / total_p1 * 100)
    media_p1 = df_comp['quantidade_p1'].mean()
    media_p2 = df_comp['quantidade_p2'].mean()
    
    # 1. Visão Geral
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Indicadores Gerais")
        st.markdown(f"""
        ##### Volume Total
        - Período 1: **{total_p1:,}** atendimentos
        - Período 2: **{total_p2:,}** atendimentos
        - Variação: **{variacao_total:+.1f}%** {'📈' if variacao_total > 0 else '📉'}
        
        ##### Média por Cliente
        - Período 1: **{int(media_p1):,}** atendimentos
        - Período 2: **{int(media_p2):,}** atendimentos
        - Variação: **{((media_p2 - media_p1) / media_p1 * 100):+.1f}%**
        """)
    
    with col2:
        st.subheader("🔝 Clientes Destaque")
        top_clientes = df_comp.nlargest(3, 'total')
        
        for _, row in top_clientes.iterrows():
            var = ((row['quantidade_p2'] - row['quantidade_p1']) / row['quantidade_p1'] * 100)
            st.markdown(f"""
            - **{row['cliente']}**:
                - Total: **{int(row['total']):,}** atendimentos
                - Participação: **{(row['total']/(total_p1 + total_p2)*100):.1f}%**
                - Variação: **{var:+.1f}%** {'📈' if var > 0 else '📉'}
            """)
    
    # 2. Análise de Variações
    st.markdown("---")
    st.subheader("📊 Análise de Variações")
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("🔼 Maiores Crescimentos")
        crescimentos = df_comp.nlargest(3, 'variacao')
        for _, row in crescimentos.iterrows():
            aumento = row['quantidade_p2'] - row['quantidade_p1']
            st.markdown(f"""
            - **{row['cliente']}**:
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
            - **{row['cliente']}**:
                - Redução: **{row['variacao']:.1f}%** 📉
                - De {row['quantidade_p1']:,} para {row['quantidade_p2']:,}
                - Queda de **{reducao:,}** atendimentos
            """)
    
    # 3. Recomendações
    st.markdown("---")
    st.subheader("💡 Recomendações")
    col5, col6 = st.columns(2)
    
    with col5:
        st.markdown("#### Ações Imediatas")
        if variacao_total > 10:
            st.markdown(f"- ⚠️ Aumento significativo no volume total: **{variacao_total:+.1f}%**")
        st.markdown("""
        - Acompanhamento dos principais clientes
        - Análise das quedas significativas
        - Plano de retenção para clientes críticos
        """)

    with col6:
        st.markdown("#### Ações Preventivas")
        df_comp['perc_total'] = (df_comp['total'] / df_comp['total'].sum()) * 100
        concentracao_top3 = df_comp.nlargest(3, 'total')['perc_total'].sum()
        
        if concentracao_top3 > 50:
            st.markdown(f"- ⚠️ Alta concentração (**{concentracao_top3:.1f}%**) em 3 clientes")
        st.markdown("""
        - Diversificação da carteira
        - Desenvolvimento de novos clientes
        - Programa de fidelização
        """)

def mostrar_aba(dados, filtros):
    """Mostra a aba de Movimentação por Cliente"""
    st.header("Movimentação por Cliente")
    
    with st.expander("ℹ️ Como funciona?"):
        st.markdown("""
        ### Como analisamos a movimentação por cliente?

        1. **Contagem de Atendimentos**:
        - **Total**: Quantidade de senhas atendidas por cliente
        - **Períodos**: Comparativo entre dois intervalos selecionados
        - **Participação**: Percentual de cada cliente no volume total

        2. **Métricas Principais**:
        - **Volume Total**: Soma de todos os atendimentos
        - **Média por Cliente**: Volume médio de cada cliente
        - **Variação**: Diferença percentual entre períodos
            - 🟢 Variação positiva = Aumento no volume
            - 🔴 Variação negativa = Redução no volume

        3. **Análise de Concentração**:
        - 📈 Clientes com maior volume
        - 📉 Clientes com maior queda
        - ⚖️ Distribuição do volume

        4. **Indicadores**:
        - ✅ Crescimento equilibrado
        - ⚠️ Alta concentração em poucos clientes
        - 📊 Diversificação da carteira

        5. **Insights**:
        - 🎯 Clientes principais
        - ⚠️ Pontos de atenção
        - 💡 Recomendações estratégicas
        """)
    
    try:
        st.session_state['tema_atual'] = detectar_tema()
        
        mov_p1 = calcular_movimentacao_por_periodo(dados, filtros, 'periodo1')
        mov_p2 = calcular_movimentacao_por_periodo(dados, filtros, 'periodo2')
        
        if mov_p1.empty or mov_p2.empty:
            st.warning("Não há dados para exibir no período selecionado.")
            return
        
        fig = criar_grafico_comparativo(mov_p1, mov_p2, filtros)
        if fig:
            st.plotly_chart(
                fig, 
                use_container_width=True, 
                key=f"grafico_{st.session_state['tema_atual']}"
            )
            
        # Adiciona insights abaixo do gráfico
        st.markdown("---")
        st.subheader("📈 Análise Detalhada")
        with st.expander("Ver análise detalhada", expanded=True):
            gerar_insights_cliente(mov_p1, mov_p2)
    
    except Exception as e:
        st.error(f"Erro ao mostrar aba: {str(e)}")
        st.exception(e)