import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def calcular_gates_por_hora(dados, filtros, operacao=None):
    """Calcula métricas de gates ativos por hora"""
    df = dados['base']
    
    # Aplicar filtros de data para período 2
    mask = (
        (df['retirada'].dt.date >= filtros['periodo2']['inicio']) &
        (df['retirada'].dt.date <= filtros['periodo2']['fim'])
    )
    df_filtrado = df[mask]
    
    # Filtrar por operação se especificado
    if operacao and operacao != "Todas":
        df_filtrado = df_filtrado[df_filtrado['OPERAÇÃO'] == operacao]
    
    # Criar DataFrame com métricas por hora
    metricas_hora = pd.DataFrame()
    metricas_hora['hora'] = range(24)
    
    # Calcular gates ativos por hora
    gates_hora = df_filtrado.groupby([df_filtrado['inicio'].dt.hour])['guichê'].nunique()
    metricas_hora['gates_ativos'] = metricas_hora['hora'].map(gates_hora).fillna(0)
    
    # Calcular senhas retiradas e atendidas
    retiradas = df_filtrado.groupby(df_filtrado['retirada'].dt.hour)['id'].count()
    atendidas = df_filtrado.groupby(df_filtrado['inicio'].dt.hour)['id'].count()
    
    metricas_hora['retiradas'] = metricas_hora['hora'].map(retiradas).fillna(0)
    metricas_hora['atendidas'] = metricas_hora['hora'].map(atendidas).fillna(0)
    
    return metricas_hora

def criar_grafico_gates(metricas_hora, operacao=None):
    """Cria gráfico comparativo de gates ativos e senhas"""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Adiciona barras de senhas retiradas
    fig.add_trace(
        go.Bar(
            name='Senhas Retiradas',
            x=metricas_hora['hora'],
            y=metricas_hora['retiradas'],
            marker_color='lightblue'
        ),
        secondary_y=False
    )
    
    # Adiciona barras de senhas atendidas
    fig.add_trace(
        go.Bar(
            name='Senhas Atendidas',
            x=metricas_hora['hora'],
            y=metricas_hora['atendidas'],
            marker_color='darkblue'
        ),
        secondary_y=False
    )
    
    # Adiciona linha de gates ativos
    fig.add_trace(
        go.Scatter(
            name='Gates Ativos',
            x=metricas_hora['hora'],
            y=metricas_hora['gates_ativos'],
            mode='lines+markers',
            line=dict(color='red', width=2),
            marker=dict(size=8)
        ),
        secondary_y=True
    )
    
    # Atualiza layout
    titulo = f"Gates em Atividade {'- ' + operacao if operacao else 'Geral'}"
    fig.update_layout(
        title=titulo,
        barmode='group',
        height=500,
        showlegend=True,
        xaxis=dict(
            title="Hora do Dia",
            tickmode='linear',
            tick0=0,
            dtick=1
        )
    )
    
    # Atualiza títulos dos eixos Y
    fig.update_yaxes(title_text="Quantidade de Senhas", secondary_y=False)
    fig.update_yaxes(title_text="Quantidade de Gates", secondary_y=True)
    
    return fig

def mostrar_aba(dados, filtros):
    """Mostra a aba de análise de Gates em Atividade"""
    st.header("Gates em Atividade")
    st.write("Análise da quantidade de gates ativos em relação à demanda")
    
    with st.expander("ℹ️ Como funciona?"):
        st.markdown("""
        ### Como analisamos os Gates em Atividade?

        1. **Métricas Analisadas**:
        - **Gates Ativos**: Quantidade de guichês operando simultaneamente
        - **Senhas Retiradas**: Volume de senhas geradas por hora
        - **Senhas Atendidas**: Volume de atendimentos realizados

        2. **Distribuição por Horário**:
        - **Manhã**: 06:00h às 13:59h
        - **Tarde**: 14:00h às 21:59h
        - **Noite**: 22:00h às 05:59h

        3. **Indicadores**:
        - ✅ Bem dimensionado: Gates suficientes para a demanda
        - ⚠️ Subdimensionado: Mais senhas que capacidade
        - ⚠️ Superdimensionado: Gates ociosos

        4. **Análise de Eficiência**:
        - 📊 Gates ativos vs. Demanda
        - 📈 Média de atendimentos por gate
        - ⏱️ Distribuição ao longo do dia

        5. **Insights Gerados**:
        - 🎯 Dimensionamento ideal
        - 💡 Sugestões de otimização
        - ⚠️ Alertas de ajustes necessários
        """)

    try:
        # Seleção de visualização
        tipo_analise = st.radio(
            "Visualizar:",
            ["Geral", "Por Operação"],
            horizontal=True
        )
        
        if tipo_analise == "Por Operação":
            # Lista de operações disponíveis
            operacoes = ["Todas"] + sorted(dados['base']['OPERAÇÃO'].unique().tolist())
            operacao_selecionada = st.selectbox(
                "Selecione a Operação:",
                operacoes
            )
            
            # Calcular métricas e criar gráfico
            metricas = calcular_gates_por_hora(dados, filtros, operacao_selecionada)
            fig = criar_grafico_gates(metricas, operacao_selecionada)
        else:
            # Calcular métricas e criar gráfico geral
            metricas = calcular_gates_por_hora(dados, filtros)
            fig = criar_grafico_gates(metricas)
        
        # Exibir gráfico
        st.plotly_chart(fig, use_container_width=True)
        
        # Insights
        st.subheader("📊 Insights")
        with st.expander("Ver insights"):
            # Análise de eficiência
            media_gates = metricas['gates_ativos'].mean()
            max_gates = metricas['gates_ativos'].max()
            hora_pico = metricas.loc[metricas['retiradas'].idxmax()]
            
            st.write("#### Principais Observações:")
            st.write(f"**Média de Gates Ativos:** {media_gates:.1f}")
            st.write(f"**Máximo de Gates Simultâneos:** {int(max_gates)}")
            
            # Horário de pico
            st.write(f"\n**Horário de Maior Demanda:** {int(hora_pico['hora']):02d}:00h")
            st.write(f"- Senhas Retiradas: {int(hora_pico['retiradas'])}")
            st.write(f"- Gates Ativos: {int(hora_pico['gates_ativos'])}")
            st.write(f"- Senhas por Gate: {(hora_pico['retiradas']/hora_pico['gates_ativos']):.1f}")
            
            # Recomendações
            if hora_pico['retiradas'] > (hora_pico['gates_ativos'] * 15):  # Assumindo capacidade de 15 atendimentos/hora/gate
                st.warning("⚠️ Possível subdimensionamento de gates no horário de pico")
    
    except Exception as e:
        st.error("Erro ao gerar a aba de Gates em Atividade")
        st.exception(e)