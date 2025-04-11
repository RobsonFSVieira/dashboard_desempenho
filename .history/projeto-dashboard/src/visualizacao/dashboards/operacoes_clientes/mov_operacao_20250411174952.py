import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.tema import TemaDashboard  # Adicionada importação do TemaDashboard

def calcular_movimentacao_por_periodo(dados, filtros, periodo):
    """Calcula a movimentação de cada operação no período especificado"""
    df = dados['base']
    
    # Aplicar filtros de data
    mask = (
        (df['retirada'].dt.date >= filtros[periodo]['inicio']) &
        (df['retirada'].dt.date <= filtros[periodo]['fim'])
    )
    df_filtrado = df[mask]
    
    # Aplicar filtros adicionais se especificados
    if filtros['cliente'] != ['Todos']:
        df_filtrado = df_filtrado[df_filtrado['CLIENTE'].isin(filtros['cliente'])]
    
    # Agrupar por operação
    movimentacao = df_filtrado.groupby('OPERAÇÃO')['id'].count().reset_index()
    movimentacao.columns = ['operacao', 'quantidade']
    
    return movimentacao

def criar_grafico_comparativo(dados_p1, dados_p2, filtros):
    """Cria gráfico comparativo entre os dois períodos"""
    fig = go.Figure()
    cores = TemaDashboard.get_cores_tema()
    
    # Formata as datas para exibição
    periodo1 = f"Período 1 ({filtros['periodo1']['inicio'].strftime('%d/%m/%Y')} - {filtros['periodo1']['fim'].strftime('%d/%m/%Y')})"
    periodo2 = f"Período 2 ({filtros['periodo2']['inicio'].strftime('%d/%m/%Y')} - {filtros['periodo2']['fim'].strftime('%d/%m/%Y')})"
    
    # Merge dos dados dos dois períodos
    df_comp = pd.merge(
        dados_p1, 
        dados_p2, 
        on='operacao', 
        suffixes=('_p1', '_p2')
    )
    
    # Calcula variação percentual e total
    df_comp['variacao'] = ((df_comp['quantidade_p2'] - df_comp['quantidade_p1']) 
                          / df_comp['quantidade_p1'] * 100)
    df_comp['total'] = df_comp['quantidade_p1'] + df_comp['quantidade_p2']
    
    # Ordenar pelo total (maiores no topo)
    df_comp = df_comp.sort_values('total', ascending=True)
    
    # Adiciona primeiro as barras do período 1
    fig.add_trace(
        go.Bar(
            name=periodo1,
            x=df_comp['quantidade_p1'],
            y=df_comp['operacao'],
            orientation='h',
            marker_color=cores['secundaria'],
            text=df_comp['quantidade_p1'],
            textposition='inside',
            textfont=dict(size=16, color='white')
        )
    )
    
    # Adiciona depois as barras do período 2
    fig.add_trace(
        go.Bar(
            name=periodo2,
            x=df_comp['quantidade_p2'],
            y=df_comp['operacao'],
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
    
    # Layout específico
    fig.update_layout(
        title=dict(text=''),
        barmode='stack',
        plot_bgcolor='#262730',
        paper_bgcolor='#262730',
        height=max(450, len(df_comp) * 35),
        margin=dict(
            l=180,   # Margem esquerda para nomes das operações
            r=150,   # Margem direita para valores e porcentagens
            t=50,    # Margem superior
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
            automargin=True
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
            font=dict(size=14, color='white'),
            traceorder='normal'
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
    
    return fig

def mostrar_aba(dados, filtros):
    """Mostra a aba de Movimentação por Operação"""
    st.header("Movimentação por Operação")
    
    try:
        # Calcula movimentação para os dois períodos
        mov_p1 = calcular_movimentacao_por_periodo(dados, filtros, 'periodo1')
        mov_p2 = calcular_movimentacao_por_periodo(dados, filtros, 'periodo2')
        
        # Cria e exibe o gráfico comparativo
        fig = criar_grafico_comparativo(mov_p1, mov_p2, filtros)
        st.plotly_chart(fig, use_container_width=True)
        
        # Insights
        st.subheader("📊 Insights")
        with st.expander("Ver insights"):
            # Calcula variações significativas
            df_comp = pd.merge(
                mov_p1, 
                mov_p2, 
                on='operacao', 
                suffixes=('_p1', '_p2')
            )
            df_comp['variacao'] = ((df_comp['quantidade_p2'] - df_comp['quantidade_p1']) 
                                 / df_comp['quantidade_p1'] * 100)
            
            # Maiores aumentos e reduções
            aumentos = df_comp[df_comp['variacao'] > 0].sort_values('variacao', ascending=False)
            reducoes = df_comp[df_comp['variacao'] < 0].sort_values('variacao')
            
            # Total de atendimentos
            total_p1 = mov_p1['quantidade'].sum()
            total_p2 = mov_p2['quantidade'].sum()
            var_total = ((total_p2 - total_p1) / total_p1 * 100)
            
            st.write("#### Principais Observações:")
            st.write(f"**Variação Total**: {var_total:+.1f}%")
            
            if not aumentos.empty:
                st.write("**Operações com Maior Crescimento:**")
                for _, row in aumentos.head(3).iterrows():
                    st.write(f"- {row['operacao']}: +{row['variacao']:.1f}%")
            
            if not reducoes.empty:
                st.write("**Operações com Maior Redução:**")
                for _, row in reducoes.head(3).iterrows():
                    st.write(f"- {row['operacao']}: {row['variacao']:.1f}%")
    
    except Exception as e:
        st.error("Erro ao gerar a aba de Movimentação por Operação")
        st.exception(e)