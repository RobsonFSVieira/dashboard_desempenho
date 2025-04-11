import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.tema import TemaDashboard

def calcular_movimentacao_por_periodo(dados, filtros, periodo):
    """Calcula a movimentação de cada cliente no período especificado"""
    df = dados['base']
    
    # Aplicar filtros de data
    mask = (
        (df['retirada'].dt.date >= filtros[periodo]['inicio']) &
        (df['retirada'].dt.date <= filtros[periodo]['fim'])
    )
    df_filtrado = df[mask]
    
    # Agrupar por cliente
    movimentacao = df_filtrado.groupby('CLIENTE')['id'].count().reset_index()
    movimentacao.columns = ['cliente', 'quantidade']
    
    return movimentacao

def criar_grafico_movimentacao(dados_cliente, periodo):
    """Cria gráfico de movimentação do cliente"""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Usar CORES diretamente ao invés de get_cores()
    fig.add_trace(
        go.Bar(
            name='Quantidade de Senhas',
            x=dados_cliente.index,
            y=dados_cliente['quantidade'],
            marker_color=TemaDashboard.CORES['principal'],
            marker_line_color=TemaDashboard.CORES['background'],
            marker_line_width=1,
            texttemplate='%{y:.0f}',
            textposition='outside'
        ),
        secondary_y=False
    )
    
    # Adiciona linha de tempo médio
    fig.add_trace(
        go.Scatter(
            name='Tempo Médio (min)',
            x=dados_cliente.index,
            y=dados_cliente['tempo_medio'],
            mode='lines+markers+text',
            line=dict(color=TemaDashboard.CORES['accent'], width=2),
            marker=dict(
                size=8,
                color=TemaDashboard.CORES['accent'],
                line=dict(color=TemaDashboard.CORES['background'], width=1)
            ),
            texttemplate='%{y:.1f}',
            textposition='top center'
        ),
        secondary_y=True
    )
    
    # Aplicar tema padrão
    TemaDashboard.aplicar_tema(fig)
    
    # Ajustes específicos
    fig.update_layout(
        title=f"Movimentação por Cliente - {periodo}",
        barmode='group',
        xaxis_title="Cliente",
        yaxis_title="Quantidade de Senhas",
        yaxis2=dict(
            title="Tempo Médio (min)",
            titlefont=dict(color=TemaDashboard.CORES['accent']),
            tickfont=dict(color=TemaDashboard.CORES['accent'])
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Ajusta rótulos do eixo X para melhor visualização
    fig.update_xaxes(
        tickangle=45,
        tickmode='array',
        ticktext=dados_cliente.index,
        tickvals=list(range(len(dados_cliente.index)))
    )
    
    return fig

def criar_grafico_comparativo(dados_p1, dados_p2, filtros):
    """Cria gráfico comparativo entre períodos"""
    fig = go.Figure()
    cores = TemaDashboard.get_cores_tema()
    
    # Formata as datas para exibição
    periodo1 = f"Período 1 ({filtros['periodo1']['inicio'].strftime('%d/%m/%Y')} - {filtros['periodo1']['fim'].strftime('%d/%m/%Y')})"
    periodo2 = f"Período 2 ({filtros['periodo2']['inicio'].strftime('%d/%m/%Y')} - {filtros['periodo2']['fim'].strftime('%d/%m/%Y')})"
    
    # Preparação dos dados
    df_comp = pd.merge(
        dados_p1, 
        dados_p2, 
        on='cliente', 
        suffixes=('_p1', '_p2')
    )
    
    # Calcula variação percentual e total
    df_comp['variacao'] = ((df_comp['quantidade_p2'] - df_comp['quantidade_p1']) 
                          / df_comp['quantidade_p1'] * 100)
    df_comp['total'] = df_comp['quantidade_p1'] + df_comp['quantidade_p2']
    
    # Ordenar pelo total (maiores no topo)
    df_comp = df_comp.sort_values('total', ascending=True)  # True para maiores no topo em barras horizontais
    
    # Adiciona primeiro as barras do período 2 (fundo)
    fig.add_trace(
        go.Bar(
            name=periodo2,
            x=df_comp['quantidade_p2'],
            y=df_comp['cliente'],
            orientation='h',
            marker_color=cores['principal'],
            text=[
                f"{int(q)} (<span style='color: {cores['positivo'] if v >= 0 else cores['negativo']}'>{v:+.1f}%</span>)" 
                for q, v in zip(df_comp['quantidade_p2'], df_comp['variacao'])
            ],
            textposition='outside',
            textfont=dict(size=16, color='white')
        )
    )
    
    # Adiciona depois as barras do período 1 (frente)
    fig.add_trace(
        go.Bar(
            name=periodo1,
            x=df_comp['quantidade_p1'],
            y=df_comp['cliente'],
            orientation='h',
            marker_color=cores['secundaria'],
            text=df_comp['quantidade_p1'],
            textposition='inside',
            textfont=dict(size=16, color='white')
        )
    )
    
    # Calcula o valor máximo total (soma dos dois períodos) para o range
    max_total = df_comp['total'].max()
    
    # Layout específico
    fig.update_layout(
        title=dict(text=''),
        barmode='stack',
        plot_bgcolor='#262730',
        paper_bgcolor='#262730',
        height=max(450, len(df_comp) * 35),  # Altura base de 450px com ajuste dinâmico
        margin=dict(
            l=180,   # Margem esquerda para nomes dos clientes
            r=150,   # Margem direita para valores e porcentagens
            t=50,    # Margem superior reduzida
            b=50,    # Margem inferior
            pad=5    # Padding reduzido
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor='#404040',
            zeroline=False,
            tickfont=dict(size=12, color='white'),
            range=[0, df_comp['total'].max() * 1.15],  # Range com 15% de margem
            fixedrange=True
        ),
        yaxis=dict(
            showgrid=False,
            tickfont=dict(size=12, color='white'),
            fixedrange=True,
            automargin=True  # Ajusta margem automaticamente para textos longos
        ),
        font=dict(
            family="Helvetica Neue, Arial, sans-serif",
            size=14,
            color='white'
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor='#262730',
            font=dict(size=14, color='white')
        ),
        modebar=dict(
            bgcolor='rgba(0,0,0,0)',
            color='white',
            activecolor='white',
            remove=[
                'zoom', 'pan', 'select', 'lasso2d', 'zoomIn2d', 
                'zoomOut2d', 'autoScale2d', 'resetScale2d',
                'hoverClosestCartesian', 'hoverCompareCartesian',
                'toggleSpikelines'
            ]
        )
    )
    
    # Força o recálculo do layout
    fig.update_layout(autosize=True)
    
    return fig

def mostrar_aba(dados, filtros):
    """Mostra a aba de movimentação por cliente"""
    st.header("Movimentação por Cliente")
    st.write("Análise da movimentação por cliente")
    
    try:
        # Calcula movimentação para os dois períodos
        mov_p1 = calcular_movimentacao_por_periodo(dados, filtros, 'periodo1')
        mov_p2 = calcular_movimentacao_por_periodo(dados, filtros, 'periodo2')
        
        # Cria e exibe o gráfico comparativo
        fig_comp = criar_grafico_comparativo(mov_p1, mov_p2, filtros)
        st.plotly_chart(fig_comp, use_container_width=True)
        
        # Insights
        st.subheader("📊 Insights")
        with st.expander("Ver insights"):
            # Calcula variações significativas
            df_comp = pd.merge(
                mov_p1, 
                mov_p2, 
                on='cliente', 
                suffixes=('_p1', '_p2')
            )
            df_comp['variacao'] = ((df_comp['quantidade_p2'] - df_comp['quantidade_p1']) 
                                 / df_comp['quantidade_p1'] * 100)
            
            # Maiores aumentos e reduções
            aumentos = df_comp[df_comp['variacao'] > 0].sort_values('variacao', ascending=False)
            reducoes = df_comp[df_comp['variacao'] < 0].sort_values('variacao')
            
            st.write("#### Principais Observações:")
            
            if not aumentos.empty:
                st.write("**Maiores Aumentos:**")
                for _, row in aumentos.head(3).iterrows():
                    st.write(f"- {row['cliente']}: +{row['variacao']:.1f}%")
            
            if not reducoes.empty:
                st.write("**Maiores Reduções:**")
                for _, row in reducoes.head(3).iterrows():
                    st.write(f"- {row['cliente']}: {row['variacao']:.1f}%")
    
    except Exception as e:
        st.error("Erro ao gerar a aba de Movimentação por Cliente")
        st.exception(e)