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
            # Agrupar por gate e calcular métricas
            detalhes = (
                atendimentos_hora.groupby('guichê')
                .agg({
                    'id': 'count',
                    'inicio': ['min', 'max'],
                    'usuário': 'first'  # Adicionar usuário responsável
                })
                .reset_index()
            )
            
            # Renomear colunas
            detalhes.columns = ['gate', 'atendimentos', 'inicio', 'fim', 'usuario']
            
            # Calcular tempo efetivo de operação em minutos
            detalhes['tempo_operacao'] = (
                (detalhes['fim'] - detalhes['inicio'])
                .dt.total_seconds() / 60
            ).round(0)
            
            # Calcular média de atendimentos por hora
            detalhes['atend_por_hora'] = (
                detalhes['atendimentos'] / (detalhes['tempo_operacao'] / 60)
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
        <h3 style="margin: 0;">📊 Resumo do Horário {hora:02d}:00h</h3>
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

def gerar_insights_gates(metricas, data_selecionada=None, cliente=None, operacao=None):
    """Gera insights sobre o uso dos gates"""
    metricas_df, df_base, detalhes_gates = metricas
    
    # Cálculos principais
    total_gates = metricas_df['gates_ativos'].max()
    media_gates = metricas_df[metricas_df['gates_ativos'] > 0]['gates_ativos'].mean()
    total_atendimentos = metricas_df['atendimentos'].sum()
    
    # Análise por períodos
    manha = metricas_df.loc[7:14, 'gates_ativos'].mean()
    tarde = metricas_df.loc[15:22, 'gates_ativos'].mean()
    noite = pd.concat([metricas_df.loc[23:23, 'gates_ativos'], 
                      metricas_df.loc[0:7, 'gates_ativos']]).mean()
    
    # Identificar picos
    hora_pico_gates = metricas_df.loc[metricas_df['gates_ativos'].idxmax()]
    hora_pico_atendimentos = metricas_df.loc[metricas_df['atendimentos'].idxmax()]
    
    # Criar ranking dos 7 horários com mais gates ativos
    top_7_horarios = metricas_df.nlargest(7, 'gates_ativos')
    
    # Exibição dos insights
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"📊 Visão Geral em {data_selecionada.strftime('%d/%m/%Y')}")
        st.markdown(f"""
        - Gates máximos em operação: **{int(total_gates)}**
        - Média de gates ativos: **{media_gates:.1f}**
        - Total de atendimentos: **{int(total_atendimentos):,}**
        """)
        
        st.subheader("⏱️ Média Gates por Turno")
        st.markdown(f"""
        - Manhã (7h-14h): **{manha:.1f}** gates
        - Tarde (15h-22h): **{tarde:.1f}** gates
        - Noite (23h-07h): **{noite:.1f}** gates
        """)

    with col2:
        st.subheader("📈 Picos")
        st.markdown(f"""
        - Pico de gates ativos: **{int(hora_pico_gates['gates_ativos'])}** às **{int(hora_pico_gates['hora']):02d}:00h**
        - Pico de atendimentos: **{int(hora_pico_atendimentos['atendimentos'])}** às **{int(hora_pico_atendimentos['hora']):02d}:00h**
        - Média de atendimentos/gate: **{float(hora_pico_atendimentos['media_atendimentos_gate']):.1f}**
        """)
        
        st.subheader("💡 Recomendações")
        if media_gates < total_gates * 0.7:
            st.markdown("- **Atenção**: Subutilização dos gates disponíveis")
        if manha > tarde * 1.5 or tarde > manha * 1.5:
            st.markdown("- **Ação**: Redistribuir gates entre turnos")
        st.markdown("""
        - Avaliar distribuição dos gates por turno
        - Otimizar uso dos recursos disponíveis
        """)
    
    # Exibir ranking dos 7 horários com mais gates
    st.markdown("---")
    st.subheader("⚠️ Horários Críticos")
    st.markdown("#### Ranking dos Horários com Mais Gates Ativos")
    
    for idx, pico in enumerate(top_7_horarios.itertuples(), 1):
        info_adicional = f"- {data_selecionada.strftime('%d/%m/%Y')}"
        if cliente:
            info_adicional += f" - {cliente}"
        if operacao:
            info_adicional += f" - {operacao}"
            
        eficiencia = pico.atendimentos / pico.gates_ativos if pico.gates_ativos > 0 else 0
        st.markdown(
            f"**{idx}º** - {int(pico.gates_ativos)} gates às **{int(pico.hora):02d}:00h** "
            f"({int(pico.atendimentos)} atendimentos - {eficiencia:.1f} atend/gate) {info_adicional}"
        )
    
    # Adicionar nova seção de Detalhes do Horário
    st.markdown("---")
    st.subheader("🔍 Detalhes do Horário")
    
    # Criar tabs para os horários com gates ativos
    horas_ativas = [hora for hora, det in detalhes_gates.items() if not det.empty]
    if horas_ativas:
        tabs = st.tabs([f"{hora:02d}:00h ({len(detalhes_gates[hora])} gates)" 
                       for hora in sorted(horas_ativas)])
        
        for tab, hora in zip(tabs, sorted(horas_ativas)):
            with tab:
                mostrar_detalhes_gates(hora, detalhes_gates[hora], total_gates)
    else:
        st.write("Sem operações registradas no período.")

def mostrar_aba(dados, filtros):
    """Mostra a aba de análise de gates por hora"""
    st.header("Gates em Atividade/Hora")
    st.write("Análise hora a hora dos gates ativos e sua eficiência")
    
    try:
        st.session_state['tema_atual'] = detectar_tema()
        
        # Obter datas disponíveis
        df = dados['base']
        mask_periodo = (
            (df['retirada'].dt.date >= filtros['periodo2']['inicio']) &
            (df['retirada'].dt.date <= filtros['periodo2']['fim'])
        )
        datas_disponiveis = sorted(df[mask_periodo]['retirada'].dt.date.unique())
        
        if len(datas_disponiveis) == 0:
            st.warning("Não existem dados para o período selecionado.")
            return
            
        # Formatar datas para exibição
        datas_formatadas = [data.strftime('%d/%m/%Y') for data in datas_disponiveis]
        datas_dict = dict(zip(datas_formatadas, datas_disponiveis))

        # Seleção de visualização
        tipo_analise = st.radio(
            "Visualizar:",
            ["Geral", "Por Cliente", "Por Operação"],
            horizontal=True,
            key="gates_hora_tipo_analise"
        )
        
        # Interface baseada no tipo de análise
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
        
        # Exibir gráfico
        st.plotly_chart(fig, use_container_width=True, key="main_chart")
        
        # Exibir análise detalhada
        st.markdown("---")
        st.subheader("📈 Análise Detalhada")
        with st.expander("Ver análise completa", expanded=True):
            gerar_insights_gates(metricas, data_especifica, 
                               cliente_selecionado if tipo_analise == "Por Cliente" else None,
                               operacao_selecionada if tipo_analise == "Por Operação" else None)
    
    except Exception as e:
        st.error("Erro ao gerar a aba de Gates em Atividade/Hora")
        st.exception(e)
