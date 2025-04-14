import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

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
    fig = go.Figure()
    
    # Adiciona barras de senhas retiradas
    fig.add_trace(
        go.Bar(
            name='Senhas Retiradas',
            x=metricas_hora['hora'],
            y=metricas_hora['retiradas'],
            marker_color='rgba(99, 110, 250, 0.6)'  # Azul claro com transparência
        )
    )
    
    # Adiciona barras de senhas atendidas
    fig.add_trace(
        go.Bar(
            name='Senhas Atendidas',
            x=metricas_hora['hora'],
            y=metricas_hora['atendidas'],
            marker_color='rgba(25, 25, 112, 0.7)'  # Azul escuro com transparência
        )
    )
    
    # Adiciona linha de senhas pendentes
    fig.add_trace(
        go.Scatter(
            name='Senhas Pendentes',
            x=metricas_hora['hora'],
            y=metricas_hora['pendentes'],
            mode='lines+markers',
            line=dict(color='rgba(255, 0, 0, 0.8)', width=2),  # Vermelho com transparência
            marker=dict(size=6, symbol='circle')
        )
    )
    
    # Atualiza layout
    titulo = f"Análise Hora a Hora {'- ' + cliente if cliente else 'Geral'}"
    fig.update_layout(
        title=dict(
            text=titulo,
            x=0.5,
            xanchor='center',
            font=dict(size=20)
        ),
        xaxis_title=dict(text="Hora do Dia", font=dict(size=14)),
        yaxis_title=dict(text="Quantidade de Senhas", font=dict(size=14)),
        barmode='group',
        height=500,
        showlegend=True,
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(
            tickmode='linear',
            tick0=0,
            dtick=1,
            gridcolor='rgba(200, 200, 200, 0.2)',
            showgrid=True,
            zeroline=False
        ),
        yaxis=dict(
            gridcolor='rgba(200, 200, 200, 0.2)',
            showgrid=True,
            zeroline=False
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        )
    )
    
    return fig

def mostrar_aba(dados, filtros):
    """Mostra a aba de análise detalhada de chegada em comboio"""
    st.header("Análise de Chegada em Comboio II")
    st.write("Análise hora a hora de senhas retiradas, atendidas e pendentes")
    
    try:
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