import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import timedelta

def analisar_colaborador(dados, filtros, colaborador, adicional_filters=None):
    """Analisa dados de um colaborador específico"""
    df = dados['base']
    
    # Calcular médias gerais por operação (todos os usuários)
    mask_periodo = (
        (df['retirada'].dt.date >= filtros['periodo2']['inicio']) &
        (df['retirada'].dt.date <= filtros['periodo2']['fim'])
    )
    medias_gerais = df[mask_periodo].groupby('OPERAÇÃO').agg({
        'tpatend': 'mean'
    }).reset_index()
    medias_gerais['tpatend'] = medias_gerais['tpatend'] / 60
    
    # Aplicar filtros para o colaborador específico
    mask = mask_periodo & (df['usuário'] == colaborador)
    
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
    
    # Adicionar médias gerais como referência
    metricas_op = pd.merge(
        metricas_op,
        medias_gerais.rename(columns={'tpatend': 'meta_tempo'}),
        on='OPERAÇÃO',
        how='left'
    )
    
    # Calcular variação em relação à média geral
    metricas_op['variacao'] = ((metricas_op['tpatend'] - metricas_op['meta_tempo']) / 
                              metricas_op['meta_tempo'] * 100)
    
    return metricas_op

def criar_grafico_operacoes(metricas_op):
    """Cria gráfico comparativo por operação"""
    # Ordenar dados para os gráficos
    dados_qtd = metricas_op.sort_values('id', ascending=True)
    dados_tempo = metricas_op.sort_values('tpatend', ascending=False)

    # Criar rótulos personalizados para tempo médio com cores
    tempo_labels = []
    for i, row in dados_tempo.iterrows():
        var_pct = ((row['tpatend'] - row['meta_tempo']) / row['meta_tempo'] * 100)
        # Verde se negativo (mais rápido), vermelho se positivo (mais lento)
        cor = 'red' if var_pct > 0 else 'green'
        tempo_labels.append(
            f"<b>{row['tpatend']:.1f} min <span style='color: {cor}'>({var_pct:+.1f}%)</span></b>"
        )

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("<b>Quantidade de Atendimentos</b>", "<b>Tempo Médio de Atendimento</b>"),
        specs=[[{"type": "bar"}, {"type": "bar"}]],
        horizontal_spacing=0.20,  # Aumentado de 0.15 para 0.20
        column_widths=[0.35, 0.65]  # Define proporção 35%-65% entre as colunas
    )
    
    # Gráfico de quantidade - barra horizontal (maiores quantidades no topo)
    fig.add_trace(
        go.Bar(
            y=dados_qtd['OPERAÇÃO'],
            x=dados_qtd['id'],
            name="<b>Atendimentos</b>",
            text=["<b>" + str(val) + "</b>" for val in dados_qtd['id']],
            textposition='outside',
            marker_color='royalblue',
            orientation='h'
        ),
        row=1, col=1
    )
    
    # Gráfico de tempo médio com rótulos personalizados
    fig.add_trace(
        go.Bar(
            y=dados_tempo['OPERAÇÃO'],
            x=dados_tempo['tpatend'],
            name="<b>Tempo Médio</b>",
            text=tempo_labels,
            textposition='outside',
            marker_color='lightblue',
            orientation='h'
        ),
        row=1, col=2
    )
    
    # Adicionar linha de meta por operação
    fig.add_trace(
        go.Scatter(
            y=dados_tempo['OPERAÇÃO'],
            x=dados_tempo['meta_tempo'],
            name="<b>Meta (Média Geral)</b>",
            mode='lines+markers',
            line=dict(color='red', dash='dash'),
            marker=dict(symbol='diamond', size=8)
        ),
        row=1, col=2
    )
    
    # Calcular o valor máximo para o eixo X do gráfico de tempo
    max_tempo = max(dados_tempo['tpatend'].max(), dados_tempo['meta_tempo'].max())
    # Adicionar 30% de margem para acomodar os rótulos
    max_tempo_with_margin = max_tempo * 1.3

    # Atualizar layout com margens e limites ajustados
    fig.update_layout(
        height=max(400, len(metricas_op) * 40),
        showlegend=True,
        title_text="<b>Análise por Operação</b>",
        margin=dict(t=50, b=20, l=20, r=150)  # Aumentada margem direita para 150
    )
    
    # Atualizar eixos com limites definidos
    fig.update_xaxes(title_text="<b>Quantidade</b>", row=1, col=1)
    fig.update_xaxes(
        title_text="<b>Minutos</b>",
        range=[0, max_tempo_with_margin],  # Define limite do eixo X
        row=1, col=2
    )
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
        # Debug de períodos
        df = dados['base']
        data_min = df['retirada'].dt.date.min()
        data_max = df['retirada'].dt.date.max()
        
        # Verificar se o período selecionado está contido nos dados
        if (filtros['periodo2']['inicio'] < data_min or 
            filtros['periodo2']['fim'] > data_max):
            
            st.warning(
                f"⚠️ Período selecionado ({filtros['periodo2']['inicio'].strftime('%d/%m/%Y')} "
                f"a {filtros['periodo2']['fim'].strftime('%d/%m/%Y')}) está fora do intervalo "
                f"disponível na base de dados ({data_min.strftime('%d/%m/%Y')} a "
                f"{data_max.strftime('%d/%m/%Y')})"
            )
            return
        
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
