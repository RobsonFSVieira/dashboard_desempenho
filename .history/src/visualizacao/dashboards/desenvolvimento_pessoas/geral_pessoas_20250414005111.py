import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

def formatar_tempo(minutos):
    """Formata o tempo de minutos para o formato hh:mm min ou mm:ss min"""
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
        "success": "#00cc44"
    }
    bg_cores = {
        "default": "rgba(255,255,255,0)",
        "warning": "rgba(255,75,75,0.05)",
        "success": "rgba(0,204,68,0.05)"
    }
    
    return f"""
    <div style='border:1px solid {cores[estilo]}; border-radius:5px; padding:15px; margin-bottom:20px; background-color:{bg_cores[estilo]};'>
        <p style='font-size:1.1em; font-weight:bold; margin:0 0 10px 0;'>{titulo}</p>
        {conteudo}
    </div>
    """

def calcular_metricas_colaborador(dados, filtros):
    """Calcula métricas gerais por colaborador"""
    df = dados['base']
    df_medias = dados['medias']
    
    # Aplicar filtros de data
    mask = (
        (df['retirada'].dt.date >= filtros['periodo2']['inicio']) &
        (df['retirada'].dt.date <= filtros['periodo2']['fim'])
    )
    
    df_filtrado = df[mask]
    
    # Cálculo das métricas por colaborador
    metricas_colab = df_filtrado.groupby('usuário').agg({
        'id': 'count',
        'tpatend': ['mean', 'std'],
        'tpesper': 'mean',
        'tempo_permanencia': 'mean'
    }).reset_index()
    
    # Renomear colunas
    metricas_colab.columns = [
        'colaborador', 'total_atendimentos', 'tempo_medio_atend', 
        'desvio_padrao_atend', 'tempo_medio_espera', 'tempo_medio_total'
    ]
    
    # Converter tempos para minutos
    for col in ['tempo_medio_atend', 'tempo_medio_espera', 'tempo_medio_total']:
        metricas_colab[col] = metricas_colab[col] / 60
    
    return metricas_colab

def criar_grafico_produtividade(dados, metricas_colab):
    """Cria gráfico de produtividade por colaborador"""
    fig = px.bar(
        metricas_colab.sort_values('total_atendimentos', ascending=True),
        x='total_atendimentos',
        y='colaborador',
        orientation='h',
        title='Produtividade por Colaborador',
        labels={
            'total_atendimentos': 'Total de Atendimentos',
            'colaborador': 'Colaborador'
        }
    )
    
    fig.update_layout(
        height=400,
        margin=dict(l=10, r=10, t=40, b=10)
    )
    
    return fig

def criar_grafico_tempos(metricas_colab):
    """Cria gráfico comparativo de tempos por colaborador"""
    fig = go.Figure()
    
    # Adiciona barras para tempo de atendimento
    fig.add_trace(go.Bar(
        name='Tempo de Atendimento',
        y=metricas_colab['colaborador'],
        x=metricas_colab['tempo_medio_atend'],
        orientation='h',
        marker_color='#1864ab'
    ))
    
    # Adiciona barras para tempo de espera
    fig.add_trace(go.Bar(
        name='Tempo de Espera',
        y=metricas_colab['colaborador'],
        x=metricas_colab['tempo_medio_espera'],
        orientation='h',
        marker_color='#83c9ff'
    ))
    
    fig.update_layout(
        title='Tempos Médios por Colaborador',
        barmode='group',
        height=400,
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis_title='Tempo (minutos)',
        yaxis_title='Colaborador'
    )
    
    return fig

def gerar_insights_colaboradores(metricas_colab, dados):
    """Gera insights sobre o desempenho dos colaboradores"""
    df_medias = dados.get('medias')
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Desempenho Geral")
        
        # Métricas gerais
        media_atendimentos = metricas_colab['total_atendimentos'].mean()
        media_tempo_atend = metricas_colab['tempo_medio_atend'].mean()
        
        st.markdown(formatar_card(
            "Indicadores Médios",
            f"""
            👥 Atendimentos por colaborador: {media_atendimentos:.1f}
            ⏱️ Tempo médio de atendimento: {formatar_tempo(media_tempo_atend)}
            📊 Desvio padrão médio: {metricas_colab['desvio_padrao_atend'].mean()/60:.1f} min
            """
        ), unsafe_allow_html=True)
        
        # Destaques positivos
        top_produtividade = metricas_colab.nlargest(3, 'total_atendimentos')
        
        st.markdown(formatar_card(
            "🌟 Destaques em Produtividade",
            "\n".join([
                f"• {row['colaborador']}: {row['total_atendimentos']} atendimentos"
                for _, row in top_produtividade.iterrows()
            ]),
            estilo="success"
        ), unsafe_allow_html=True)
    
    with col2:
        st.subheader("⚠️ Pontos de Atenção")
        
        # Identificar colaboradores com tempos muito acima da média
        media_geral = metricas_colab['tempo_medio_atend'].mean()
        desvio_padrao = metricas_colab['tempo_medio_atend'].std()
        
        acima_media = metricas_colab[
            metricas_colab['tempo_medio_atend'] > (media_geral + desvio_padrao)
        ]
        
        if not acima_media.empty:
            st.markdown(formatar_card(
                "Tempo Acima da Média",
                "\n".join([
                    f"• {row['colaborador']}: {formatar_tempo(row['tempo_medio_atend'])}"
                    for _, row in acima_media.iterrows()
                ]),
                estilo="warning"
            ), unsafe_allow_html=True)
    
    # Análise de consistência
    st.markdown("---")
    st.subheader("📊 Análise de Consistência")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Variabilidade no tempo de atendimento
        alta_variacao = metricas_colab[
            metricas_colab['desvio_padrao_atend'] > desvio_padrao
        ].sort_values('desvio_padrao_atend', ascending=False)
        
        if not alta_variacao.empty:
            st.markdown(formatar_card(
                "Alta Variação no Tempo de Atendimento",
                "\n".join([
                    f"• {row['colaborador']}:"
                    f"\n  - Tempo médio: {formatar_tempo(row['tempo_medio_atend'])}"
                    f"\n  - Desvio: ±{row['desvio_padrao_atend']/60:.1f} min"
                    for _, row in alta_variacao.iterrows()
                ])
            ), unsafe_allow_html=True)
    
    with col2:
        # Comparação com metas
        if df_medias is not None:
            st.markdown(formatar_card(
                "Atingimento de Metas",
                "Análise de metas por operação será implementada em breve."
            ), unsafe_allow_html=True)

def mostrar_aba(dados, filtros):
    """Mostra a aba Geral do dashboard de Desenvolvimento de Pessoas"""
    st.header("Visão Geral do Desenvolvimento")
    
    try:
        # Cálculo das métricas por colaborador
        metricas_colab = calcular_metricas_colaborador(dados, filtros)
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total de Colaboradores",
                len(metricas_colab),
                help="Número de colaboradores ativos no período"
            )
        
        with col2:
            media_atend = metricas_colab['total_atendimentos'].mean()
            st.metric(
                "Média de Atendimentos",
                f"{media_atend:.1f}",
                help="Média de atendimentos por colaborador"
            )
        
        with col3:
            media_tempo = metricas_colab['tempo_medio_atend'].mean()
            st.metric(
                "Tempo Médio de Atendimento",
                formatar_tempo(media_tempo),
                help="Tempo médio de atendimento por colaborador"
            )
        
        with col4:
            media_espera = metricas_colab['tempo_medio_espera'].mean()
            st.metric(
                "Tempo Médio de Espera",
                formatar_tempo(media_espera),
                help="Tempo médio de espera por colaborador"
            )
        
        # Gráficos
        col_left, col_right = st.columns(2)
        
        with col_left:
            fig_prod = criar_grafico_produtividade(dados, metricas_colab)
            st.plotly_chart(fig_prod, use_container_width=True)
        
        with col_right:
            fig_tempos = criar_grafico_tempos(metricas_colab)
            st.plotly_chart(fig_tempos, use_container_width=True)
        
        # Insights
        st.markdown("---")
        with st.expander("📈 Ver Análise Detalhada", expanded=True):
            gerar_insights_colaboradores(metricas_colab, dados)
    
    except Exception as e:
        st.error("Erro ao gerar a aba Geral")
        st.exception(e)
