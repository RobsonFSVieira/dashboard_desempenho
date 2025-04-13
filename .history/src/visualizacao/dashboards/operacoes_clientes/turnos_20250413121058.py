import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def identificar_turno(hora):
    """Identifica o turno com base na hora"""
    if 7 <= hora < 15:
        return 'A'
    elif 15 <= hora < 23:
        return 'B'
    else:
        return 'C'

def calcular_metricas_turno(dados, filtros):
    """Calcula métricas por turno"""
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
    
    df_filtrado = df[mask]
    
    # Identificar turno
    df_filtrado['turno'] = df_filtrado['retirada'].dt.hour.apply(identificar_turno)
    
    # Calcular métricas por turno
    metricas = df_filtrado.groupby('turno').agg({
        'id': 'count',
        'tpatend': 'mean',
        'tpesper': 'mean',
        'tempo_permanencia': 'mean'
    }).reset_index()
    
    # Converter tempos para minutos
    for col in ['tpatend', 'tpesper', 'tempo_permanencia']:
        metricas[col] = metricas[col] / 60
    
    return metricas

def criar_graficos_turno(metricas):
    """Cria conjunto de gráficos para análise por turno"""
    # Criar subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Quantidade de Atendimentos por Turno',
            'Tempo Médio de Atendimento por Turno',
            'Tempo Médio de Espera por Turno',
            'Tempo Médio de Permanência por Turno'
        )
    )
    
    # Gráfico 1: Quantidade de atendimentos
    fig.add_trace(
        go.Bar(
            x=metricas['turno'],
            y=metricas['id'],
            name='Quantidade',
            marker_color='darkblue'
        ),
        row=1, col=1
    )
    
    # Gráfico 2: Tempo médio de atendimento
    fig.add_trace(
        go.Bar(
            x=metricas['turno'],
            y=metricas['tpatend'],
            name='Tempo Atendimento',
            marker_color='lightblue'
        ),
        row=1, col=2
    )
    
    # Gráfico 3: Tempo médio de espera
    fig.add_trace(
        go.Bar(
            x=metricas['turno'],
            y=metricas['tpesper'],
            name='Tempo Espera',
            marker_color='lightgray'
        ),
        row=2, col=1
    )
    
    # Gráfico 4: Tempo médio de permanência
    fig.add_trace(
        go.Bar(
            x=metricas['turno'],
            y=metricas['tempo_permanencia'],
            name='Tempo Total',
            marker_color='darkgray'
        ),
        row=2, col=2
    )
    
    # Atualizar layout
    fig.update_layout(
        height=800,
        title_text="Análise por Turno",
        showlegend=False
    )
    
    return fig

def mostrar_aba(dados, filtros):
    """Mostra a aba de análise por Turno"""
    st.header("Análise por Turno")
    
    try:
        # Calcular métricas por turno
        metricas = calcular_metricas_turno(dados, filtros)
        
        # Mostrar gráficos
        fig = criar_graficos_turno(metricas)
        st.plotly_chart(fig, use_container_width=True)
        
        # Insights
        st.subheader("📊 Insights")
        with st.expander("Ver insights"):
            # Encontrar turno mais movimentado
            turno_max = metricas.loc[metricas['id'].idxmax()]
            
            # Encontrar turno com maior tempo de espera
            turno_espera = metricas.loc[metricas['tpesper'].idxmax()]
            
            st.write("#### Principais Observações:")
            
            st.write(f"**Turno mais movimentado:** Turno {turno_max['turno']}")
            st.write(f"- {turno_max['id']} atendimentos")
            st.write(f"- {turno_max['tempo_permanencia']:.1f} min de permanência média")
            
            st.write(f"\n**Turno com maior tempo de espera:** Turno {turno_espera['turno']}")
            st.write(f"- {turno_espera['tpesper']:.1f} min de espera média")
            st.write(f"- {turno_espera['id']} atendimentos")
            
            # Comparação entre turnos
            st.write("\n**Distribuição dos Atendimentos:**")
            for _, row in metricas.iterrows():
                percentual = (row['id'] / metricas['id'].sum()) * 100
                st.write(f"- Turno {row['turno']}: {percentual:.1f}% dos atendimentos")
    
    except Exception as e:
        st.error("Erro ao gerar a aba de Análise por Turno")
        st.exception(e)