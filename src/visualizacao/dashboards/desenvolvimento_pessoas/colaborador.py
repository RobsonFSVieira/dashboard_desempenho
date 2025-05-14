import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import timedelta

def analisar_colaborador(dados, filtros, colaborador, adicional_filters=None):
    """Analisa dados de um colaborador específico"""
    df = dados['base']
    
    # Calcular médias gerais por operação (todos os usuários)
    mask_periodo = (
        (df['retirada'].dt.date >= filtros['periodo2']['inicio']) &
        (df['retirada'].dt.date <= filtros['periodo2']['fim'])
    )
    medias_gerais = df[mask_periodo].groupby('OPERAÇÃO').agg({
        'tpatend': 'mean'
    }).reset_index()
    medias_gerais['tpatend'] = medias_gerais['tpatend'] / 60
    
    # Aplicar filtros para o colaborador específico
    mask = mask_periodo & (df['usuário'] == colaborador)
    
    # Aplicar filtros adicionais
    if adicional_filters:
        if adicional_filters['turno'] != "Todos":
            # Mapear hora para turno
            df['turno'] = df['inicio'].dt.hour.map(
                lambda x: 'TURNO A' if 6 <= x < 14 else ('TURNO B' if 14 <= x < 22 else 'TURNO C')
            )
            mask &= (df['turno'] == adicional_filters['turno'])
        
        if adicional_filters['cliente'] != "Todos":
            mask &= (df['CLIENTE'] == adicional_filters['cliente'])
            
        if adicional_filters['data_especifica']:
            mask &= (df['retirada'].dt.date == adicional_filters['data_especifica'])
    
    df_filtrado = df[mask]
    
    # Métricas por operação
    metricas_op = df_filtrado.groupby('OPERAÇÃO').agg({
        'id': 'count',
        'tpatend': 'mean',
        'tpesper': 'mean'
    }).reset_index()
    
    # Converter tempos para minutos
    metricas_op['tpatend'] = metricas_op['tpatend'] / 60
    metricas_op['tpesper'] = metricas_op['tpesper'] / 60
    
    # Adicionar médias gerais como referência
    metricas_op = pd.merge(
        metricas_op,
        medias_gerais.rename(columns={'tpatend': 'meta_tempo'}),
        on='OPERAÇÃO',
        how='left'
    )
    
    # Calcular variação em relação à média geral
    metricas_op['variacao'] = ((metricas_op['tpatend'] - metricas_op['meta_tempo']) / 
                              metricas_op['meta_tempo'] * 100)
    
    return metricas_op

def criar_grafico_operacoes(metricas_op):
    """Cria gráfico comparativo por operação"""
    # Ordenar dados para os gráficos
    dados_qtd = metricas_op.sort_values('id', ascending=True)
    dados_tempo = metricas_op.sort_values('tpatend', ascending=False)

    # Criar rótulos personalizados para tempo médio com cores
    tempo_labels = []
    for i, row in dados_tempo.iterrows():
        var_pct = ((row['tpatend'] - row['meta_tempo']) / row['meta_tempo'] * 100)
        # Verde se negativo (mais rápido), vermelho se positivo (mais lento)
        cor = 'red' if var_pct > 0 else 'green'
        tempo_labels.append(
            f"<b>{row['tpatend']:.1f} min <span style='color: {cor}'>({var_pct:+.1f}%)</span></b>"
        )

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("<b>Quantidade de Atendimentos</b>", "<b>Tempo Médio de Atendimento</b>"),
        specs=[[{"type": "bar"}, {"type": "bar"}]],
        horizontal_spacing=0.20,  # Aumentado de 0.15 para 0.20
        column_widths=[0.35, 0.65]  # Define proporção 35%-65% entre as colunas
    )
    
    # Gráfico de quantidade - barra horizontal
    fig.add_trace(
        go.Bar(
            y=dados_qtd['OPERAÇÃO'],
            x=dados_qtd['id'],
            name="<b>Atendimentos</b>",
            text=["<b>" + str(val) + "</b>" for val in dados_qtd['id']],
            textposition='inside',
            insidetextanchor='start',  # Alinha o texto no início da barra
            marker_color='royalblue',
            orientation='h'
        ),
        row=1, col=1
    )
    
    # Gráfico de tempo médio com rótulos personalizados
    fig.add_trace(
        go.Bar(
            y=dados_tempo['OPERAÇÃO'],
            x=dados_tempo['tpatend'],
            name="<b>Tempo Médio</b>",
            text=tempo_labels,
            textposition='inside',
            insidetextanchor='start',  # Alinha o texto no início da barra
            marker_color='lightblue',
            orientation='h'
        ),
        row=1, col=2
    )

    # Adicionar linha de meta por operação (sem ajuste necessário agora)
    fig.add_trace(
        go.Scatter(
            y=dados_tempo['OPERAÇÃO'],
            x=dados_tempo['meta_tempo'],
            name="<b>Meta (Média Geral)</b>",
            mode='lines+markers',
            line=dict(color='red', dash='dash'),
            marker=dict(symbol='diamond', size=8)
        ),
        row=1, col=2
    )

    # Calcular o valor máximo para o eixo X do gráfico de tempo
    max_tempo = max(dados_tempo['tpatend'].max(), dados_tempo['meta_tempo'].max())
    # Reduzir margem pois os rótulos agora estão dentro
    max_tempo_with_margin = max_tempo * 1.1

    # Atualizar layout com margens reduzidas
    fig.update_layout(
        height=max(400, len(metricas_op) * 40),
        showlegend=True,
        title_text="<b>Análise por Operação</b>",
        margin=dict(t=50, b=20, l=20, r=50)  # Margem direita reduzida
    )

    # Atualizar eixos com limites definidos
    fig.update_xaxes(title_text="<b>Quantidade</b>", row=1, col=1)
    fig.update_xaxes(
        title_text="<b>Minutos</b>",
        range=[0, max_tempo_with_margin],  # Define limite do eixo X
        row=1, col=2
    )
    fig.update_yaxes(title_text="", row=1, col=1)
    fig.update_yaxes(title_text="", row=1, col=2)
    
    return fig

def criar_grafico_evolucao_diaria(dados, filtros, colaborador):
    """Cria gráfico de evolução diária"""
    df = dados['base']
    # Aplicar filtros de data
    mask = (
        (df['retirada'].dt.date >= filtros['periodo2']['inicio']) &
        (df['retirada'].dt.date <= filtros['periodo2']['fim'])
    )
    
    # Calcular média geral do período para comparação
    df_periodo = df[mask]
    meta_geral = df_periodo['tpatend'].mean() / 60
    
    df_filtrado = df[mask & (df['usuário'] == colaborador)]
    
    # Agrupar por dia
    evolucao = df_filtrado.groupby(df_filtrado['retirada'].dt.date).agg({
        'id': 'count',
        'tpatend': 'mean'
    }).reset_index()
    
    evolucao['tpatend'] = evolucao['tpatend'] / 60
    # Calcular variação diária em relação à meta
    evolucao['variacao'] = ((evolucao['tpatend'] - meta_geral) / meta_geral * 100)

    # Formatar período para exibição
    periodo = (f"{filtros['periodo2']['inicio'].strftime('%d/%m/%Y')} a "
              f"{filtros['periodo2']['fim'].strftime('%d/%m/%Y')}")

    fig = make_subplots(
        rows=1, cols=3,  # Aumentado para 3 colunas
        subplot_titles=(
            "Atendimentos por Dia",
            "Tempo Médio por Dia",
            f"Variação da Meta ({periodo})"
        ),
        specs=[[{"type": "scatter"}, {"type": "scatter"}, {"type": "scatter"}]],
        column_widths=[0.33, 0.33, 0.34]  # Distribuição do espaço
    )
    
    fig.add_trace(
        go.Scatter(
            x=evolucao['retirada'],
            y=evolucao['id'],
            mode='lines+markers',
            name="Atendimentos",
            line=dict(color='royalblue')
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=evolucao['retirada'],
            y=evolucao['tpatend'],
            mode='lines+markers',
            name="Tempo Médio",
            line=dict(color='lightblue')
        ),
        row=1, col=2
    )
    
    # Adicionar gráfico de variação com linha única
    fig.add_trace(
        go.Scatter(
            x=evolucao['retirada'],
            y=evolucao['variacao'],
            mode='lines+markers',
            name="Variação",
            line=dict(
                width=2,
                color="red"  # Cor base da linha
            ),
            marker=dict(
                color=['green' if var < 0 else 'red' for var in evolucao['variacao']],
                size=8
            ),
            hovertemplate='Data: %{x}<br>Variação: %{y:.1f}%<extra></extra>'
        ),
        row=1, col=3
    )

    # Linha de referência no zero
    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="gray",
        row=1, col=3
    )
    
    fig.update_layout(
        height=400,
        showlegend=True,
        title_text=f"Evolução Diária ({periodo})"
    )
    
    # Atualizar eixo Y do gráfico de variação
    fig.update_yaxes(title_text="Variação (%)", row=1, col=3)
    
    return fig

def mostrar_aba(dados, filtros):
    """Mostra a aba de análise individual do colaborador"""
    # Formatar período para exibição
    periodo = (f"{filtros['periodo2']['inicio'].strftime('%d/%m/%Y')} a "
              f"{filtros['periodo2']['fim'].strftime('%d/%m/%Y')}")
    
    st.header(f"Análise Individual do Colaborador ({periodo})")

    with st.expander("ℹ️ Como funciona?"):
        st.markdown("""
        ### Como analisamos o desempenho individual?

        1. **Métricas Principais**:
        - **Tempo Médio de Atendimento**: Média do tempo entre início e fim de cada atendimento
        - **Meta**: Média geral de todos os atendimentos da mesma operação no período
        - **Variação**: Diferença percentual entre o tempo médio do colaborador e a meta
            - 🟢 Variação negativa = Mais rápido que a meta
            - 🔴 Variação positiva = Mais lento que a meta

        2. **Análise por Operação**:
        - **Quantidade**: Total de atendimentos realizados em cada operação
        - **Tempo Médio**: Média de tempo por operação comparada à meta
        - **Meta**: Linha vermelha pontilhada indica a média geral da operação
        
        3. **Evolução Diária**:
        - **Atendimentos**: Quantidade de senhas atendidas por dia
        - **Tempo Médio**: Evolução do tempo médio diário
        - **Variação da Meta**: 
            - Pontos verdes = Abaixo da meta (mais rápido)
            - Pontos vermelhos = Acima da meta (mais lento)

        4. **Performance**:
        - ✅ Dentro da meta: Variação até ±10%
        - ⚠️ Fora da meta: Variação maior que ±10%

        5. **Insights**:
        - 🎯 Melhor Performance: Operação com menor variação absoluta
        - ⚠️ Oportunidade de Melhoria: Operação com maior variação absoluta
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
            colaboradores = sorted(dados['base']['usuário'].unique())
            colaborador = st.selectbox(
                "Selecione o Colaborador",
                options=colaboradores,
                help="Escolha um colaborador para análise detalhada"
            )
        
        with col2:
            turnos = ["Todos", "TURNO A", "TURNO B", "TURNO C"]
            turno = st.selectbox(
                "Selecione o Turno",
                options=turnos,
                help="Filtre por turno específico"
            )
            
        with col3:
            # Handle NaN values and get unique clients
            clientes_unicos = dados['base']['CLIENTE'].dropna().unique()
            clientes = ["Todos"] + sorted([str(cliente) for cliente in clientes_unicos])
            cliente = st.selectbox(
                "Selecione o Cliente",
                options=clientes,
                help="Filtre por cliente específico"
            )

        with col4:
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
                help="Escolha uma data específica ou 'Todas' para ver o período completo"
            )
            
            # Conversão da data selecionada
            data_especifica = None
            if data_selecionada != "Todas":
                dia, mes, ano = map(int, data_selecionada.split('/'))
                data_especifica = pd.to_datetime(f"{ano}-{mes}-{dia}").date()

        if colaborador:
            # Análise do colaborador com filtros adicionais
            adicional_filters = {
                'turno': turno,
                'cliente': cliente,
                'data_especifica': data_especifica
            }
            metricas_op = analisar_colaborador(dados, filtros, colaborador, adicional_filters)
            
            # Métricas principais
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total de Atendimentos",
                    metricas_op['id'].sum()
                )
            
            with col2:
                tempo_medio = metricas_op['tpatend'].mean()
                st.metric(
                    "Tempo Médio",
                    f"{tempo_medio:.1f} min"
                )
            
            with col3:
                meta_media = metricas_op['meta_tempo'].mean()
                variacao = ((tempo_medio - meta_media) / meta_media * 100)
                # Emoji verde se mais rápido (negativo), vermelho se mais lento (positivo)
                status_emoji = "🟢" if variacao < 0 else "🔴"
                st.metric(
                    f"Variação da Meta {status_emoji}",
                    f"{variacao:+.1f}%",
                    delta_color="inverse"
                )
            
            with col4:
                # TODO: Implementar cálculo de ociosidade quando disponível
                tempo_ociosidade = 0  # Placeholder até implementação
                st.metric(
                    "Tempo Médio de Ociosidade",
                    f"{tempo_ociosidade:.1f} min"
                )
            
            # Gráficos
            st.plotly_chart(criar_grafico_operacoes(metricas_op), use_container_width=True)
            st.plotly_chart(criar_grafico_evolucao_diaria(dados, filtros, colaborador), use_container_width=True)
            
            # Análise Detalhada
            st.subheader("📊 Análise Detalhada")
            with st.expander("Ver análise", expanded=True):
                # Criar 4 colunas principais
                col_perf1, col_perf2, col_perf3, col_insights = st.columns([0.25, 0.25, 0.25, 0.25])
                
                # Dividir operações em 3 partes
                tamanho_parte = len(metricas_op) // 3
                resto = len(metricas_op) % 3
                
                # Ajustar distribuição para acomodar o resto
                indices = [
                    (0, tamanho_parte + (1 if resto > 0 else 0)),
                    (tamanho_parte + (1 if resto > 0 else 0), 2*tamanho_parte + (2 if resto > 1 else 1 if resto > 0 else 0)),
                    (2*tamanho_parte + (2 if resto > 1 else 1 if resto > 0 else 0), len(metricas_op))
                ]

                # Primeira coluna de performance
                with col_perf1:
                    st.write("#### Performance (1/3)")
                    for i, (_, row) in enumerate(metricas_op.iterrows()):
                        if i < indices[0][1]:
                            status = "✅" if abs(row['variacao']) <= 10 else "⚠️"
                            st.write(
                                f"**{row['OPERAÇÃO']}** {status}\n\n"
                                f"- Atendimentos: {row['id']}\n"
                                f"- Tempo Médio: {row['tpatend']:.1f} min\n"
                                f"- Meta: {row['meta_tempo']:.1f} min\n"
                                f"- Variação: {row['variacao']:+.1f}%"
                            )

                # Segunda coluna de performance
                with col_perf2:
                    st.write("#### Performance (2/3)")
                    for i, (_, row) in enumerate(metricas_op.iterrows()):
                        if indices[0][1] <= i < indices[1][1]:
                            status = "✅" if abs(row['variacao']) <= 10 else "⚠️"
                            st.write(
                                f"**{row['OPERAÇÃO']}** {status}\n\n"
                                f"- Atendimentos: {row['id']}\n"
                                f"- Tempo Médio: {row['tpatend']:.1f} min\n"
                                f"- Meta: {row['meta_tempo']:.1f} min\n"
                                f"- Variação: {row['variacao']:+.1f}%"
                            )
                
                # Terceira coluna de performance
                with col_perf3:
                    st.write("#### Performance (3/3)")
                    for i, (_, row) in enumerate(metricas_op.iterrows()):
                        if indices[1][1] <= i:
                            status = "✅" if abs(row['variacao']) <= 10 else "⚠️"
                            st.write(
                                f"**{row['OPERAÇÃO']}** {status}\n\n"
                                f"- Atendimentos: {row['id']}\n"
                                f"- Tempo Médio: {row['tpatend']:.1f} min\n"
                                f"- Meta: {row['meta_tempo']:.1f} min\n"
                                f"- Variação: {row['variacao']:+.1f}%"
                            )

                # Coluna de insights (mantida como estava)
                with col_insights:
                    st.write("#### 📈 Insights")
                    
                    # Box para pontos fortes
                    st.markdown("""
                        <style>
                            .success-box { 
                                background-color: rgba(0,255,0,0.1);
                                padding: 10px;
                                border-radius: 5px;
                            }
                        </style>
                    """, unsafe_allow_html=True)
                    
                    melhor_op = metricas_op.loc[metricas_op['variacao'].abs().idxmin()]
                    st.markdown(
                        f"<div class='success-box'>"
                        f"<b>🎯 Melhor Performance</b><br>"
                        f"{melhor_op['OPERAÇÃO']}<br>"
                        f"Variação: {melhor_op['variacao']:+.1f}%"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                    
                    # Box para pontos de melhoria
                    pior_op = metricas_op.loc[metricas_op['variacao'].abs().idxmax()]
                    if abs(pior_op['variacao']) > 10:
                        st.markdown("""
                            <style>
                                .warning-box { 
                                    background-color: rgba(255,0,0,0.1);
                                    padding: 10px;
                                    border-radius: 5px;
                                    margin-top: 10px;
                                }
                            </style>
                        """, unsafe_allow_html=True)
                        
                        st.markdown(
                            f"<div class='warning-box'>"
                            f"<b>⚠️ Oportunidade de Melhoria</b><br>"
                            f"{pior_op['OPERAÇÃO']}<br>"
                            f"Variação: {pior_op['variacao']:+.1f}%"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                
    except Exception as e:
        st.error("Erro ao analisar dados do colaborador")
        st.exception(e)
