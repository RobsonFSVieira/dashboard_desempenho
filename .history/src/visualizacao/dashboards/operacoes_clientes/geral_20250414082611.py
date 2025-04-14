import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

def formatar_tempo(minutos):
    """Formata o tempo de minutos para o formato hh:mm min ou mm:ss min"""
    if pd.isna(minutos):
        return "00:00 min"
        
    if minutos >= 60:
        horas = int(minutos // 60)
        minutos_restantes = int(minutos % 60)
        return f"{horas:02d}:{minutos_restantes:02d} h"
    else:
        minutos_parte = int(minutos)
        segundos_parte = int((minutos - minutos_parte) * 60)
        return f"{minutos_parte:02d}:{segundos_parte:02d} min"

def formatar_card(titulo, conteudo, estilo="default"):
    """Formata um card com título e conteúdo"""
    cores = {
        "default": "#ddd",
        "warning": "#ff4b4b",
    }
    bg_cores = {
        "default": "rgba(255,255,255,0)",
        "warning": "rgba(255,75,75,0.05)",
    }
    
    return f"""
    <div style='border:1px solid {cores[estilo]}; border-radius:5px; padding:15px; margin-bottom:20px; background-color:{bg_cores[estilo]};'>
        <p style='font-size:1.1em; font-weight:bold; margin:0 0 10px 0;'>{titulo}</p>
        {conteudo}
    </div>
    """

def formatar_lista(items, separador="\n"):
    """Formata uma lista de items com separador personalizado"""
    return separador.join(items)

def calcular_metricas_gerais(dados, filtros):
    """Calcula métricas gerais para o período selecionado"""
    df = dados['base']
    
    # Aplicar filtros de data
    mask = (
        (df['retirada'].dt.date >= filtros['periodo2']['inicio']) &
        (df['retirada'].dt.date <= filtros['periodo2']['fim'])
    )
    
    # Aplicar filtros adicionais
    if filtros['cliente'] != ['Todos']:
        mask &= df['CLIENTE'].isin(filtros['cliente'])
    if filtros['operacao'] != ['Todas']:
        mask &= df['OPERAÇÃO'].isin(filtros['operacao'])
    if filtros['turno'] != ['Todos']:
        mask &= df['retirada'].dt.hour.apply(lambda x: 'A' if 7 <= x < 15 else ('B' if 15 <= x < 23 else 'C')).isin(filtros['turno'])
    
    df_filtrado = df[mask]
    
    # Cálculo das métricas
    total_atendimentos = len(df_filtrado)
    media_tempo_atendimento = df_filtrado['tpatend'].mean() / 60  # em minutos
    media_tempo_espera = df_filtrado['tpesper'].mean() / 60  # em minutos
    media_permanencia = df_filtrado['tempo_permanencia'].mean() / 60  # em minutos
    
    return {
        'total_atendimentos': total_atendimentos,
        'media_tempo_atendimento': media_tempo_atendimento,
        'media_tempo_espera': media_tempo_espera,
        'media_permanencia': media_permanencia
    }

def criar_grafico_atendimentos_diarios(dados, filtros):
    """Cria gráfico de atendimentos diários"""
    df = dados['base']
    
    # Agrupa dados por data
    df_diario = df.groupby(df['retirada'].dt.date).size().reset_index()
    df_diario.columns = ['data', 'quantidade']
    
    # Cria o gráfico
    fig = px.line(
        df_diario, 
        x='data', 
        y='quantidade',
        title='Atendimentos Diários',
        labels={'data': 'Data', 'quantidade': 'Quantidade de Atendimentos'}
    )
    
    return fig

def criar_grafico_top_clientes(dados, filtros):
    """Cria gráfico dos top 10 clientes"""
    df = dados['base']
    
    # Agrupa dados por cliente
    df_clientes = df.groupby('CLIENTE').size().reset_index()
    df_clientes.columns = ['cliente', 'quantidade']
    df_clientes = df_clientes.sort_values('quantidade', ascending=True).tail(10)
    
    # Cria o gráfico
    fig = px.bar(
        df_clientes,
        x='quantidade',
        y='cliente',
        title='Top 10 Clientes',
        orientation='h',
        labels={
            'quantidade': 'Quantidade de Atendimentos',
            'cliente': 'Cliente'
        },
        text='quantidade'  # Adiciona os valores nas barras
    )
    
    # Atualiza o layout para garantir que os rótulos apareçam
    fig.update_layout(
        xaxis_title="Quantidade de Atendimentos",
        yaxis_title="Cliente",
        title_x=0.5,
        margin=dict(l=10, r=120, t=40, b=10),  # Aumenta margem direita para 120
        height=400,  # Define altura fixa
        uniformtext=dict(minsize=10, mode='show')  # Garante visibilidade uniforme do texto
    )
    
    # Atualiza os eixos e o formato do texto
    fig.update_traces(
        textposition='outside',
        textangle=0,  # Mantém o texto horizontal
        cliponaxis=False  # Impede que o texto seja cortado
    )
    fig.update_xaxes(showgrid=True)
    fig.update_yaxes(showgrid=False)
    
    return fig

def gerar_insights_gerais(dados, filtros, metricas):
    """Gera insights sobre as operações gerais"""
    df = dados['base']
    
    # Aplicar filtros de data
    mask = (
        (df['retirada'].dt.date >= filtros['periodo2']['inicio']) &
        (df['retirada'].dt.date <= filtros['periodo2']['fim'])
    )
    
    # Aplicar filtros adicionais
    if filtros['cliente'] != ['Todos']:
        mask &= df['CLIENTE'].isin(filtros['cliente'])
    if filtros['operacao'] != ['Todas']:
        mask &= df['OPERAÇÃO'].isin(filtros['operacao'])
    if filtros['turno'] != ['Todos']:
        mask &= df['retirada'].dt.hour.apply(lambda x: 'A' if 7 <= x < 15 else ('B' if 15 <= x < 23 else 'C')).isin(filtros['turno'])
    
    df = df[mask]
    
    # Análise por períodos do dia
    df['hora'] = df['retirada'].dt.hour
    manha = df[df['hora'].between(6, 11)]['id'].count()
    tarde = df[df['hora'].between(12, 17)]['id'].count()
    noite = df[df['hora'].between(18, 23)]['id'].count()
    total = manha + tarde + noite
    
    # Evitar divisão por zero
    total = max(total, 1)  # Se total for 0, usa 1 para evitar divisão por zero
    
    # Análise de eficiência
    tempo_meta = filtros.get('meta_permanencia', 30)
    atendimentos_eficientes = df[df['tempo_permanencia'] <= tempo_meta * 60]['id'].count()
    taxa_eficiencia = (atendimentos_eficientes / len(df) * 100) if len(df) > 0 else 0
    
    # Análise de pontos fora da meta
    tempo_meta_segundos = tempo_meta * 60
    df['status_meta'] = df['tempo_permanencia'].apply(lambda x: 'Dentro' if x <= tempo_meta_segundos else 'Fora')
    pontos_fora = df[df['status_meta'] == 'Fora']

    # Análise detalhada dos pontos fora da meta
    dias_criticos = df[df['status_meta'] == 'Fora'].groupby(df['retirada'].dt.date).size().sort_values(ascending=False)
    clientes_criticos = df[df['status_meta'] == 'Fora'].groupby('CLIENTE').size().sort_values(ascending=False)
    operacoes_criticas = df[df['status_meta'] == 'Fora'].groupby('OPERAÇÃO').size().sort_values(ascending=False)

    # Análise de dias da semana
    df['dia_semana'] = df['retirada'].dt.day_name()
    dias_semana_fora = df[df['status_meta'] == 'Fora'].groupby('dia_semana').size()
    
    # Análise de horários críticos
    df['hora_completa'] = df['retirada'].dt.hour
    horas_criticas = df[df['status_meta'] == 'Fora'].groupby('hora_completa').size().sort_values(ascending=False)

    # Análise de picos
    pico_espera = df.nlargest(3, 'tpesper')[['retirada', 'CLIENTE', 'OPERAÇÃO', 'tpesper']]
    pico_permanencia = df.nlargest(3, 'tempo_permanencia')[['retirada', 'CLIENTE', 'OPERAÇÃO', 'tempo_permanencia']]

    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("📊 Visão Geral do Período")
        st.markdown(formatar_card(
            "Resumo do Período",
            f"""
            📌 Atendimentos totais: {len(df):,}
            ⏱️ Tempo médio total: {formatar_tempo(df['tempo_permanencia'].mean() / 60)}
            📈 Taxa de eficiência: {taxa_eficiencia:.1f}%
            """
        ), unsafe_allow_html=True)
        
        st.markdown(formatar_card(
            "⏰ Indicadores de Tempo",
            f"""
            ⏳ Tempo médio de espera: {formatar_tempo(df['tpesper'].mean() / 60)}
            ⚡ Tempo médio de atendimento: {formatar_tempo(df['tpatend'].mean() / 60)}
            🎯 Meta de permanência: {tempo_meta}:00 min
            """
        ), unsafe_allow_html=True)

    with col2:
        st.subheader("🎯 Análise de Metas")
        st.markdown(formatar_card(
            "Desempenho",
            f"""
            ✅ Dentro da meta: {len(df[df['status_meta'] == 'Dentro']):,} ({(len(df[df['status_meta'] == 'Dentro'])/len(df)*100):.1f}%)
            ❌ Fora da meta: {len(pontos_fora):,} ({(len(pontos_fora)/len(df)*100):.1f}%)
            """
        ), unsafe_allow_html=True)

        st.markdown(formatar_card(
            "Pontos Críticos",
            f"""
            📅 Top 3 Dias:
            • {dias_criticos.head(3).index[0].strftime('%d/%m/%Y')}: {dias_criticos.head(3).values[0]:,} atendimentos
            • {dias_criticos.head(3).index[1].strftime('%d/%m/%Y')}: {dias_criticos.head(3).values[1]:,} atendimentos
            • {dias_criticos.head(3).index[2].strftime('%d/%m/%Y')}: {dias_criticos.head(3).values[2]:,} atendimentos
            """
        ), unsafe_allow_html=True)

        st.markdown(formatar_card(
            "Principais Impactos",
            f"""
            👥 Top 3 Clientes:
            • {clientes_criticos.head(3).index[0]}: {clientes_criticos.head(3).values[0]:,} atendimentos
            • {clientes_criticos.head(3).index[1]}: {clientes_criticos.head(3).values[1]:,} atendimentos
            • {clientes_criticos.head(3).index[2]}: {clientes_criticos.head(3).values[2]:,} atendimentos
            """
        ), unsafe_allow_html=True)

    with col3:
        st.subheader("⚠️ Análise de Picos")
        st.markdown(formatar_card(
            "Maiores Tempos de Espera",
            formatar_lista([
                f"""
                📍 {formatar_tempo(row['tpesper']/60)}
                📅 {row['retirada'].strftime('%d/%m/%Y %H:%M')}
                👥 {row['CLIENTE']}
                🔧 {row['OPERAÇÃO']}
                """
                for _, row in pico_espera.iterrows()
            ], "\n\n"),
            estilo="warning"
        ), unsafe_allow_html=True)

        st.markdown(formatar_card(
            "Maiores Tempos de Permanência",
            formatar_lista([
                f"""
                📍 {formatar_tempo(row['tempo_permanencia']/60)}
                📅 {row['retirada'].strftime('%d/%m/%Y %H:%M')}
                👥 {row['CLIENTE']}
                🔧 {row['OPERAÇÃO']}
                """
                for _, row in pico_permanencia.iterrows()
            ], "\n\n"),
            estilo="warning"
        ), unsafe_allow_html=True)

def mostrar_aba(dados, filtros):
    """Mostra a aba Geral do dashboard"""
    st.header("Visão Geral das Operações")
    
    try:
        # Cálculo das métricas gerais
        metricas = calcular_metricas_gerais(dados, filtros)
        
        # Layout das métricas em colunas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total de Atendimentos",
                f"{metricas['total_atendimentos']:,} atendimentos",
                help="Número total de atendimentos no período"
            )
        
        with col2:
            st.metric(
                "Tempo Médio de Atendimento",
                formatar_tempo(metricas['media_tempo_atendimento']),
                help="Tempo médio de atendimento no período"
            )
        
        with col3:
            st.metric(
                "Tempo Médio de Espera",
                formatar_tempo(metricas['media_tempo_espera']),
                help="Tempo médio de espera em fila no período"
            )
        
        with col4:
            st.metric(
                "Tempo Médio de Permanência",
                formatar_tempo(metricas['media_permanencia']),
                help="Tempo médio total (espera + atendimento)"
            )
        
        # Gráficos
        col_left, col_right = st.columns(2)
        
        with col_left:
            fig_diario = criar_grafico_atendimentos_diarios(dados, filtros)
            st.plotly_chart(fig_diario, use_container_width=True)
        
        with col_right:
            fig_clientes = criar_grafico_top_clientes(dados, filtros)
            st.plotly_chart(fig_clientes, use_container_width=True)
        
        # Insights
        st.markdown("---")
        st.subheader("📈 Análise Detalhada")
        with st.expander("Ver análise completa", expanded=True):
            gerar_insights_gerais(dados, filtros, metricas)
    
    except Exception as e:
        st.error("Erro ao gerar a aba Geral")
        st.exception(e)