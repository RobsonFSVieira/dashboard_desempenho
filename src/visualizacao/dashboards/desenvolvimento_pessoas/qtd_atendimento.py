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

def calcular_atendimentos_por_periodo(dados, filtros, periodo, adicional_filters=None):
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
    if adicional_filters:
        if adicional_filters['colaborador'] != "Todos":
            df_filtrado = df_filtrado[df_filtrado['usuário'] == adicional_filters['colaborador']]
        
        if adicional_filters['turno'] != "Todos":
            # Mapear hora para turno
            df_filtrado['turno'] = df_filtrado['inicio'].dt.hour.map(
                lambda x: 'TURNO A' if 6 <= x < 14 else ('TURNO B' if 14 <= x < 22 else 'TURNO C')
            )
            df_filtrado = df_filtrado[df_filtrado['turno'] == adicional_filters['turno']]
        
        if adicional_filters['cliente'] != "Todos":
            df_filtrado = df_filtrado[df_filtrado['CLIENTE'] == adicional_filters['cliente']]
            
        if adicional_filters['data_especifica']:
            df_filtrado = df_filtrado[df_filtrado['retirada'].dt.date == adicional_filters['data_especifica']]
    
    # Agrupar por colaborador usando a coluna correta
    atendimentos = df_filtrado.groupby('usuário')['id'].count().reset_index()
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
        
        # Adiciona barras para período 1
        fig.add_trace(go.Bar(
            name=legenda_p1,
            y=df_comp['colaborador'],
            x=df_comp['quantidade_p1'],
            orientation='h',
            text=df_comp['quantidade_p1'].astype(int),
            textposition='inside',
            marker_color=cores_tema['primaria'],
            textfont={'color': '#ffffff', 'size': 16},
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
            textfont={'color': '#000000', 'size': 16},
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
                'x': 1,
                'traceorder': 'normal'  # Define ordem normal para mostrar Período 1 primeiro
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
    try:
        # Merge dos dados
        df_insights = pd.merge(
            atend_p1, 
            atend_p2, 
            on='colaborador',
            suffixes=('_p1', '_p2'),
            how='outer'
        ).fillna(0)
        
        # Calcula variação percentual
        df_insights['variacao'] = ((df_insights['quantidade_p2'] - df_insights['quantidade_p1']) / 
                                  df_insights['quantidade_p1'] * 100).replace([float('inf')], 100)
        
        # Criar 4 colunas principais
        col_perf1, col_perf2, col_perf3, col_insights = st.columns([0.25, 0.25, 0.25, 0.25])
        
        # Dividir colaboradores em 3 partes
        tamanho_parte = len(df_insights) // 3
        resto = len(df_insights) % 3
        indices = [
            (0, tamanho_parte + (1 if resto > 0 else 0)),
            (tamanho_parte + (1 if resto > 0 else 0), 2*tamanho_parte + (2 if resto > 1 else 1 if resto > 0 else 0)),
            (2*tamanho_parte + (2 if resto > 1 else 1 if resto > 0 else 0), len(df_insights))
        ]

        # Estilo CSS para os boxes
        st.markdown("""
            <style>
                .success-box { 
                    background-color: rgba(0,255,0,0.1);
                    padding: 10px;
                    border-radius: 5px;
                }
                .warning-box { 
                    background-color: rgba(255,0,0,0.1);
                    padding: 10px;
                    border-radius: 5px;
                    margin-top: 10px;
                }
            </style>
        """, unsafe_allow_html=True)

        # Primeira coluna de performance
        with col_perf1:
            st.write("#### Performance (1/3)")
            df_parte = df_insights.iloc[indices[0][0]:indices[0][1]]
            for _, row in df_parte.iterrows():
                status = "✅" if row['variacao'] > 0 else "⚠️"
                st.write(
                    f"**{row['colaborador']}** {status}\n\n"
                    f"- P1: {int(row['quantidade_p1'])}\n"
                    f"- P2: {int(row['quantidade_p2'])}\n"
                    f"- Variação: {row['variacao']:+.1f}%"
                )

        # Segunda coluna de performance
        with col_perf2:
            st.write("#### Performance (2/3)")
            df_parte = df_insights.iloc[indices[1][0]:indices[1][1]]
            for _, row in df_parte.iterrows():
                status = "✅" if row['variacao'] > 0 else "⚠️"
                st.write(
                    f"**{row['colaborador']}** {status}\n\n"
                    f"- P1: {int(row['quantidade_p1'])}\n"
                    f"- P2: {int(row['quantidade_p2'])}\n"
                    f"- Variação: {row['variacao']:+.1f}%"
                )

        # Terceira coluna de performance
        with col_perf3:
            st.write("#### Performance (3/3)")
            df_parte = df_insights.iloc[indices[2][0]:indices[2][1]]
            for _, row in df_parte.iterrows():
                status = "✅" if row['variacao'] > 0 else "⚠️"
                st.write(
                    f"**{row['colaborador']}** {status}\n\n"
                    f"- P1: {int(row['quantidade_p1'])}\n"
                    f"- P2: {int(row['quantidade_p2'])}\n"
                    f"- Variação: {row['variacao']:+.1f}%"
                )

        # Coluna de insights
        with col_insights:
            st.write("#### 📈 Insights")
            
            # Melhor performance
            melhor = df_insights.loc[df_insights['variacao'].idxmax()]
            st.markdown(
                f"<div class='success-box'>"
                f"<b>🎯 Melhor Performance</b><br>"
                f"{melhor['colaborador']}<br>"
                f"Variação: {melhor['variacao']:+.1f}%"
                f"</div>",
                unsafe_allow_html=True
            )
            
            # Oportunidade de melhoria
            pior = df_insights.loc[df_insights['variacao'].idxmin()]
            st.markdown(
                f"<div class='warning-box'>"
                f"<b>⚠️ Oportunidade de Melhoria</b><br>"
                f"{pior['colaborador']}<br>"
                f"Variação: {pior['variacao']:+.1f}%"
                f"</div>",
                unsafe_allow_html=True
            )

    except Exception as e:
        st.error(f"Erro ao gerar insights: {str(e)}")

def mostrar_aba(dados, filtros):
    """Mostra a aba de Quantidade de Atendimento"""
    # Aplicar filtros master primeiro
    df = dados['base'].copy()
    mask_master = (
        (df['retirada'].dt.date >= filtros['periodo2']['inicio']) &
        (df['retirada'].dt.date <= filtros['periodo2']['fim'])
    )
    
    # Filtrar clientes baseado no filtro master
    if 'cliente' in filtros and "Todos" not in filtros['cliente']:
        mask_master &= df['CLIENTE'].isin(filtros['cliente'])
        clientes_permitidos = sorted(filtros['cliente'])
    else:
        clientes_permitidos = sorted(df[mask_master]['CLIENTE'].dropna().unique())
        
    if 'operacao' in filtros and "Todas" not in filtros['operacao']:
        mask_master &= df['OPERAÇÃO'].isin(filtros['operacao'])
    
    df_filtrado = df[mask_master]
    dados_filtrados = {'base': df_filtrado}
    
    # Debug de períodos usando dados filtrados
    data_min = df_filtrado['retirada'].dt.date.min()
    data_max = df_filtrado['retirada'].dt.date.max()
    
    periodo1 = (f"{filtros['periodo1']['inicio'].strftime('%d/%m/%Y')} a "
               f"{filtros['periodo1']['fim'].strftime('%d/%m/%Y')}")
    periodo2 = (f"{filtros['periodo2']['inicio'].strftime('%d/%m/%Y')} a "
               f"{filtros['periodo2']['fim'].strftime('%d/%m/%Y')}")
    
    st.header(f"Quantidade de Atendimento - P1: {periodo1} | P2: {periodo2}")
    
    with st.expander("ℹ️ Como funciona?"):
        st.markdown("""
        ### Como analisamos a quantidade de atendimentos?

        1. **Contagem de Atendimentos**:
        - Total de senhas atendidas por colaborador
        - Contabiliza apenas atendimentos finalizados
        - Agrupado por período de análise

        2. **Comparativo entre Períodos**:
        - **Período 1**: Base histórica para comparação
        - **Período 2**: Período atual em análise
        - **Variação**: Diferença percentual entre os períodos
            - 🟢 Variação positiva = Aumento na quantidade (melhor)
            - 🔴 Variação negativa = Redução na quantidade (pior)

        3. **Indicadores de Performance**:
        - ✅ Aumento no número de atendimentos = Maior produtividade
        - ⚠️ Redução no número de atendimentos = Oportunidade de melhoria

        4. **Métricas Importantes**:
        - **Total de Atendimentos**: Quantidade absoluta por colaborador
        - **Variação Percentual**: Evolução em relação ao período anterior
        - **Média por Período**: Base para análise de produtividade

        5. **Insights**:
        - 🎯 Melhor Performance: Maior quantidade ou maior aumento
        - ⚠️ Oportunidade de Melhoria: Menor quantidade ou maior redução
        """)

    try:
        # Verificar se o período selecionado está contido nos dados
        if (filtros['periodo2']['inicio'] < data_min or 
            filtros['periodo2']['fim'] > data_max):
            st.warning(
                f"⚠️ Período selecionado ({filtros['periodo2']['inicio'].strftime('%d/%m/%Y')} "
                f"a {filtros['periodo2']['fim'].strftime('%d/%m/%Y')}) está fora do intervalo "
                f"disponível na base de dados ({data_min.strftime('%d/%m/%Y')} a "
                f"{data_max.strftime('%d/%m/%Y')})"
            )
            return
        
        # Linha de seletores
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            colaboradores = sorted(df_filtrado['usuário'].unique())
            colaborador = st.selectbox(
                "Selecione o Colaborador",
                options=["Todos"] + colaboradores,
                key="qtd_atend_colaborador",
                help="Escolha um colaborador específico ou 'Todos'"
            )
        
        with col2:
            turnos = ["Todos", "TURNO A", "TURNO B", "TURNO C"]
            turno = st.selectbox(
                "Selecione o Turno",
                options=turnos,
                key="qtd_atend_turno",
                help="Filtre por turno específico"
            )
            
        with col3:
            # Usar apenas clientes permitidos pelo filtro master
            clientes = ["Todos"] + [str(cliente) for cliente in clientes_permitidos]
            cliente = st.selectbox(
                "Selecione o Cliente",
                options=clientes,
                key="qtd_atend_cliente",
                help="Filtre por cliente específico"
            )

        with col4:
            # Obter lista de datas disponíveis no período
            mask_periodo = (
                (df_filtrado['retirada'].dt.date >= filtros['periodo2']['inicio']) &
                (df_filtrado['retirada'].dt.date <= filtros['periodo2']['fim'])
            )
            datas_disponiveis = sorted(df_filtrado[mask_periodo]['retirada'].dt.date.unique())
            datas_opcoes = ["Todas"] + [data.strftime("%d/%m/%Y") for data in datas_disponiveis]
            
            data_selecionada = st.selectbox(
                "Selecione a Data",
                options=datas_opcoes,
                key="qtd_atend_data",
                help="Escolha uma data específica ou 'Todas' para ver o período completo"
            )

        # Processar data selecionada
        data_especifica = None
        if data_selecionada != "Todas":
            dia, mes, ano = map(int, data_selecionada.split('/'))
            data_especifica = pd.to_datetime(f"{ano}-{mes}-{dia}").date()

        # Criar dicionário de filtros adicionais
        adicional_filters = {
            'colaborador': colaborador,
            'turno': turno,
            'cliente': cliente,
            'data_especifica': data_especifica
        }

        # Calcular métricas para cada período com os filtros
        atend_p1 = calcular_atendimentos_por_periodo(dados_filtrados, filtros, 'periodo1', adicional_filters)
        atend_p2 = calcular_atendimentos_por_periodo(dados_filtrados, filtros, 'periodo2', adicional_filters)
        
        if atend_p1.empty or atend_p2.empty:
            st.warning("Não há dados suficientes para o período ou filtros selecionados.")
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
