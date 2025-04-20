import streamlit as st
import plotly.graph_objects as go
import pandas as pd

def calcular_metricas_por_periodo(dados, filtros, periodo_key):
    """Calcula métricas por colaborador para um período específico"""
    df = dados['base']
    
    # Aplicar filtros de data
    mask = (
        (df['retirada'].dt.date >= filtros[periodo_key]['inicio']) &
        (df['retirada'].dt.date <= filtros[periodo_key]['fim'])
    )
    
    # Calcular métricas
    metricas = df[mask].groupby('usuário').agg({
        'id': 'count',
        'tpatend': 'mean'
    }).reset_index()
    
    # Converter tempo para minutos
    metricas['tpatend'] = metricas['tpatend'] / 60
    
    return metricas

def criar_grafico_comparativo(dados_p1, dados_p2, filtros):
    """Cria gráfico comparativo entre períodos"""
    # Mesclar dados dos dois períodos
    df_merged = pd.merge(
        dados_p1,
        dados_p2,
        on='usuário',
        suffixes=('_p1', '_p2'),
        how='outer'
    ).fillna(0)
    
    # Calcular variação
    df_merged['variacao'] = ((df_merged['tpatend_p2'] - df_merged['tpatend_p1']) / 
                            df_merged['tpatend_p1'] * 100)
    
    # Ordenar por variação
    df_merged = df_merged.sort_values('variacao', ascending=True)
    
    # Criar figura
    fig = go.Figure()
    
    # Adicionar barras do período 1
    fig.add_trace(
        go.Bar(
            name=f"Período 1 ({filtros['periodo1']['inicio'].strftime('%d/%m')} a {filtros['periodo1']['fim'].strftime('%d/%m')})",
            x=df_merged['usuário'],
            y=df_merged['tpatend_p1'],
            marker_color='lightblue'
        )
    )
    
    # Adicionar barras do período 2
    fig.add_trace(
        go.Bar(
            name=f"Período 2 ({filtros['periodo2']['inicio'].strftime('%d/%m')} a {filtros['periodo2']['fim'].strftime('%d/%m')})",
            x=df_merged['usuário'],
            y=df_merged['tpatend_p2'],
            marker_color='royalblue'
        )
    )
    
    # Adicionar linha de variação
    fig.add_trace(
        go.Scatter(
            name="Variação",
            x=df_merged['usuário'],
            y=df_merged['variacao'],
            yaxis="y2",
            line=dict(color="red", width=2),
            mode='lines+markers',
            marker=dict(
                color=['green' if var < 0 else 'red' for var in df_merged['variacao']],
                size=8
            ),
            hovertemplate="Variação: %{y:.1f}%<extra></extra>"
        )
    )
    
    # Atualizar layout
    fig.update_layout(
        title="<b>Comparativo de Tempo Médio de Atendimento por Colaborador</b>",
        barmode='group',
        height=500,
        yaxis=dict(title="Minutos"),
        yaxis2=dict(
            title="Variação (%)",
            overlaying='y',
            side='right',
            showgrid=False
        ),
        showlegend=True,
        hovermode='x unified'
    )
    
    return fig, df_merged

def mostrar_aba(dados, filtros):
    """Mostra a aba de tempo de atendimento"""
    try:
        # Calcular métricas para cada período
        dados_p1 = calcular_metricas_por_periodo(dados, filtros, 'periodo1')
        dados_p2 = calcular_metricas_por_periodo(dados, filtros, 'periodo2')
        
        # Criar gráfico comparativo
        fig, df_merged = criar_grafico_comparativo(dados_p1, dados_p2, filtros)
        
        # Exibir gráfico
        st.plotly_chart(fig, use_container_width=True)
        
        # Métricas gerais de variação
        col1, col2, col3 = st.columns(3)
        
        with col1:
            var_media = df_merged['variacao'].mean()
            status_emoji = "🟢" if var_media < 0 else "🔴"
            st.metric(
                "Variação Média",
                f"{var_media:+.1f}%",
                delta=None,
                help="Média das variações individuais"
            )
        
        with col2:
            melhor_var = df_merged.loc[df_merged['variacao'].idxmin()]
            st.metric(
                "Maior Redução",
                f"{melhor_var['variacao']:.1f}%",
                f"{melhor_var['usuário']}",
                delta_color="inverse"
            )
        
        with col3:
            pior_var = df_merged.loc[df_merged['variacao'].idxmax()]
            st.metric(
                "Maior Aumento",
                f"{pior_var['variacao']:.1f}%",
                f"{pior_var['usuário']}"
            )
        
        # Tabela detalhada
        with st.expander("Ver dados detalhados", expanded=False):
            st.dataframe(
                df_merged.style.format({
                    'tpatend_p1': '{:.1f}',
                    'tpatend_p2': '{:.1f}',
                    'variacao': '{:+.1f}%'
                }),
                use_container_width=True
            )
    
    except Exception as e:
        st.error("Erro ao gerar análise de tempo de atendimento")
        st.exception(e)
