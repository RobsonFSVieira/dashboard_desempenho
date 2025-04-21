import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
from datetime import datetime
import math

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
        'grid': '#2c3e50' if is_dark else '#e9ecef'
    }

def calcular_gates_hora(dados, filtros, cliente=None, operacao=None, data_especifica=None):
    """Calcula a quantidade de gates ativos por hora"""
    df = dados['base']
    
    # Aplicar filtros de data
    if data_especifica:
        mask = (df['retirada'].dt.date == data_especifica)
    else:
        mask = (
            (df['retirada'].dt.date >= filtros['periodo2']['inicio']) &
            (df['retirada'].dt.date <= filtros['periodo2']['fim'])
        )
    df_filtrado = df[mask]
    
    # Filtrar por cliente se especificado
    if cliente:
        df_filtrado = df_filtrado[df_filtrado['CLIENTE'] == cliente]
    
    # Filtrar por operação se especificado
    if operacao:
        df_filtrado = df_filtrado[df_filtrado['OPERAÇÃO'] == operacao]
    
    # Criar DataFrame para métricas por hora
    metricas_hora = pd.DataFrame()
    metricas_hora['hora'] = range(24)
    
    # Calcular gates únicos ativos por hora
    gates_por_hora = df_filtrado.groupby(df_filtrado['inicio'].dt.hour)['guichê'].nunique()
    metricas_hora['gates_ativos'] = metricas_hora['hora'].map(gates_por_hora).fillna(0)
    
    # Calcular atendimentos por hora
    atendimentos_hora = df_filtrado.groupby(df_filtrado['inicio'].dt.hour)['id'].count()
    metricas_hora['atendimentos'] = metricas_hora['hora'].map(atendimentos_hora).fillna(0)
    
    # Calcular média de atendimentos por gate
    metricas_hora['media_atendimentos_gate'] = (metricas_hora['atendimentos'] / 
                                               metricas_hora['gates_ativos']).fillna(0)
    
    # Adicionar detalhes dos gates por hora
    detalhes_gates = {}
    for hora in range(24):
        # Filtrar atendimentos da hora
        mask_hora = (df_filtrado['inicio'].dt.hour == hora)
        atendimentos_hora = df_filtrado[mask_hora].copy()
        
        if not atendimentos_hora.empty:
            # Calcular total de atendimentos na hora para percentuais
            total_atendimentos_hora = len(atendimentos_hora)
            
            # Calcular tempo de atendimento
            atendimentos_hora['tempo_atendimento'] = (
                atendimentos_hora['fim'] - atendimentos_hora['inicio']
            ).dt.total_seconds() / 60
            
            # Função para calcular intervalo médio
            def calcular_intervalo_medio(serie):
                diff = serie.diff()
                if diff.empty:
                    return pd.Timedelta(seconds=0)
                return diff.mean().total_seconds() / 60
            
            # Agrupar por gate e calcular métricas
            detalhes = (
                atendimentos_hora.groupby('guichê')
                .agg({
                    'id': 'count',
                    'inicio': ['min', 'max', calcular_intervalo_medio],  # Média de intervalo
                    'usuário': 'first',
                    'tempo_atendimento': 'mean',  # Média tempo atendimento
                })
                .reset_index()
            )
            
            # Renomear colunas
            detalhes.columns = [
                'gate', 'atendimentos', 'inicio', 'fim', 
                'media_intervalo', 'usuario', 'media_tempo_atend'
            ]
            
            # Adicionar coluna de senhas transferidas como 0 (já que não temos essa informação)
            detalhes['senhas_transferidas'] = 0
            
            # Calcular tempo efetivo de operação em minutos
            detalhes['tempo_operacao'] = (
                (detalhes['fim'] - detalhes['inicio'])
                .dt.total_seconds() / 60
            ).round(0)
            
            # Calcular média de atendimentos por hora
            detalhes['atend_por_hora'] = (
                detalhes['atendimentos'] / (detalhes['tempo_operacao'] / 60)
            ).round(1)
            
            # Calcular percentual de contribuição
            detalhes['percentual_contribuicao'] = (
                detalhes['atendimentos'] / total_atendimentos_hora * 100
            ).round(1)
            
            detalhes_gates[hora] = detalhes
        else:
            detalhes_gates[hora] = pd.DataFrame()
    
    return metricas_hora, df_filtrado, detalhes_gates

def criar_grafico_gates(metricas_hora, cliente=None):
    """Cria gráfico de barras para análise de gates ativos"""
    cores_tema = obter_cores_tema()
    fig = go.Figure()
    
    # Converter zeros para None para não exibir
    def replace_zeros(series):
        return [None if x == 0 else int(x) for x in series]
    
    # Adicionar barras de gates ativos
    fig.add_trace(
        go.Bar(
            name='Gates Ativos',
            x=metricas_hora['hora'],
            y=replace_zeros(metricas_hora['gates_ativos']),
            marker_color=cores_tema['primaria'],
            text=replace_zeros(metricas_hora['gates_ativos']),
            textposition='outside',
            textfont={'family': 'Arial Black', 'size': 16},
            texttemplate='%{text:d}',
            cliponaxis=False,
        )
    )
    
    # Adicionar linha de média de atendimentos por gate
    fig.add_trace(
        go.Scatter(
            name='Média de Atendimentos por Gate',
            x=metricas_hora['hora'],
            y=metricas_hora['media_atendimentos_gate'].round(1),
            mode='lines+markers',
            line=dict(color='#2ecc71', width=2),
            marker=dict(size=8),
            yaxis='y2'
        )
    )
    
    # Atualizar layout
    titulo = f"Gates em Atividade por Hora {'- ' + cliente if cliente else 'Geral'}"
    fig.update_layout(
        title={
            'text': titulo,
            'font': {'size': 20, 'color': cores_tema['texto']},
            'x': 0.5,
            'xanchor': 'center',
            'y': 0.95
        },
        xaxis_title="Hora do Dia",
        yaxis_title="Quantidade de Gates",
        yaxis2=dict(
            title=dict(
                text='Média de Atendimentos por Gate',
                font=dict(color='#2ecc71')
            ),
            tickfont=dict(color='#2ecc71'),
            overlaying='y',
            side='right'
        ),
        height=600,
        showlegend=True,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor=cores_tema['fundo'],
        legend={
            'orientation': 'h',
            'yanchor': 'bottom',
            'y': 1.15,
            'xanchor': 'right',
            'x': 1,
            'font': {'size': 14, 'color': cores_tema['texto']},
            'bgcolor': 'rgba(0,0,0,0)'
        },
        margin=dict(l=40, r=40, t=150, b=100),
        xaxis=dict(
            tickmode='array',
            ticktext=[f'{i:02d}h' for i in range(24)],
            tickvals=list(range(24)),
            tickfont={'color': cores_tema['texto'], 'size': 12},
            gridcolor=cores_tema['grid'],
            showline=True,
            linewidth=1,
            linecolor=cores_tema['grid'],
            range=[-0.5, 23.5]
        ),
        yaxis=dict(
            gridcolor=cores_tema['grid'],
            showline=True,
            linewidth=1,
            linecolor=cores_tema['grid'],
            tickfont={'color': cores_tema['texto'], 'size': 12}
        )
    )
    
    return fig

def mostrar_detalhes_gates(hora, detalhes, total_gates):
    """Mostra detalhes dos gates ativos em uma determinada hora"""
    # Adicionar indicador visual do período do dia
    emoji_periodo = "🌙" if 0 <= hora <= 5 else "🌅" if 6 <= hora <= 11 else "🌞" if 12 <= hora <= 17 else "🌚"
    
    if detalhes.empty:
        st.write("Sem operações neste horário.")
        return
    
    # Ordenar por tempo de operação (decrescente)
    detalhes = detalhes.sort_values('tempo_operacao', ascending=False)
    
    # Criar um cartão com informações gerais do horário
    st.markdown(f"""
    <div style="
        padding: 20px;
        border-radius: 10px;
        background-color: {'rgba(14, 17, 23, 0.6)' if detectar_tema() == 'dark' else 'rgba(247, 248, 249, 0.6)'};
        margin-bottom: 20px;
    ">
        <h3 style="margin: 0;">📊 Resumo do Horário {hora:02d}:00h {emoji_periodo}</h3>
        <div style="display: flex; justify-content: space-between; margin-top: 15px;">
            <div>
                <h4 style="color: #1a5fb4;">Gates Ativos</h4>
                <p style="font-size: 24px; margin: 0;">{len(detalhes)} / {total_gates}</p>
            </div>
            <div>
                <h4 style="color: #2ecc71;">Atendimentos</h4>
                <p style="font-size: 24px; margin: 0;">{detalhes['atendimentos'].sum()}</p>
            </div>
            <div>
                <h4 style="color: #f1c40f;">Média/Gate</h4>
                <p style="font-size: 24px; margin: 0;">{detalhes['atend_por_hora'].mean():.1f}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Mostrar distribuição em gráfico de pizza
    st.markdown("### 📊 Distribuição do Tempo de Operação")
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Criar gráfico de pizza com plotly
        labels = ['< 15 min', '15-30 min', '30-45 min', '> 45 min']
        values = [
            len(detalhes[detalhes['tempo_operacao'] < 15]),
            len(detalhes[(detalhes['tempo_operacao'] >= 15) & (detalhes['tempo_operacao'] < 30)]),
            len(detalhes[(detalhes['tempo_operacao'] >= 30) & (detalhes['tempo_operacao'] < 45)]),
            len(detalhes[detalhes['tempo_operacao'] >= 45])
        ]
        colors = ['#ff6b6b', '#ffd93d', '#51cf66', '#339af0']
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            marker_colors=colors,
            hole=.3,
            textinfo='percent+label',
            textposition='outside'
        )])
        
        fig.update_layout(
            showlegend=False,
            margin=dict(t=0, b=0, l=0, r=0),
            height=200
        )
        
        # Adicionar key única para o gráfico de pizza
        st.plotly_chart(fig, use_container_width=True, key=f"pie_chart_{hora}")
    
    with col2:
        # Mostrar legenda com contagens
        for label, value, color in zip(labels, values, colors):
            st.markdown(f"""
            <div style="display: flex; align-items: center; margin-bottom: 5px;">
                <div style="width: 15px; height: 15px; background-color: {color}; border-radius: 3px; margin-right: 10px;"></div>
                <div>{label}: <strong>{value}</strong> gates</div>
            </div>
            """, unsafe_allow_html=True)

def get_color_by_duration(duracao):
    """Retorna cor baseada na duração do atendimento"""
    if duracao < 15:
        return "#ff6b6b"  # Vermelho
    elif duracao < 30:
        return "#ffd93d"  # Amarelo
    elif duracao < 45:
        return "#51cf66"  # Verde
    else:
        return "#339af0"  # Azul

def criar_relogio_interativo(horas_ativas, hora_selecionada=None):
    """Cria um relógio interativo usando componentes do Streamlit"""
    cores_tema = obter_cores_tema()
    
    # Organizar as horas em 4 períodos do dia
    periodos = {
        "Madrugada 🌙": [h for h in horas_ativas if 0 <= h <= 5],
        "Manhã 🌅": [h for h in horas_ativas if 6 <= h <= 11],
        "Tarde 🌞": [h for h in horas_ativas if 12 <= h <= 17],
        "Noite 🌚": [h for h in horas_ativas if 18 <= h <= 23]
    }
    
    st.markdown("""
        <style>
        div[data-testid="stSelectbox"] {
            background-color: transparent !important;
        }
        div.row-widget.stSelectbox > div {
            background-color: transparent !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Criar seletor por período
    col1, col2 = st.columns([1, 1])
    
    with col1:
        periodo = st.selectbox(
            "Período do dia",
            options=list(periodos.keys()),
            key="periodo_relogio"
        )
    
    # Formatar horas disponíveis no período
    horas_periodo = periodos[periodo]
    opcoes_hora = [f"{h:02d}:00h" for h in horas_periodo]
    
    if not opcoes_hora:
        with col2:
            st.warning(f"Sem operações neste período")
        return None
    
    # Criar seletor de hora
    with col2:
        hora_sel = st.selectbox(
            "Horário",
            options=opcoes_hora,
            key="hora_relogio"
        )
    
    # Extrair hora selecionada
    if hora_sel:
        return int(hora_sel.split(":")[0])
    return None

def gerar_insights_gates(metricas, data_selecionada=None, cliente=None, operacao=None):
    """Gera insights sobre o uso dos gates"""
    metricas_df, df_base, detalhes_gates = metricas
    
    if 'hora_selecionada' not in st.session_state:
        st.session_state.hora_selecionada = None
    
    # Adicionar CSS para ocultar os labels do select_slider
    st.markdown("""
        <style>
            /* Esconde os labels das extremidades do select slider */
            div.stSlider [data-testid="stTickBar"] {
                display: none;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # Criação do seletor de hora - Removida a divisão em colunas para ocupar toda largura
    horas_disponiveis = [hora for hora in range(24) if not detalhes_gates[hora].empty]
    if not horas_disponiveis:
        st.warning("Não há dados disponíveis para análise")
        return
        
    hora = st.select_slider(
        "Selecione a hora para análise:",
        options=horas_disponiveis,
        format_func=lambda x: f"{x:02d}:00h",
        key="hora_analise",
        label_visibility='hidden'  # Alterado para 'hidden'
    )

    # Função para formatar tempo em mm:ss
    def formatar_tempo(minutos):
        if pd.isna(minutos):
            return "--:-- min"
        mins = int(minutos)
        segs = int((minutos - mins) * 60)
        return f"{mins:02d}:{segs:02d} min"

    # Estilo padrão para todas as tabelas
    estilo_tabela = {
        'background-color': '#0e1117',
        'color': 'white',
        'border-color': '#2d2d2d'
    }

    # Se tiver uma hora selecionada, mostrar análise detalhada
    if hora is not None:
        detalhes = detalhes_gates[hora]
        if not detalhes.empty:
            st.markdown(f"""
            <div style='background-color: #1a5fb4; padding: 1rem; border-radius: 10px; margin: 1rem 0; color: white;'>
                <h3 style="margin: 0; color: white;">📊 Análise Detalhada - {hora:02d}:00h</h3>
                <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Total de atendimentos na hora: {detalhes['atendimentos'].sum()}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Tabela principal com todas as métricas solicitadas
            cols = ['gate', 'usuario', 'atendimentos', 'percentual_contribuicao', 
                   'media_tempo_atend', 'media_intervalo', 'senhas_transferidas']
            
            # Formatação da tabela
            df_display = detalhes[cols].copy()
            
            # Adicionar colunas de períodos de atendimento
            periodos_atendimento = {}
            for gate in detalhes['gate']:
                mask_gate = (df_base['guichê'] == gate) & (df_base['inicio'].dt.hour == hora)
                atends = df_base[mask_gate].sort_values('inicio')
                
                # Criar lista de períodos para cada atendimento
                periodos = []
                for _, atend in atends.iterrows():
                    inicio = f"{hora:02d}:{atend['inicio'].minute:02d}"
                    fim = f"{hora:02d}:{atend['fim'].minute:02d}"
                    periodos.append(f"{inicio}-{fim}")
                
                # Preencher dicionário com os períodos
                periodos_atendimento[gate] = periodos
            
            # Encontrar o máximo de atendimentos para criar as colunas
            max_atends = max(len(p) for p in periodos_atendimento.values())
            
            # Adicionar colunas de período ao DataFrame
            for i in range(max_atends):
                df_display[f'Atendimento {i+1}'] = df_display['gate'].map(
                    lambda x: periodos_atendimento[x][i] if i < len(periodos_atendimento[x]) else '-'
                )
            
            # Renomear e reorganizar colunas
            colunas_base = ['Gate', 'Atendente', 'Atendimentos', 'Contribuição (%)', 
                           'Tempo Médio (min)', 'Intervalo Médio (min)', 'Transferências']
            colunas_atendimentos = [f'Atendimento {i+1}' for i in range(max_atends)]
            df_display.columns = colunas_base + colunas_atendimentos
            
            df_display = df_display.sort_values('Contribuição (%)', ascending=False)
            df_display['Contribuição (%)'] = df_display['Contribuição (%)'].apply(lambda x: f"{x:.1f}%")
            
            # Aplicar formatação de tempo
            df_display['Tempo Médio (min)'] = df_display['Tempo Médio (min)'].apply(formatar_tempo)
            df_display['Intervalo Médio (min)'] = df_display['Intervalo Médio (min)'].apply(formatar_tempo)
            
            # Mostrar tabela com tema escuro
            st.dataframe(
                df_display.style.set_properties(**estilo_tabela),
                use_container_width=True
            )
            
            # Título seção de contribuição e gráfico
            st.markdown("### 📊 Contribuição por Gate (%)")
            fig = go.Figure()
            
            # Barra de fundo (60 minutos)
            fig.add_trace(go.Bar(
                x=detalhes['gate'],
                y=[60] * len(detalhes),  # 60 minutos
                marker_color='rgba(128, 128, 128, 0.2)',
                name='Hora Total',
                hoverinfo='skip'
            ))

            # Calcular minutos dentro da hora para início e fim
            minuto_inicio = detalhes['inicio'].dt.minute
            minuto_fim = detalhes['fim'].dt.minute
            
            # Ajustar casos onde fim é na próxima hora
            minuto_fim = minuto_fim.where(minuto_fim >= minuto_inicio, 60)
            
            # Criar rótulos com horários
            rotulos = [
                f"{hora:02d}:{inicio:02d}-{hora:02d}:{fim:02d}"
                for inicio, fim in zip(minuto_inicio, minuto_fim)
            ]
            
            # Barra de tempo ativo (período real)
            fig.add_trace(go.Bar(
                x=detalhes['gate'],
                y=minuto_fim - minuto_inicio,
                base=minuto_inicio,
                marker_color=obter_cores_tema()['primaria'],
                name='Período Ativo',
                hovertemplate='Horário: %{base:.0f}-%{y:.0f}min<br>Duração: %{y:.1f}min<extra></extra>'
            ))

            # Criar visualização detalhada dos atendimentos
            for idx, gate in enumerate(detalhes['gate']):
                # Filtrar atendimentos do gate na hora específica
                mask_gate = (df_base['guichê'] == gate) & (df_base['inicio'].dt.hour == hora)
                atendimentos_gate = df_base[mask_gate].sort_values('inicio')
                
                if not atendimentos_gate.empty:
                    # Para cada atendimento, criar uma barra
                    for _, atend in atendimentos_gate.iterrows():
                        inicio_min = atend['inicio'].minute + (atend['inicio'].second / 60)
                        fim_min = atend['fim'].minute + (atend['fim'].second / 60)
                        
                        # Barra do atendimento (azul)
                        fig.add_trace(go.Bar(
                            x=[gate],
                            y=[fim_min - inicio_min],
                            base=[inicio_min],
                            marker_color=obter_cores_tema()['primaria'],
                            name='Atendimento',
                            showlegend=False,
                            hovertemplate=(
                                f'Horário: {hora:02d}:{int(inicio_min):02d}-{hora:02d}:{int(fim_min):02d}<br>'
                                f'Duração: {fim_min - inicio_min:.1f}min<extra></extra>'
                            )
                        ))
                        
                        # Se houver próximo atendimento, adicionar intervalo
                        if _ < len(atendimentos_gate) - 1:
                            proximo_inicio = atendimentos_gate.iloc[_ + 1]['inicio'].minute + (atendimentos_gate.iloc[_ + 1]['inicio'].second / 60)
                            # Barra do intervalo (escura)
                            fig.add_trace(go.Bar(
                                x=[gate],
                                y=[proximo_inicio - fim_min],
                                base=[fim_min],
                                marker_color='rgba(0,0,0,0.1)',
                                name='Intervalo',
                                showlegend=False,
                                hovertemplate='Intervalo: %{y:.1f}min<extra></extra>'
                            ))

            fig.update_layout(
                barmode='overlay',
                title={'text': ''},
                margin=dict(t=0, b=20, l=40, r=40),
                xaxis_title='Gate',
                yaxis_title='Minutos',
                height=400,
                xaxis={'tickfont': {'size': 14}},
                yaxis={
                    'tickfont': {'size': 14},
                    'range': [0, 65],
                    'tickmode': 'array',
                    'tickvals': [0, 15, 30, 45, 60],
                    'ticktext': ['0', '15', '30', '45', '60']
                }
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Título seção de desempenho (mantido mas com estilo consistente)
            st.markdown("### 👥 Desempenho por Atendente")
            
            metricas_atendente = detalhes.groupby('usuario').agg({
                'atendimentos': 'sum',
                'media_tempo_atend': 'mean',
                'media_intervalo': 'mean',
                'senhas_transferidas': 'sum'
            }).round(1)
            
            metricas_atendente.columns = ['Total Atendimentos', 'Tempo Médio (min)', 
                                        'Intervalo Médio (min)', 'Transferências']
            
            # Aplicar formatação de tempo nas métricas de atendente
            metricas_atendente['Tempo Médio (min)'] = metricas_atendente['Tempo Médio (min)'].apply(formatar_tempo)
            metricas_atendente['Intervalo Médio (min)'] = metricas_atendente['Intervalo Médio (min)'].apply(formatar_tempo)
            
            st.dataframe(
                metricas_atendente.style.set_properties(**estilo_tabela),
                use_container_width=True
            )
            
            # Detalhes estatísticos
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### 📊 Estatísticas de Tempo")
                stats_tempo = {
                    "Menor tempo médio": formatar_tempo(detalhes['media_tempo_atend'].min()),
                    "Maior tempo médio": formatar_tempo(detalhes['media_tempo_atend'].max()),
                    "Tempo médio geral": formatar_tempo(detalhes['media_tempo_atend'].mean())
                }
                for k, v in stats_tempo.items():
                    st.metric(k, v)
            
            with col2:
                st.markdown("### ⌛ Estatísticas de Intervalo")
                stats_intervalo = {
                    "Menor intervalo": formatar_tempo(detalhes['media_intervalo'].min()),
                    "Maior intervalo": formatar_tempo(detalhes['media_intervalo'].max()),
                    "Intervalo médio": formatar_tempo(detalhes['media_intervalo'].mean())
                }
                for k, v in stats_intervalo.items():
                    st.metric(k, v)
        
        else:
            st.info(f"Não há operações registradas para o horário {hora:02d}:00h")
    
    return

def mostrar_aba(dados, filtros):
    """Mostra a aba de análise de gates por hora"""
    st.header("Gates em Atividade/Hora")
    st.write("Análise hora a hora dos gates ativos e sua eficiência")
    
    with st.expander("ℹ️ Como funciona?"):
        st.markdown("""
        ### Como analisamos os Gates por Hora?

        1. **Análise Temporal**:
        - **Por Hora**: Acompanhamento detalhado dos gates ativos em cada hora
        - **Distribuição**: Como os gates são alocados ao longo do dia
        - **Eficiência**: Média de atendimentos por gate em cada período

        2. **Métricas de Performance**:
        - **Gates Ativos**: Quantidade de guichês operando em cada horário
        - **Atendimentos**: Volume de senhas atendidas por hora
        - **Média/Gate**: Produtividade média por gate em cada hora

        3. **Análise de Períodos**:
        - **Manhã (07h-14h)**: Comportamento no primeiro turno
        - **Tarde (15h-22h)**: Performance no segundo turno
        - **Noite (23h-06h)**: Operação no período noturno

        4. **Insights Operacionais**:
        - 🎯 Horários de maior eficiência
        - ⚠️ Momentos críticos de operação
        - 📊 Sugestões de dimensionamento

        5. **Análise Detalhada**:
        - Timeline detalhada dos atendimentos
        - Performance individual dos gates
        - Períodos de maior demanda
        """)
    
    try:
        st.session_state['tema_atual'] = detectar_tema()
        
        df = dados['base']
        mask_periodo = (
            (df['retirada'].dt.date >= filtros['periodo2']['inicio']) &
            (df['retirada'].dt.date <= filtros['periodo2']['fim'])
        )
        datas_disponiveis = sorted(df[mask_periodo]['retirada'].dt.date.unique())
        
        if len(datas_disponiveis) == 0:
            st.warning("Não existem dados para o período selecionado.")
            return
            
        datas_formatadas = [data.strftime('%d/%m/%Y') for data in datas_disponiveis]
        datas_dict = dict(zip(datas_formatadas, datas_disponiveis))

        tipo_analise = st.radio(
            "Visualizar:",
            ["Geral", "Por Cliente", "Por Operação"],
            horizontal=True,
            key="gates_hora_tipo_analise"
        )
        
        if tipo_analise == "Por Cliente":
            clientes = sorted(dados['base']['CLIENTE'].unique())
            cliente_selecionado = st.selectbox(
                "Selecione o Cliente:",
                clientes,
                key="gates_hora_cliente_selectbox"
            )
            
            data_formatada = st.selectbox(
                "Selecione uma data:",
                options=datas_formatadas,
                key="gates_hora_data_cliente"
            )
            data_especifica = datas_dict[data_formatada]
            
            metricas = calcular_gates_hora(dados, filtros, 
                                         cliente=cliente_selecionado, 
                                         data_especifica=data_especifica)
            fig = criar_grafico_gates(metricas[0], cliente_selecionado)
            
        elif tipo_analise == "Por Operação":
            operacoes = sorted(dados['base']['OPERAÇÃO'].unique())
            operacao_selecionada = st.selectbox(
                "Selecione a Operação:",
                operacoes,
                key="gates_hora_operacao_selectbox"
            )
            
            data_formatada = st.selectbox(
                "Selecione uma data:",
                options=datas_formatadas,
                key="gates_hora_data_operacao"
            )
            data_especifica = datas_dict[data_formatada]
            
            metricas = calcular_gates_hora(dados, filtros, 
                                         operacao=operacao_selecionada, 
                                         data_especifica=data_especifica)
            fig = criar_grafico_gates(metricas[0], operacao_selecionada)
            
        else:
            data_formatada = st.selectbox(
                "Selecione uma data:",
                options=datas_formatadas,
                key="gates_hora_data_geral"
            )
            data_especifica = datas_dict[data_formatada]
            
            metricas = calcular_gates_hora(dados, filtros, data_especifica=data_especifica)
            fig = criar_grafico_gates(metricas[0])
        
        st.plotly_chart(fig, use_container_width=True, key="main_chart")
        
        st.markdown("---")
        st.subheader("📈 Análise Detalhada")
        with st.expander("Ver análise completa", expanded=True):
            gerar_insights_gates(metricas, data_especifica, 
                               cliente_selecionado if tipo_analise == "Por Cliente" else None,
                               operacao_selecionada if tipo_analise == "Por Operação" else None)
    
    except Exception as e:
        st.error("Erro ao gerar a aba de Gates em Atividade/Hora")
        st.exception(e)
</copilot-edited-file>
```
