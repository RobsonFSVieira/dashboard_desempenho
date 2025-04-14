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

def calcular_metricas_hora(dados, filtros, cliente=None):
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
            textfont={'family': 'Arial Black', 'size': 14},
            text=[f'<b>{int(v)}</b>' for v in metricas_hora['retiradas']],  # Texto em negrito
            textposition='outside',
            textfont_color='#000000',  # Texto preto para melhor contraste
        )
    )
    
    # Adiciona barras de senhas atendidas
    fig.add_trace(
        go.Bar(
            name='Senhas Atendidas',
            x=metricas_hora['hora'],
            y=metricas_hora['atendidas'],
            marker_color=cores_tema['primaria'],
            textfont={'family': 'Arial Black', 'size': 14},
            text=[f'<b>{int(v)}</b>' for v in metricas_hora['atendidas']],  # Texto em negrito
            textposition='outside',
            textfont_color='#ffffff',  # Texto branco para melhor contraste
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
            text=[f'<b>{int(v)}</b>' for v in metricas_hora['pendentes']],  # Texto em negrito
            textposition='top center',
            textfont=dict(color='#8b0000', size=14, family='Arial Black'),  # Vermelho mais escuro
            texttemplate='%{text}',  # Mantém o formato HTML
        )
    )
    
    # Atualiza layout
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
        margin=dict(l=40, r=40, t=100, b=80),  # Aumentado todas as margens
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
            ["Geral", "Por Cliente"],
            horizontal=True,
            key="comboio_ii_tipo_analise"  # Added unique key
        )
        
        if tipo_analise == "Por Cliente":
            # Lista de clientes disponíveis
            clientes = sorted(dados['base']['CLIENTE'].unique())
            cliente_selecionado = st.selectbox(
                "Selecione o Cliente:",
                clientes,
                key="comboio_ii_cliente_selectbox"  # Added unique key
            )
            
            # Calcular métricas e criar gráfico
            metricas = calcular_metricas_hora(dados, filtros, cliente_selecionado)
            fig = criar_grafico_comboio(metricas, cliente_selecionado)
        else:
            # Calcular métricas e criar gráfico geral
            metricas = calcular_metricas_hora(dados, filtros)
            fig = criar_grafico_comboio(metricas)
        
        # Exibir gráfico
        st.plotly_chart(fig, use_container_width=True)
        
        # Insights
        st.subheader("📊 Insights")
        with st.expander("Ver insights"):
            # Encontrar horário com maior acúmulo
            hora_critica = metricas.loc[metricas['pendentes'].idxmax()]
            
            st.write("#### Principais Observações:")
            st.write(f"**Horário Mais Crítico:** {int(hora_critica['hora']):02d}:00h")
            st.write(f"- Senhas Pendentes: {int(hora_critica['pendentes'])}")
            st.write(f"- Senhas Retiradas: {int(hora_critica['retiradas'])}")
            st.write(f"- Senhas Atendidas: {int(hora_critica['atendidas'])}")
            
            # Calcular eficiência do atendimento
            total_retiradas = metricas['retiradas'].sum()
            total_atendidas = metricas['atendidas'].sum()
            eficiencia = (total_atendidas / total_retiradas * 100) if total_retiradas > 0 else 0
            
            st.write(f"\n**Eficiência do Atendimento:** {eficiencia:.1f}%")
            st.write(f"- Total de Senhas Retiradas: {int(total_retiradas)}")
            st.write(f"- Total de Senhas Atendidas: {int(total_atendidas)}")
    
    except Exception as e:
        st.error("Erro ao gerar a aba de Análise de Chegada em Comboio II")
        st.exception(e)