import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import json

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

def formatar_tempo(minutos):
    """Formata o tempo em minutos para o formato mm:ss"""
    minutos_int = int(minutos)
    segundos = int((minutos - minutos_int) * 60)
    return f"{minutos_int:02d}:{segundos:02d}"

def calcular_metricas_por_periodo(dados, filtros, periodo_key, adicional_filters=None):
    """Calcula métricas por colaborador para um período específico"""
    df = dados['base']
    
    # Aplicar filtros de data
    mask = (
        (df['retirada'].dt.date >= filtros[periodo_key]['inicio']) &
        (df['retirada'].dt.date <= filtros[periodo_key]['fim'])
    )
    df_filtrado = df[mask]
    
    # Aplicar filtros adicionais se fornecidos
    if adicional_filters:
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
    
    # Calcular métricas
    metricas = df_filtrado.groupby('usuário').agg({
        'id': 'count',
        'tpatend': 'mean'
    }).reset_index()
    
    # Converter tempo para minutos
    metricas['tpatend'] = metricas['tpatend'] / 60
    
    return metricas

def criar_grafico_comparativo(dados_p1, dados_p2, filtros):
    """Cria gráfico comparativo entre períodos"""
    try:
        # Merge e prepara dados
        df_comp = pd.merge(
            dados_p1, 
            dados_p2,
            on='usuário',
            suffixes=('_p1', '_p2')
        )
        
        # Calcula total e variação percentual
        df_comp['total'] = df_comp['tpatend_p1'] + df_comp['tpatend_p2']
        df_comp['variacao'] = ((df_comp['tpatend_p2'] - df_comp['tpatend_p1']) / 
                              df_comp['tpatend_p1'] * 100)
        
        # Ordena por tempo do período 2 decrescente (maiores tempos no topo)
        df_comp = df_comp.sort_values('tpatend_p2', ascending=False)
        
        # Obtém cores do tema atual
        cores_tema = obter_cores_tema()
        
        # Prepara legendas com data formatada
        legenda_p1 = (f"Período 1 ({filtros['periodo1']['inicio'].strftime('%d/%m/%Y')} "
                      f"a {filtros['periodo1']['fim'].strftime('%d/%m/%Y')})")
        legenda_p2 = (f"Período 2 ({filtros['periodo2']['inicio'].strftime('%d/%m/%Y')} "
                      f"a {filtros['periodo2']['fim'].strftime('%d/%m/%Y')})")
        
        # Cria o gráfico
        fig = go.Figure()
        
        # Adiciona barras para período 1
        fig.add_trace(go.Bar(
            name=legenda_p1,
            y=df_comp['usuário'],
            x=df_comp['tpatend_p1'],
            orientation='h',
            text=[f"{formatar_tempo(x)} min" for x in df_comp['tpatend_p1']],
            textposition='inside',
            marker_color=cores_tema['primaria'],
            textfont={
                'size': 16,
                'color': '#ffffff',
                'family': 'Arial Black'
            },
            opacity=0.85
        ))
        
        # Adiciona barras para período 2
        fig.add_trace(go.Bar(
            name=legenda_p2,
            y=df_comp['usuário'],
            x=df_comp['tpatend_p2'],
            orientation='h',
            text=[f"{formatar_tempo(x)} min" for x in df_comp['tpatend_p2']],
            textposition='inside',
            marker_color=cores_tema['secundaria'],
            textfont={
                'size': 16,
                'color': '#000000',
                'family': 'Arial Black'
            },
            opacity=0.85
        ))

        # Adiciona anotações de variação percentual
        df_comp['posicao_total'] = df_comp['tpatend_p1'] + df_comp['tpatend_p2']
        for i, row in df_comp.iterrows():
            cor = cores_tema['sucesso'] if row['variacao'] < 0 else cores_tema['erro']
            
            fig.add_annotation(
                y=row['usuário'],
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
                'text': 'Comparativo de Tempo Médio de Atendimento por Colaborador',
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
            title='Tempo de Atendimento (minutos)',
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
        
        return fig, df_comp
    except Exception as e:
        st.error(f"Erro ao criar gráfico: {str(e)}")
        return None, None

def gerar_insights_atendimentos(atend_p1, atend_p2):
    """Gera insights sobre os tempos de atendimento dos colaboradores"""
    try:
        # Merge dos dados
        df_insights = pd.merge(
            atend_p1, 
            atend_p2, 
            on='usuário',
            suffixes=('_p1', '_p2')
        ).fillna(0)
        
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
                status = "✅" if row['tpatend_p2'] <= row['tpatend_p1'] else "⚠️"
                st.write(
                    f"**{row['usuário']}** {status}\n\n"
                    f"- P1: {formatar_tempo(row['tpatend_p1'])} min\n"
                    f"- P2: {formatar_tempo(row['tpatend_p2'])} min\n"
                    f"- Variação: {((row['tpatend_p2'] - row['tpatend_p1']) / row['tpatend_p1'] * 100):+.1f}%"
                )

        # Segunda coluna de performance
        with col_perf2:
            st.write("#### Performance (2/3)")
            df_parte = df_insights.iloc[indices[1][0]:indices[1][1]]
            for _, row in df_parte.iterrows():
                status = "✅" if row['tpatend_p2'] <= row['tpatend_p1'] else "⚠️"
                st.write(
                    f"**{row['usuário']}** {status}\n\n"
                    f"- P1: {formatar_tempo(row['tpatend_p1'])} min\n"
                    f"- P2: {formatar_tempo(row['tpatend_p2'])} min\n"
                    f"- Variação: {((row['tpatend_p2'] - row['tpatend_p1']) / row['tpatend_p1'] * 100):+.1f}%"
                )

        # Terceira coluna de performance
        with col_perf3:
            st.write("#### Performance (3/3)")
            df_parte = df_insights.iloc[indices[2][0]:indices[2][1]]
            for _, row in df_parte.iterrows():
                status = "✅" if row['tpatend_p2'] <= row['tpatend_p1'] else "⚠️"
                st.write(
                    f"**{row['usuário']}** {status}\n\n"
                    f"- P1: {formatar_tempo(row['tpatend_p1'])} min\n"
                    f"- P2: {formatar_tempo(row['tpatend_p2'])} min\n"
                    f"- Variação: {((row['tpatend_p2'] - row['tpatend_p1']) / row['tpatend_p1'] * 100):+.1f}%"
                )

        # Coluna de insights
        with col_insights:
            st.write("#### 📈 Insights")
            
            # Melhor performance (menor tempo ou maior redução)
            melhor = df_insights.loc[df_insights['tpatend_p2'].idxmin()]
            variacao_melhor = ((melhor['tpatend_p2'] - melhor['tpatend_p1']) / melhor['tpatend_p1'] * 100)
            st.markdown(
                f"<div class='success-box'>"
                f"<b>🎯 Melhor Performance</b><br>"
                f"{melhor['usuário']}<br>"
                f"Tempo: {formatar_tempo(melhor['tpatend_p2'])} min<br>"
                f"Variação: {variacao_melhor:+.1f}%"
                f"</div>",
                unsafe_allow_html=True
            )
            
            # Oportunidade de melhoria (maior tempo ou maior aumento)
            pior = df_insights.loc[df_insights['tpatend_p2'].idxmax()]
            variacao_pior = ((pior['tpatend_p2'] - pior['tpatend_p1']) / pior['tpatend_p1'] * 100)
            st.markdown(
                f"<div class='warning-box'>"
                f"<b>⚠️ Oportunidade de Melhoria</b><br>"
                f"{pior['usuário']}<br>"
                f"Tempo: {formatar_tempo(pior['tpatend_p2'])} min<br>"
                f"Variação: {variacao_pior:+.1f}%"
                f"</div>",
                unsafe_allow_html=True
            )

    except Exception as e:
        st.error(f"Erro ao gerar insights: {str(e)}")

def mostrar_aba(dados, filtros):
    """Mostra a aba de tempo de atendimento"""
    st.header("Tempo de Atendimento")

    with st.expander("ℹ️ Como funciona?"):
        st.markdown("""
        ### Como analisamos o tempo de atendimento?

        1. **Cálculo do Tempo**:
        - Tempo = (Horário de Fim - Horário de Início) do atendimento
        - Valor apresentado em minutos e segundos (mm:ss)
        - Média calculada por colaborador para cada período

        2. **Comparativo entre Períodos**:
        - **Período 1**: Base histórica para comparação
        - **Período 2**: Período atual em análise
        - **Variação**: Diferença percentual entre os períodos
            - 🟢 Variação negativa = Redução no tempo (melhor)
            - 🔴 Variação positiva = Aumento no tempo (pior)

        3. **Indicadores de Performance**:
        - ✅ Redução no tempo médio = Melhoria na eficiência
        - ⚠️ Aumento no tempo médio = Oportunidade de melhoria

        4. **Métricas Importantes**:
        - **Variação Média**: Tendência geral do grupo
        - **Maior Redução**: Melhor evolução individual
        - **Maior Aumento**: Maior necessidade de atenção

        5. **Insights**:
        - 🎯 Melhor Performance: Menor tempo médio ou maior redução
        - ⚠️ Oportunidade de Melhoria: Maior tempo médio ou maior aumento
        """)

    try:
        # Debug de períodos
        df = dados['base']
        data_min = df['retirada'].dt.date.min()
        data_max = df['retirada'].dt.date.max()
        
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
            turnos = ["Todos", "TURNO A", "TURNO B", "TURNO C"]
            turno = st.selectbox(
                "Selecione o Turno",
                options=turnos,
                key="tempo_atend_turno",
                help="Filtre por turno específico"
            )
            
        with col2:
            clientes = ["Todos"] + sorted(dados['base']['CLIENTE'].unique().tolist())
            cliente = st.selectbox(
                "Selecione o Cliente",
                options=clientes,
                key="tempo_atend_cliente",
                help="Filtre por cliente específico"
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
                key="tempo_atend_data",
                help="Escolha uma data específica ou 'Todas' para ver o período completo"
            )

        # Processar data selecionada
        data_especifica = None
        if data_selecionada != "Todas":
            dia, mes, ano = map(int, data_selecionada.split('/'))
            data_especifica = pd.to_datetime(f"{ano}-{mes}-{dia}").date()

        # Criar dicionário de filtros adicionais
        adicional_filters = {
            'turno': turno,
            'cliente': cliente,
            'data_especifica': data_especifica
        }

        # Calcular métricas para cada período com os filtros
        dados_p1 = calcular_metricas_por_periodo(dados, filtros, 'periodo1', adicional_filters)
        dados_p2 = calcular_metricas_por_periodo(dados, filtros, 'periodo2', adicional_filters)

        if dados_p1.empty or dados_p2.empty:
            st.warning("Não há dados suficientes para o período ou filtros selecionados.")
            return

        # Criar gráfico comparativo
        fig, df_merged = criar_grafico_comparativo(dados_p1, dados_p2, filtros)
        
        # Exibir gráfico
        st.plotly_chart(fig, use_container_width=True)
        
        # Métricas gerais de variação
        col1, col2, col3 = st.columns(3)
        
        with col1:
            var_media = df_merged['variacao'].mean()
            var_media_usuario = df_merged.loc[df_merged['variacao'].idxmin()]['usuário']  # Pega o nome do usuário
            st.metric(
                "Variação Média",
                var_media_usuario,  # Nome do usuário como valor principal
                f"{var_media:+.1f}%",  # Variação como delta
                delta_color="normal"
            )
        
        with col2:
            melhor_var = df_merged.loc[df_merged['variacao'].idxmin()]
            st.metric(
                "Maior Redução (Melhor)",
                melhor_var['usuário'],  # Nome do usuário como valor principal
                f"{melhor_var['variacao']:.1f}%",  # Variação como delta
                delta_color="normal"
            )
        
        with col3:
            pior_var = df_merged.loc[df_merged['variacao'].idxmax()]
            st.metric(
                "Maior Aumento (Pior)",
                pior_var['usuário'],  # Nome do usuário como valor principal
                f"{pior_var['variacao']:.1f}%",  # Variação como delta
                delta_color="normal"
            )
        
        # Tabela detalhada
        with st.expander("Ver dados detalhados", expanded=False):
            st.dataframe(
                df_merged.style.format({
                    'tpatend_p1': '{:.1f}',
                    'tpatend_p2': '{:.1f}',
                    'variacao': '{:+.1f}%'
                }),
                use_container_width=True
            )
        
        # Gerar insights detalhados
        gerar_insights_atendimentos(dados_p1, dados_p2)
    
    except Exception as e:
        st.error("Erro ao gerar análise de tempo de atendimento")
        st.exception(e)
