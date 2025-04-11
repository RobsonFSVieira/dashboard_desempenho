import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

def calcular_tempo_ocioso(dados, filtros, intervalo_almoco=60):
    """Calcula tempo ocioso por colaborador"""
    df = dados['base']
    
    # Aplicar filtros de data
    mask = (
        (df['retirada'].dt.date >= filtros['periodo2']['inicio']) &
        (df['retirada'].dt.date <= filtros['periodo2']['fim'])
    )
    df_filtrado = df[mask]
    
    # Agrupar por colaborador e data
    df_analise = df_filtrado.groupby(['usuário', df_filtrado['inicio'].dt.date]).agg({
        'inicio': ['min', 'max'],  # Primeiro e último atendimento
        'id': 'count',             # Quantidade de atendimentos
        'tpatend': 'sum'           # Tempo total em atendimento
    }).reset_index()
    
    # Renomear colunas
    df_analise.columns = ['colaborador', 'data', 'primeiro_atend', 
                         'ultimo_atend', 'qtd_atendimentos', 'tempo_total_atend']
    
    # Calcular tempo teórico de trabalho (em segundos)
    df_analise['tempo_trabalho'] = (
        df_analise['ultimo_atend'] - df_analise['primeiro_atend']
    ).dt.total_seconds()
    
    # Subtrair intervalo de almoço (convertido para segundos)
    df_analise['tempo_trabalho'] = df_analise['tempo_trabalho'] - (intervalo_almoco * 60)
    
    # Calcular tempo ocioso (tempo de trabalho - tempo em atendimento)
    df_analise['tempo_ocioso'] = df_analise['tempo_trabalho'] - df_analise['tempo_total_atend']
    
    # Converter para minutos
    df_analise['tempo_ocioso'] = df_analise['tempo_ocioso'] / 60
    df_analise['tempo_trabalho'] = df_analise['tempo_trabalho'] / 60
    df_analise['tempo_total_atend'] = df_analise['tempo_total_atend'] / 60
    
    return df_analise

def criar_grafico_ociosidade(dados_ociosidade):
    """Cria gráfico de análise de ociosidade"""
    # Calcular médias por colaborador
    medias = dados_ociosidade.groupby('colaborador').agg({
        'tempo_ocioso': 'mean',
        'tempo_trabalho': 'mean',
        'tempo_total_atend': 'mean',
        'qtd_atendimentos': 'mean'
    }).reset_index()
    
    # Ordenar por tempo ocioso
    medias = medias.sort_values('tempo_ocioso', ascending=True)
    
    # Criar figura
    fig = go.Figure()
    
    # Adicionar barras empilhadas
    fig.add_trace(
        go.Bar(
            name='Tempo em Atendimento',
            y=medias['colaborador'],
            x=medias['tempo_total_atend'],
            orientation='h',
            marker_color='darkblue'
        )
    )
    
    fig.add_trace(
        go.Bar(
            name='Tempo Ocioso',
            y=medias['colaborador'],
            x=medias['tempo_ocioso'],
            orientation='h',
            marker_color='lightgray'
        )
    )
    
    # Atualizar layout
    fig.update_layout(
        title="Distribuição do Tempo de Trabalho por Colaborador",
        barmode='stack',
        height=400 + (len(medias) * 20),
        xaxis_title="Tempo (minutos)",
        yaxis_title="Colaborador"
    )
    
    return fig

def mostrar_aba(dados, filtros):
    """Mostra a aba de análise de ociosidade"""
    st.header("Análise de Tempo Ocioso")
    st.write("Análise do tempo não utilizado em atendimentos")
    
    try:
        # Configuração do intervalo de almoço
        intervalo = st.slider(
            "Intervalo de Almoço (minutos)",
            min_value=30,
            max_value=120,
            value=60,
            step=15
        )
        
        # Calcular tempos ociosos
        dados_ociosidade = calcular_tempo_ocioso(dados, filtros, intervalo)
        
        # Exibir gráfico
        fig = criar_grafico_ociosidade(dados_ociosidade)
        st.plotly_chart(fig, use_container_width=True)
        
        # Métricas gerais
        st.subheader("📊 Métricas Gerais")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            media_ocioso = dados_ociosidade['tempo_ocioso'].mean()
            st.metric(
                "Média de Tempo Ocioso",
                f"{media_ocioso:.1f} min"
            )
        
        with col2:
            media_atend = dados_ociosidade['tempo_total_atend'].mean()
            st.metric(
                "Média de Tempo em Atendimento",
                f"{media_atend:.1f} min"
            )
        
        with col3:
            percentual_ocioso = (media_ocioso / (media_ocioso + media_atend)) * 100
            st.metric(
                "% Tempo Ocioso",
                f"{percentual_ocioso:.1f}%"
            )
        
        # Insights
        st.subheader("📊 Insights")
        with st.expander("Ver insights"):
            # Análise por colaborador
            medias_colab = dados_ociosidade.groupby('colaborador').agg({
                'tempo_ocioso': 'mean',
                'qtd_atendimentos': 'mean'
            }).reset_index()
            
            st.write("#### Principais Observações:")
            
            # Identificar colaboradores com alto tempo ocioso
            alto_ocioso = medias_colab[
                medias_colab['tempo_ocioso'] > (medias_colab['tempo_ocioso'].mean() + 
                                              medias_colab['tempo_ocioso'].std())
            ]
            
            if not alto_ocioso.empty:
                st.write("**Colaboradores com Tempo Ocioso Elevado:**")
                for _, row in alto_ocioso.iterrows():
                    st.write(
                        f"- {row['colaborador']}: {row['tempo_ocioso']:.1f} min "
                        f"({row['qtd_atendimentos']:.1f} atendimentos/dia)"
                    )
            
            # Sugestões de melhoria
            if percentual_ocioso > 30:
                st.warning(
                    "⚠️ O tempo ocioso está acima de 30%. "
                    "Considere revisar a distribuição de atividades."
                )
    
    except Exception as e:
        st.error("Erro ao gerar a aba de Análise de Ociosidade")
        st.exception(e)