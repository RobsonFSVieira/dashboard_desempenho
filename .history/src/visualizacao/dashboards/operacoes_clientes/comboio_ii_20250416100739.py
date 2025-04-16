import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
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
        'primaria': '#1a5fb4' if is_dark else '#1864ab',      # Azul mais escuro
        'secundaria': '#4dabf7' if is_dark else '#83c9ff',    # Azul mais claro
        'texto': '#ffffff' if is_dark else '#2c3e50',         # Cor do texto
        'fundo': '#0e1117' if is_dark else '#ffffff',         # Cor de fundo
        'grid': '#2c3e50' if is_dark else '#e9ecef',         # Cor da grade
        'alerta': '#ff6b6b' if is_dark else '#ff5757'        # Vermelho
    }

def calcular_potencial_atendimento(df_filtrado, minutos_atendimento=8):
    """Calcula quantas senhas poderiam ser atendidas dentro da hora"""
    df = df_filtrado.copy()
    df['minuto_retirada'] = df['retirada'].dt.minute
    df['atendimento_viavel'] = df['minuto_retirada'] <= (60 - minutos_atendimento)
    
    metricas_viaveis = pd.DataFrame()
    metricas_viaveis['hora'] = range(24)
    viaveis = df[df['atendimento_viavel']].groupby(df['retirada'].dt.hour).size()
    metricas_viaveis['senhas_viaveis'] = metricas_viaveis['hora'].map(viaveis).fillna(0)
    
    return metricas_viaveis

def calcular_metricas_hora(dados, filtros, cliente=None, operacao=None, data_especifica=None):
    """Calcula métricas de senhas por hora considerando o efeito bola de neve"""
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
    
    # Agrupar por hora mantendo os IDs
    metricas_hora = pd.DataFrame()
    metricas_hora['hora'] = range(24)
    
    # Agrupar mantendo os IDs das senhas e garantir valores numéricos
    retiradas_grupo = df_filtrado.groupby(df_filtrado['retirada'].dt.hour)
    metricas_hora['retiradas'] = pd.Series(retiradas_grupo.size()).reindex(range(24)).fillna(0)
    metricas_hora['senhas_hora'] = retiradas_grupo.apply(lambda x: x['id'].tolist())
    
    # Calcular atendidas e pendentes com valores padrão
    atendidas = df_filtrado.groupby(df_filtrado['inicio'].dt.hour)['id'].count()
    metricas_hora['atendidas'] = metricas_hora['hora'].map(atendidas).fillna(0)
    
    # Calcular pendentes com efeito bola de neve
    metricas_hora['pendentes'] = 0
    pendentes_acumulados = 0
    
    for idx in metricas_hora.index:
        total_para_atender = metricas_hora.loc[idx, 'retiradas'] + pendentes_acumulados
        atendidas_hora = metricas_hora.loc[idx, 'atendidas']
        pendentes_acumulados = max(0, total_para_atender - atendidas_hora)
        metricas_hora.loc[idx, 'pendentes'] = pendentes_acumulados
    
    # Adicionar métricas de viabilidade
    metricas_viaveis = calcular_potencial_atendimento(df_filtrado)
    metricas_hora['senhas_viaveis'] = metricas_viaveis['senhas_viaveis']
    metricas_hora['senhas_inviaveis'] = metricas_hora['retiradas'] - metricas_hora['senhas_viaveis']
    
    return metricas_hora, df_filtrado

def criar_grafico_comboio(metricas_hora, cliente=None):
    """Cria gráfico de barras para análise de comboio"""
    cores_tema = obter_cores_tema()
    fig = go.Figure()
    
    # Converter zeros para None para não exibir, garantindo valores numéricos
    def replace_zeros(series):
        return [None if pd.isna(x) or x == 0 else int(x) for x in series]
    
    # Adiciona barras de senhas retiradas com tratamento de NaN
    fig.add_trace(
        go.Bar(
            name='Senhas Retiradas',
            x=metricas_hora['hora'],
            y=replace_zeros(metricas_hora['retiradas']),
            marker_color=cores_tema['secundaria'],
            text=replace_zeros(metricas_hora['retiradas']),
            textposition='outside',
            textfont={'family': 'Arial Black', 'size': 16},
            texttemplate='%{text:d}',
            cliponaxis=False,
        )
    )
    
    # Adiciona barras de senhas atendidas com tratamento de NaN
    fig.add_trace(
        go.Bar(
            name='Senhas Atendidas',
            x=metricas_hora['hora'],
            y=replace_zeros(metricas_hora['atendidas']),
            marker_color=cores_tema['primaria'],
            text=replace_zeros(metricas_hora['atendidas']),
            textposition='outside',
            textfont={'family': 'Arial Black', 'size': 16},
            texttemplate='%{text:d}',
            cliponaxis=False,
        )
    )
    
    # Adiciona barras de senhas pendentes com tratamento de NaN e nova anotação
    fig.add_trace(
        go.Bar(
            name='Senhas Pendentes (Acumuladas)',
            x=metricas_hora['hora'],
            y=replace_zeros(metricas_hora['pendentes']),
            marker_color=cores_tema['alerta'],
            text=replace_zeros(metricas_hora['pendentes']),
            textposition='outside',
            textfont={'family': 'Arial Black', 'size': 16},
            texttemplate='%{text:d}',
            cliponaxis=False,
        )
    )
    
    # Adiciona linha de potencial de atendimento
    fig.add_trace(
        go.Scatter(
            name='Potencial Real de Atendimento',
            x=metricas_hora['hora'],
            y=replace_zeros(metricas_hora['senhas_viaveis']),
            mode='lines+markers',
            line=dict(color='#2ecc71', width=2, dash='dot'),
            marker=dict(size=8),
        )
    )

    # Atualiza layout para acomodar os rótulos maiores
    titulo = f"Análise Hora a Hora {'- ' + cliente if cliente else 'Geral'}"
    fig.update_layout(
        title={
            'text': titulo,
            'font': {'size': 20, 'color': cores_tema['texto']},  # Aumentado tamanho do título
            'x': 0.5,
            'xanchor': 'center',
            'y': 0.95  # Ajustado posição do título
        },
        xaxis_title={
            'text': "Hora do Dia",
            'font': {'size': 16, 'color': cores_tema['texto']}  # Aumentado tamanho da fonte
        },
        yaxis_title={
            'text': "Quantidade de Senhas",
            'font': {'size': 16, 'color': cores_tema['texto']}  # Aumentado tamanho da fonte
        },
        barmode='group',
        height=600,  # Aumentado altura do gráfico
        showlegend=True,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor=cores_tema['fundo'],
        legend={
            'orientation': 'h',
            'yanchor': 'bottom',
            'y': 1.15,  # Aumentado para dar espaço à anotação
            'xanchor': 'right',
            'x': 1,
            'font': {'size': 14, 'color': cores_tema['texto']},  # Aumentado tamanho da fonte
            'bgcolor': 'rgba(0,0,0,0)'
        },
        margin=dict(l=40, r=40, t=150, b=100),  # Aumentada margem superior (t) para 150
        xaxis=dict(
            tickmode='array',
            ticktext=[f'{i:02d}h' for i in range(24)],  # Formata como 00h, 01h, etc
            tickvals=list(range(24)),
            tickfont={'color': cores_tema['texto'], 'size': 12},
            gridcolor=cores_tema['grid'],
            showline=True,
            linewidth=1,
            linecolor=cores_tema['grid'],
            range=[-0.5, 23.5]  # Ajusta o range para mostrar todas as horas
        ),
        yaxis=dict(
            gridcolor=cores_tema['grid'],
            showline=True,
            linewidth=1,
            linecolor=cores_tema['grid'],
            tickfont={'color': cores_tema['texto'], 'size': 12},
            range=[0, metricas_hora[['retiradas', 'atendidas', 'pendentes']].max().max() * 1.3]  # Aumentado espaço
        )
    )
    
    # Adiciona anotação explicativa atualizada com novo texto e posição
    fig.add_annotation(
        text="⚠️ As senhas pendentes formam o 'efeito bola de neve' - elas acumulam,<br>somando com as senhas retiradas do horário vigente",
        xref="paper", yref="paper",
        x=1.02,  # Mantido à direita
        y=1.08,  # Mantido abaixo da legenda
        showarrow=False,
        font=dict(size=12, color=cores_tema['texto']),
        align='right',  # Alterado para 'right' para alinhar texto à direita
        bgcolor='rgba(255, 255, 255, 0.8)' if detectar_tema() == 'light' else 'rgba(14, 17, 23, 0.8)'
    )
    
    return fig

def gerar_insights_comboio(metricas, dados=None, data_selecionada=None, cliente=None, operacao=None):
    """Gera insights sobre o padrão de chegada em comboio"""
    metricas_df, df_base = metricas
    
    # Cálculos principais
    total_retiradas = metricas_df['retiradas'].sum()
    total_atendidas = metricas_df['atendidas'].sum()
    eficiencia = (total_atendidas / total_retiradas * 100) if total_retiradas > 0 else 0
    
    # Novos cálculos
    total_viaveis = metricas_df['senhas_viaveis'].sum()
    total_inviaveis = metricas_df['senhas_inviaveis'].sum()
    eficiencia_ajustada = (total_atendidas / total_viaveis * 100) if total_viaveis > 0 else 0
    
    hora_critica = metricas_df.loc[metricas_df['pendentes'].idxmax()]
    
    # Análise por períodos (ajustado para novos horários)
    manha = metricas_df.loc[7:14, 'retiradas'].mean()
    tarde = metricas_df.loc[15:22, 'retiradas'].mean()
    noite = pd.concat([metricas_df.loc[23:23, 'retiradas'], metricas_df.loc[0:7, 'retiradas']]).mean()
    
    # Obter picos do período
    hora_pico_retiradas = metricas_df.loc[metricas_df['retiradas'].idxmax()]
    hora_pico_pendentes = metricas_df.loc[metricas_df['pendentes'].idxmax()]
    hora_pico_atendidas = metricas_df.loc[metricas_df['atendidas'].idxmax()]
    
    # Criar ranking dos 7 maiores picos
    top_7_picos = metricas_df.nlargest(7, 'retiradas')
    
    # Exibição dos insights
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"📊 Visão Geral em {data_selecionada.strftime('%d/%m/%Y')}")
        st.markdown(f"""
        - Senhas retiradas: **{total_retiradas:,}**
        - Senhas atendidas: **{total_atendidas:,}**
        - Eficiência: **{eficiencia:.1f}%**
        """)
        
        st.subheader("📊 Métricas Ajustadas")
        st.markdown(f"""
        - Senhas com tempo viável: **{total_viaveis:,}** ({(total_viaveis/total_retiradas*100):.1f}%)
        - Senhas sem tempo viável: **{total_inviaveis:,}** ({(total_inviaveis/total_retiradas*100):.1f}%)
        - Eficiência ajustada: **{eficiencia_ajustada:.1f}%**
        """)
        
        st.subheader("⏱️ Média Retiradas por Hora")
        st.markdown(f"""
        - Média manhã (7h-14h): **{int(manha):,}** senhas/hora
        - Média tarde (15h-22h): **{int(tarde):,}** senhas/hora
        - Média noite (23h-07h): **{int(noite):,}** senhas/hora
        """)

    with col2:
        st.subheader("📈 Picos")
        st.markdown(f"""
        - Pico de retiradas: **{int(hora_pico_retiradas['retiradas']):,}** às **{int(hora_pico_retiradas['hora']):02d}:00h**
        - Pico de pendências: **{int(hora_pico_pendentes['pendentes']):,}** às **{int(hora_pico_pendentes['hora']):02d}:00h**
        - Pico de atendimentos: **{int(hora_pico_atendidas['atendidas']):,}** às **{int(hora_pico_atendidas['hora']):02d}:00h**
        """)
        
        st.subheader("💡 Recomendações")
        if hora_critica['pendentes'] > hora_critica['atendidas'] * 1.5:
            st.markdown("- **Urgente**: Reforço de equipe no horário crítico")
        if eficiencia < 80:
            st.markdown("- **Atenção**: Eficiência abaixo do esperado")
        st.markdown("""
        - Avaliar distribuição dos atendimentos
        - Implementar sistema de agendamento
        """)
    
    # Nova seção de Pontos Críticos
    st.markdown("---")
    st.subheader("⚠️ Pontos Críticos")
    
    # Exibir ranking dos 7 maiores picos
    st.markdown("#### Ranking dos Maiores Picos de Retiradas")
    for idx, pico in enumerate(top_7_picos.itertuples(), 1):
        info_adicional = f"- {data_selecionada.strftime('%d/%m/%Y')}"
        if cliente:
            info_adicional += f" - {cliente}"
        if operacao:
            info_adicional += f" - {operacao}"
            
        st.markdown(f"**{idx}º** - {int(pico.retiradas):,} senhas às **{int(pico.hora):02d}:00h** {info_adicional}")
    
    # Criar tabela de faseamento com detalhes
    st.markdown("#### Timeline dos Picos")
    
    # Definir colunas desejadas e verificar quais estão disponíveis
    colunas_desejadas = [
        'id', 'prefixo', 'numero', 'complemento', 'status', 
        'retirada', 'inicio', 'fim', 'guichê', 'usuário'
    ]
    
    dados_detalhados = []
    
    # Criar tabs para cada horário de pico
    tabs = st.tabs([f"{idx + 1}º) {int(pico.hora):02d}:00h ({int(pico.retiradas)} senhas)" 
                    for idx, (_, pico) in enumerate(top_7_picos.iterrows())])
    
    for tab, (_, pico) in zip(tabs, top_7_picos.iterrows()):
        with tab:
            hora = int(pico['hora'])
            senhas_hora = pico['senhas_hora']
            
            # Buscar detalhes das senhas na base
            detalhes_senhas = df_base[df_base['id'].isin(senhas_hora)].copy()
            
            # Formatar as colunas de data/hora
            for col in ['retirada', 'inicio', 'fim']:
                if col in detalhes_senhas.columns:
                    detalhes_senhas[col] = detalhes_senhas[col].dt.strftime('%H:%M:%S')
            
            # Mostrar resumo do horário
            st.write(f"### Detalhes do Horário {hora:02d}:00h")
            col1, col2, col3, col4 = st.columns(4)
            
            # Calcular pendências do horário anterior (hora - 1)
            pendencias_anterior = metricas_df.loc[metricas_df['hora'] == (hora - 1 if hora > 0 else 23), 'pendentes'].iloc[0] if hora in metricas_df['hora'].values else 0
            novas_senhas = int(pico['retiradas'])
            
            # Exibir métrica com detalhamento
            col1.metric(
                f"Senhas para Atender: {novas_senhas + int(pendencias_anterior)} (Retiradas: {novas_senhas} + Pendentes: {int(pendencias_anterior)})",
                None  # Removendo o valor principal pois já está no título
            )
            
            col2.metric("Senhas Atendidas", int(pico['atendidas']))
            col3.metric("Senhas Pendentes", int(pico['pendentes']))
            col4.metric("Potencial Real de Atendimento", int(pico['senhas_viaveis']))
            
            # Exibir tabela detalhada
            st.dataframe(
                detalhes_senhas[colunas_desejadas],
                column_config={
                    'id': st.column_config.NumberColumn('ID', width=70),
                    'prefixo': st.column_config.TextColumn('Prefixo', width=80),
                    'numero': st.column_config.NumberColumn('Número', width=80),
                    'complemento': st.column_config.TextColumn('Complemento', width=100),
                    'status': st.column_config.TextColumn('Status', width=100),
                    'retirada': st.column_config.TextColumn('Retirada', width=100),
                    'inicio': st.column_config.TextColumn('Início', width=100),
                    'fim': st.column_config.TextColumn('Fim', width=100),
                    'guichê': st.column_config.TextColumn('Guichê', width=80),
                    'usuário': st.column_config.TextColumn('Usuário', width=120)
                },
                hide_index=True,
                use_container_width=True
            )

def mostrar_aba(dados, filtros):
    """Mostra a aba de análise detalhada de chegada em comboio"""
    st.header("Análise de Chegada em Comboio II")
    st.write("Análise hora a hora de senhas retiradas, atendidas e pendentes")
    
    try:
        st.session_state['tema_atual'] = detectar_tema()
        
        # Obter datas disponíveis na base dentro do período 2
        df = dados['base']
        mask_periodo = (
            (df['retirada'].dt.date >= filtros['periodo2']['inicio']) &
            (df['retirada'].dt.date <= filtros['periodo2']['fim'])
        )
        datas_disponiveis = sorted(df[mask_periodo]['retirada'].dt.date.unique())
        
        if len(datas_disponiveis) == 0:
            st.warning("Não existem dados para o período selecionado.")
            return
            
        # Formatar datas para exibição no formato brasileiro
        datas_formatadas = [data.strftime('%d/%m/%Y') for data in datas_disponiveis]
        datas_dict = dict(zip(datas_formatadas, datas_disponiveis))

        # Seleção de visualização
        tipo_analise = st.radio(
            "Visualizar:",
            ["Geral", "Por Cliente", "Por Operação"],
            horizontal=True,
            key="comboio_ii_tipo_analise"
        )
        
        if tipo_analise == "Por Cliente":
            # Lista de clientes disponíveis
            clientes = sorted(dados['base']['CLIENTE'].unique())
            cliente_selecionado = st.selectbox(
                "Selecione o Cliente:",
                clientes,
                key="comboio_ii_cliente_selectbox"
            )
            
            # Seletor de data com formato dd/mm/aaaa
            data_formatada = st.selectbox(
                "Selecione uma data:",
                options=datas_formatadas,
                key="comboio_ii_data_cliente"
            )
            data_especifica = datas_dict[data_formatada]
            
            # Calcular métricas e criar gráfico
            metricas = calcular_metricas_hora(dados, filtros, cliente=cliente_selecionado, data_especifica=data_especifica)
            fig = criar_grafico_comboio(metricas[0], cliente_selecionado)
            
        elif tipo_analise == "Por Operação":
            # Lista de operações disponíveis
            operacoes = sorted(dados['base']['OPERAÇÃO'].unique())
            operacao_selecionada = st.selectbox(
                "Selecione a Operação:",
                operacoes,
                key="comboio_ii_operacao_selectbox"
            )
            
            # Seletor de data com formato dd/mm/aaaa
            data_formatada = st.selectbox(
                "Selecione uma data:",
                options=datas_formatadas,
                key="comboio_ii_data_operacao"
            )
            data_especifica = datas_dict[data_formatada]
            
            # Calcular métricas e criar gráfico
            metricas = calcular_metricas_hora(dados, filtros, operacao=operacao_selecionada, data_especifica=data_especifica)
            fig = criar_grafico_comboio(metricas[0], operacao_selecionada)
            
        else:
            # Seletor de data com formato dd/mm/aaaa
            data_formatada = st.selectbox(
                "Selecione uma data:",
                options=datas_formatadas,
                key="comboio_ii_data_geral"
            )
            data_especifica = datas_dict[data_formatada]
            
            # Calcular métricas e criar gráfico geral
            metricas = calcular_metricas_hora(dados, filtros, data_especifica=data_especifica)
            fig = criar_grafico_comboio(metricas[0])
        
        # Exibir gráfico primeiro
        st.plotly_chart(fig, use_container_width=True)
        
        # Insights depois
        st.markdown("---")
        st.subheader("📈 Análise Detalhada")
        with st.expander("Ver análise completa", expanded=True):
            gerar_insights_comboio(metricas, dados, data_especifica, 
                                 cliente_selecionado if tipo_analise == "Por Cliente" else None,
                                 operacao_selecionada if tipo_analise == "Por Operação" else None)
    
    except Exception as e:
        st.error("Erro ao gerar a aba de Análise de Chegada em Comboio II")
        st.exception(e)