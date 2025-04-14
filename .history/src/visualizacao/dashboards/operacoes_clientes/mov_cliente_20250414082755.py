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
    """Calcula movimentação por cliente no período"""
    df = dados['base']
    
    # Debug log
    total_inicial = len(df)
    st.session_state['debug'] = {'total_inicial': total_inicial}
    
    # Aplicar filtros de data
    mask = (
        (df['retirada'].dt.date >= filtros[periodo]['inicio']) &
        (df['retirada'].dt.date <= filtros[periodo]['fim'])
    )
    df_filtrado = df[mask].copy()
    
    # Verificar se há dados após filtro de data
    if len(df_filtrado) == 0:
        return pd.DataFrame()
    
    # Aplicar filtros adicionais
    if filtros['cliente'] != ['Todos']:
        df_filtrado = df_filtrado[df_filtrado['CLIENTE'].isin(filtros['cliente'])]
    
    if filtros['operacao'] != ['Todas']:
        df_filtrado = df_filtrado[df_filtrado['OPERAÇÃO'].isin(filtros['operacao'])]
    
    if filtros['turno'] != ['Todos']:
        df_filtrado['turno'] = df_filtrado['retirada'].dt.hour.apply(
            lambda x: 'A' if 7 <= x < 15 else ('B' if 15 <= x < 23 else 'C')
        )
        df_filtrado = df_filtrado[df_filtrado['turno'].isin(filtros['turno'])]
    
    # Verificar dados após todos os filtros
    total_final = len(df_filtrado)
    st.session_state['debug']['total_final'] = total_final
    
    if total_final == 0:
        return pd.DataFrame()
    
    # Agregação dos dados
    movimentacao = df_filtrado.groupby('CLIENTE').agg({
        'id': 'count',
        'tpatend': ['mean', 'sum'],
        'tpesper': ['mean', 'sum'],
        'tempo_permanencia': ['mean', 'sum']
    }).reset_index()
    
    # Renomear colunas
    movimentacao.columns = [
        'cliente', 'quantidade', 
        'tempo_medio_atend', 'tempo_total_atend',
        'tempo_medio_espera', 'tempo_total_espera',
        'tempo_medio_perm', 'tempo_total_perm'
    ]
    
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
    
    # Identificar clientes notáveis
    maior_crescimento = df_comp.nlargest(1, 'variacao').iloc[0]
    maior_queda = df_comp.nsmallest(1, 'variacao').iloc[0]
    maior_volume = df_comp.nlargest(1, 'total').iloc[0]
    
    # Análise de concentração
    df_comp['perc_total'] = (df_comp['total'] / df_comp['total'].sum()) * 100
    top_clientes = df_comp.nlargest(3, 'total')
    concentracao_top3 = top_clientes['perc_total'].sum()

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Visão Geral")
        st.markdown(f"""
        - Total de atendimentos (P1): **{total_p1:,}**
        - Total de atendimentos (P2): **{total_p2:,}**
        - Variação geral: **{variacao_total:,.1f}%**
        """)
        
        st.subheader("👥 Concentração de Clientes")
        st.markdown(f"""
        - Top 3 clientes representam **{concentracao_top3:.1f}%** do volume total
        - Cliente mais volumoso: **{maior_volume['cliente']}**
          ({maior_volume['total']:,} atendimentos)
        """)

    with col2:
        st.subheader("📈 Variações Significativas")
        st.markdown(f"""
        - Maior crescimento: **{maior_crescimento['cliente']}**
          ({maior_crescimento['variacao']:,.1f}%)
        - Maior redução: **{maior_queda['cliente']}**
          ({maior_queda['variacao']:,.1f}%)
        """)
        
        st.subheader("💡 Análise e Recomendações")
        if concentracao_top3 > 50:
            st.markdown("""
            - **Atenção**: Alta concentração nos principais clientes
            - Considerar estratégias de diversificação da carteira
            """)
        if maior_queda['variacao'] < -20:
            st.markdown(f"""
            - Investigar redução significativa do cliente **{maior_queda['cliente']}**
            - Agendar reunião de acompanhamento
            """)

def mostrar_aba(dados, filtros):
    """Mostra a aba de Movimentação por Cliente"""
    st.header("Movimentação por Cliente")
    
    try:
        # Calculando movimentação para ambos períodos
        mov_p1 = calcular_movimentacao_por_periodo(dados, filtros, 'periodo1')
        mov_p2 = calcular_movimentacao_por_periodo(dados, filtros, 'periodo2')
        
        # Debug info - apenas durante desenvolvimento
        if 'debug' in st.session_state:
            with st.expander("Debug Info", expanded=False):
                st.write(st.session_state['debug'])
        
        # Verificar se há dados
        if mov_p1.empty and mov_p2.empty:
            st.warning("Nenhum registro encontrado com os filtros selecionados")
            st.info("Tente ajustar os filtros de data, cliente, operação ou turno")
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
        gerar_insights_cliente(mov_p1, mov_p2)
    
    except Exception as e:
        st.error(f"Erro ao mostrar aba: {str(e)}")
        st.exception(e)