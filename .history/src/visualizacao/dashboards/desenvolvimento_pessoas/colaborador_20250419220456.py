import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import timedelta

def analisar_colaborador(dados, filtros, colaborador, adicional_filters=None):
    """Analisa dados de um colaborador específico"""
    df = dados['base']
    
    # Aplicar filtros de data
    mask = (
        (df['retirada'].dt.date >= filtros['periodo2']['inicio']) &
        (df['retirada'].dt.date <= filtros['periodo2']['fim']) &
        (df['usuário'] == colaborador)
    )
    
    # Aplicar filtros adicionais
    if adicional_filters:
        if adicional_filters['turno'] != "Todos":
            # Mapear hora para turno
            df['turno'] = df['inicio'].dt.hour.map(
                lambda x: 'TURNO A' if 6 <= x < 14 else ('TURNO B' if 14 <= x < 22 else 'TURNO C')
            )
            mask &= (df['turno'] == adicional_filters['turno'])
        
        if adicional_filters['cliente'] != "Todos":
            mask &= (df['CLIENTE'] == adicional_filters['cliente'])
    
    df_filtrado = df[mask]
    
    # Métricas por operação
    metricas_op = df_filtrado.groupby('OPERAÇÃO').agg({
        'id': 'count',
        'tpatend': 'mean',
        'tpesper': 'mean'
    }).reset_index()
    
    # Converter tempos para minutos
    metricas_op['tpatend'] = metricas_op['tpatend'] / 60
    metricas_op['tpesper'] = metricas_op['tpesper'] / 60
    
    # Usar média geral como meta
    metricas_op['meta_tempo'] = df_filtrado['tpatend'].mean() / 60
    
    # Calcular variação
    metricas_op['variacao'] = ((metricas_op['tpatend'] - metricas_op['meta_tempo']) / 
                              metricas_op['meta_tempo'] * 100)
    
    return metricas_op

def criar_grafico_operacoes(metricas_op):
    """Cria gráfico comparativo por operação"""
    # Ordenar dados para os gráficos
    dados_qtd = metricas_op.sort_values('id', ascending=True)  # Para o gráfico de barras ficar de baixo para cima
    dados_tempo = metricas_op.sort_values('tpatend', ascending=False)  # Tempos maiores em baixo

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Quantidade de Atendimentos", "Tempo Médio vs Meta"),
        specs=[[{"type": "bar"}, {"type": "bar"}]]
    )
    
    # Gráfico de quantidade - barra horizontal (maiores quantidades no topo)
    fig.add_trace(
        go.Bar(
            y=dados_qtd['OPERAÇÃO'],
            x=dados_qtd['id'],
            name="Atendimentos",
            text=dados_qtd['id'],
            textposition='auto',
            marker_color='royalblue',
            orientation='h'
        ),
        row=1, col=1
    )
    
    # Gráfico de tempo médio vs meta - barra horizontal (menores tempos no topo)
    fig.add_trace(
        go.Bar(
            y=dados_tempo['OPERAÇÃO'],
            x=dados_tempo['tpatend'],
            name="Tempo Médio",
            text=dados_tempo['tpatend'].round(1),
            textposition='auto',
            marker_color='lightblue',
            orientation='h'
        ),
        row=1, col=2
    )
    
    # Linha de meta - adaptada para horizontal e ordenada igual ao tempo
    fig.add_trace(
        go.Scatter(
            y=dados_tempo['OPERAÇÃO'],
            x=dados_tempo['meta_tempo'],
            name="Meta",
            mode='lines+markers',
            line=dict(color='red', dash='dash')
        ),
        row=1, col=2
    )
    
    # Atualizar layout
    fig.update_layout(
        height=max(400, len(metricas_op) * 40),  # Altura dinâmica baseada no número de operações
        showlegend=True,
        title_text="Análise por Operação"
    )
    
    # Atualizar eixos
    fig.update_xaxes(title_text="Quantidade", row=1, col=1)
    fig.update_xaxes(title_text="Minutos", row=1, col=2)
    fig.update_yaxes(title_text="", row=1, col=1)
    fig.update_yaxes(title_text="", row=1, col=2)
    
    return fig

def criar_grafico_evolucao_diaria(dados, filtros, colaborador):
    """Cria gráfico de evolução diária"""
    df = dados['base']
    # Aplicar filtros de data
    mask = (
        (df['retirada'].dt.date >= filtros['periodo2']['inicio']) &
        (df['retirada'].dt.date <= filtros['periodo2']['fim'])
    )
    df_filtrado = df[mask & (df['usuário'] == colaborador)]
    
    # Agrupar por dia
    evolucao = df_filtrado.groupby(df_filtrado['retirada'].dt.date).agg({
        'id': 'count',
        'tpatend': 'mean'
    }).reset_index()
    
    evolucao['tpatend'] = evolucao['tpatend'] / 60
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Atendimentos por Dia", "Tempo Médio por Dia"),
        specs=[[{"type": "scatter"}, {"type": "scatter"}]]
    )
    
    fig.add_trace(
        go.Scatter(
            x=evolucao['retirada'],
            y=evolucao['id'],
            mode='lines+markers',
            name="Atendimentos",
            line=dict(color='royalblue')
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=evolucao['retirada'],
            y=evolucao['tpatend'],
            mode='lines+markers',
            name="Tempo Médio",
            line=dict(color='lightblue')
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        height=400,
        showlegend=True,
        title_text="Evolução Diária"
    )
    
    return fig

def mostrar_aba(dados, filtros):
    """Mostra a aba de análise individual do colaborador"""
    st.header("Análise Individual do Colaborador")
    
    try:
        # Linha de seletores
        col1, col2, col3 = st.columns(3)
        
        with col1:
            colaboradores = sorted(dados['base']['usuário'].unique())
            colaborador = st.selectbox(
                "Selecione o Colaborador",
                options=colaboradores,
                help="Escolha um colaborador para análise detalhada"
            )
        
        with col2:
            turnos = ["Todos", "TURNO A", "TURNO B", "TURNO C"]
            turno = st.selectbox(
                "Selecione o Turno",
                options=turnos,
                help="Filtre por turno específico"
            )
            
        with col3:
            clientes = ["Todos"] + sorted(dados['base']['CLIENTE'].unique().tolist())
            cliente = st.selectbox(
                "Selecione o Cliente",
                options=clientes,
                help="Filtre por cliente específico"
            )
        
        if colaborador:
            # Análise do colaborador com filtros adicionais
            adicional_filters = {
                'turno': turno,
                'cliente': cliente
            }
            metricas_op = analisar_colaborador(dados, filtros, colaborador, adicional_filters)
            
            # Métricas principais
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total de Atendimentos",
                    metricas_op['id'].sum()
                )
            
            with col2:
                tempo_medio = metricas_op['tpatend'].mean()
                st.metric(
                    "Tempo Médio",
                    f"{tempo_medio:.1f} min"
                )
            
            with col3:
                meta_media = metricas_op['meta_tempo'].mean()
                variacao = ((tempo_medio - meta_media) / meta_media * 100)
                st.metric(
                    "Variação da Meta",
                    f"{variacao:+.1f}%",
                    delta_color="inverse"
                )
            
            with col4:
                tempo_espera = metricas_op['tpesper'].mean()
                st.metric(
                    "Tempo Médio de Espera",
                    f"{tempo_espera:.1f} min"
                )
            
            # Gráficos
            st.plotly_chart(criar_grafico_operacoes(metricas_op), use_container_width=True)
            st.plotly_chart(criar_grafico_evolucao_diaria(dados, filtros, colaborador), use_container_width=True)
            
            # Análise Detalhada
            st.subheader("📊 Análise Detalhada")
            with st.expander("Ver análise", expanded=True):
                # Performance por operação
                st.write("#### Performance por Operação")
                for _, row in metricas_op.iterrows():
                    status = "✅" if abs(row['variacao']) <= 10 else "⚠️"
                    st.write(
                        f"**{row['OPERAÇÃO']}** {status}\n\n"
                        f"- Atendimentos: {row['id']}\n"
                        f"- Tempo Médio: {row['tpatend']:.1f} min\n"
                        f"- Meta: {row['meta_tempo']:.1f} min\n"
                        f"- Variação: {row['variacao']:+.1f}%"
                    )
                
                # Insights gerais
                st.write("#### 📈 Insights")
                
                # Identificar pontos fortes
                melhor_op = metricas_op.loc[metricas_op['variacao'].abs().idxmin()]
                st.write(
                    f"- Melhor performance em **{melhor_op['OPERAÇÃO']}** "
                    f"(variação de {melhor_op['variacao']:+.1f}%)"
                )
                
                # Identificar pontos de melhoria
                pior_op = metricas_op.loc[metricas_op['variacao'].abs().idxmax()]
                if abs(pior_op['variacao']) > 10:
                    st.write(
                        f"- Oportunidade de melhoria em **{pior_op['OPERAÇÃO']}** "
                        f"(variação de {pior_op['variacao']:+.1f}%)"
                    )
                
    except Exception as e:
        st.error("Erro ao analisar dados do colaborador")
        st.exception(e)
