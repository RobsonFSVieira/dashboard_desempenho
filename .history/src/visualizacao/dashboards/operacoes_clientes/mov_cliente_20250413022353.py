import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

def formatar_data(data):
    """Formata a data para o padrão dd/mm/aaaa"""
    if isinstance(data, datetime):
        return data.strftime('%d/%m/%Y')
    return data

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

def criar_grafico_comparativo(dados_p1, dados_p2, filtros):
    """Cria gráfico comparativo entre os dois períodos"""
    # Merge dos dados dos dois períodos
    df_comp = pd.merge(
        dados_p1, 
        dados_p2, 
        on='cliente', 
        suffixes=('_p1', '_p2')
    )
    
    # Calcula variação percentual
    df_comp['variacao'] = ((df_comp['quantidade_p2'] - df_comp['quantidade_p1']) 
                          / df_comp['quantidade_p1'] * 100)
    
    # Ordena por quantidade do período 2
    df_comp = df_comp.sort_values('quantidade_p2', ascending=True)
    
    # Prepara legendas formatadas com datas
    legenda_p1 = f"Período 1 ({formatar_data(filtros['periodo1']['inicio'])} a {formatar_data(filtros['periodo1']['fim'])})"
    legenda_p2 = f"Período 2 ({formatar_data(filtros['periodo2']['inicio'])} a {formatar_data(filtros['periodo2']['fim'])})"
    
    # Cria o gráfico
    fig = go.Figure()
    
    # Adiciona barras horizontais empilhadas
    fig.add_trace(
        go.Bar(
            name=legenda_p1,
            y=df_comp['cliente'],
            x=df_comp['quantidade_p1'],
            orientation='h',
            marker_color='rgba(75, 192, 192, 0.8)',
        )
    )
    
    fig.add_trace(
        go.Bar(
            name=legenda_p2,
            y=df_comp['cliente'],
            x=df_comp['quantidade_p2'],
            orientation='h',
            marker_color='rgba(153, 102, 255, 0.8)',
        )
    )
    
    # Adiciona anotações com a variação percentual
    for i, row in df_comp.iterrows():
        fig.add_annotation(
            x=max(row['quantidade_p1'], row['quantidade_p2']) + 1,
            y=row['cliente'],
            text=f"{row['variacao']:+.1f}%",
            showarrow=False,
            font=dict(
                color='green' if row['variacao'] >= 0 else 'red'
            )
        )
    
    # Configura o layout para barras empilhadas horizontais
    fig.update_layout(
        title='Comparativo de Movimentação por Cliente',
        barmode='stack',  # Empilha as barras
        height=400 + (len(df_comp) * 20),
        showlegend=True,
        xaxis_title="Quantidade de Atendimentos",
        yaxis_title="Cliente",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def mostrar_aba(dados, filtros):
    """Mostra a aba de Movimentação por Cliente"""
    st.header("Movimentação por Cliente")
    
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