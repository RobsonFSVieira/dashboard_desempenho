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

def calcular_metricas_hora(dados, filtros, cliente=None, operacao=None):
    """Calcula métricas de senhas por hora"""
    df = dados['base']
    
    # Aplicar filtros de data para período 2
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
    
    # Agrupar por hora
    metricas_hora = pd.DataFrame()
    metricas_hora['hora'] = range(24)
    
    # Calcular senhas retiradas por hora
    retiradas = df_filtrado.groupby(df_filtrado['retirada'].dt.hour)['id'].count()
    metricas_hora['retiradas'] = metricas_hora['hora'].map(retiradas).fillna(0)
    
    # Calcular senhas atendidas por hora
    atendidas = df_filtrado.groupby(df_filtrado['inicio'].dt.hour)['id'].count()
    metricas_hora['atendidas'] = metricas_hora['hora'].map(atendidas).fillna(0)
    
    # Calcular senhas pendentes
    metricas_hora['pendentes'] = metricas_hora['retiradas'].cumsum() - metricas_hora['atendidas'].cumsum()
    metricas_hora['pendentes'] = metricas_hora['pendentes'].clip(lower=0)  # Evita valores negativos
    
    return metricas_hora

def criar_grafico_comboio(metricas_hora, cliente=None):
    """Cria gráfico de barras para análise de comboio"""
    cores_tema = obter_cores_tema()
    fig = go.Figure()
    
    # Adiciona barras de senhas retiradas
    fig.add_trace(
        go.Bar(
            name='Senhas Retiradas',
            x=metricas_hora['hora'],
            y=metricas_hora['retiradas'],
            marker_color=cores_tema['secundaria'],
            text=metricas_hora['retiradas'].astype(int),
            textposition='outside',
            textfont={'family': 'Arial Black', 'size': 16},  # Aumentado para 16
            texttemplate='%{text}',  # Removido negrito
            cliponaxis=False,  # Evita corte dos rótulos
        )
    )
    
    # Adiciona barras de senhas atendidas
    fig.add_trace(
        go.Bar(
            name='Senhas Atendidas',
            x=metricas_hora['hora'],
            y=metricas_hora['atendidas'],
            marker_color=cores_tema['primaria'],
            text=metricas_hora['atendidas'].astype(int),
            textposition='outside',
            textfont={'family': 'Arial Black', 'size': 16},  # Aumentado para 16
            texttemplate='%{text}',  # Removido negrito
            cliponaxis=False,  # Evita corte dos rótulos
        )
    )
    
    # Adiciona linha de senhas pendentes
    fig.add_trace(
        go.Scatter(
            name='Senhas Pendentes',
            x=metricas_hora['hora'],
            y=metricas_hora['pendentes'],
            mode='lines+markers+text',
            line=dict(color=cores_tema['alerta'], width=2),
            marker=dict(size=6, symbol='circle'),
            text=metricas_hora['pendentes'].astype(int),
            textposition='top center',
            textfont=dict(
                size=16,  # Aumentado para 16
                family='Arial Black',
                color='#8b0000'  # Vermelho mais escuro
            ),
            texttemplate='%{text}',  # Removido negrito
            cliponaxis=False,  # Evita corte dos rótulos
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
            'y': 1.05,  # Ajustado posição da legenda
            'xanchor': 'right',
            'x': 1,
            'font': {'size': 14, 'color': cores_tema['texto']},  # Aumentado tamanho da fonte
            'bgcolor': 'rgba(0,0,0,0)'
        },
        margin=dict(l=40, r=40, t=100, b=100),  # Aumentada margem inferior
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
    
    return fig

def mostrar_aba(dados, filtros):
    """Mostra a aba de análise detalhada de chegada em comboio"""
    st.header("Análise de Chegada em Comboio II")
    st.write("Análise hora a hora de senhas retiradas, atendidas e pendentes")
    
    try:
        st.session_state['tema_atual'] = detectar_tema()
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
            
            # Calcular métricas e criar gráfico
            metricas = calcular_metricas_hora(dados, filtros, cliente=cliente_selecionado)
            fig = criar_grafico_comboio(metricas, cliente_selecionado)
            
        elif tipo_analise == "Por Operação":
            # Lista de operações disponíveis
            operacoes = sorted(dados['base']['OPERAÇÃO'].unique())
            operacao_selecionada = st.selectbox(
                "Selecione a Operação:",
                operacoes,
                key="comboio_ii_operacao_selectbox"
            )
            
            # Calcular métricas e criar gráfico
            metricas = calcular_metricas_hora(dados, filtros, operacao=operacao_selecionada)
            fig = criar_grafico_comboio(metricas, operacao_selecionada)
            
        else:
            # Calcular métricas e criar gráfico geral
            metricas = calcular_metricas_hora(dados, filtros)
            fig = criar_grafico_comboio(metricas)
        
        # Exibir gráfico
        st.plotly_chart(fig, use_container_width=True)
        
        # Insights
        st.subheader("📊 Insights")
        with st.expander("Ver insights"):
            # Calcular métricas principais
            hora_critica = metricas.loc[metricas['pendentes'].idxmax()]
            total_retiradas = metricas['retiradas'].sum()
            total_atendidas = metricas['atendidas'].sum()
            eficiencia = (total_atendidas / total_retiradas * 100) if total_retiradas > 0 else 0
            
            # 1. Visão Geral
            st.markdown("### 📈 Visão Geral")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    "🎟️ Total de Senhas",
                    f"{int(total_retiradas):,}",
                    f"{total_atendidas:,} atendidas"
                )
            
            with col2:
                st.metric(
                    "📊 Eficiência do Atendimento",
                    f"{eficiencia:.1f}%",
                    f"{int(total_retiradas - total_atendidas)} pendentes"
                )
            
            # 2. Análise Temporal
            st.markdown("### ⏱️ Análise por Período")
            col3, col4 = st.columns(2)
            
            with col3:
                st.markdown("#### ⚠️ Horário Mais Crítico")
                manha = metricas.loc[6:11, 'retiradas'].mean()
                tarde = metricas.loc[12:17, 'retiradas'].mean()
                noite = metricas.loc[18:23, 'retiradas'].mean()
                
                st.write(f"""
                - **Hora Crítica:** {int(hora_critica['hora']):02d}:00h
                - Senhas Pendentes: {int(hora_critica['pendentes']):,}
                - Senhas Retiradas: {int(hora_critica['retiradas']):,}
                - Senhas Atendidas: {int(hora_critica['atendidas']):,}
                """)
            
            with col4:
                st.markdown("#### 📊 Distribuição")
                st.write(f"""
                - **Manhã (6h-11h):** {int(manha):,} senhas/hora
                - **Tarde (12h-17h):** {int(tarde):,} senhas/hora
                - **Noite (18h-23h):** {int(noite):,} senhas/hora
                """)
            
            # 3. Recomendações
            st.markdown("### 💡 Recomendações")
            col5, col6 = st.columns(2)
            
            with col5:
                st.markdown("#### 🎯 Ações Imediatas")
                st.write("""
                - Reforçar equipe no horário crítico
                - Monitorar acúmulo de senhas
                - Priorizar redução de pendências
                """)
            
            with col6:
                st.markdown("#### 📋 Plano de Melhorias")
                st.write("""
                - Distribuir demanda ao longo do dia
                - Implementar agendamento prévio
                - Otimizar processos nos horários de pico
                """)
    
    except Exception as e:
        st.error("Erro ao gerar a aba de Análise de Chegada em Comboio II")
        st.exception(e)