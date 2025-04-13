import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from visualizacao.tema import Tema

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
    
    # Obtém cores do tema
    cores = Tema.obter_cores_grafico(num_cores=2, modo='categorico')
    
    # Cria o gráfico
    fig = go.Figure()
    
    # Adiciona barras horizontais empilhadas
    fig.add_trace(
        go.Bar(
            name=legenda_p1,
            y=df_comp['cliente'],
            x=df_comp['quantidade_p1'],
            orientation='h',
            marker_color=cores[0],
            text=df_comp['quantidade_p1'],
            textposition='auto'
        )
    )
    
    fig.add_trace(
        go.Bar(
            name=legenda_p2,
            y=df_comp['cliente'],
            x=df_comp['quantidade_p2'],
            orientation='h',
            marker_color=cores[1],
            text=df_comp['quantidade_p2'],
            textposition='auto'
        )
    )
    
    # Adiciona anotações com a variação percentual
    for i, row in df_comp.iterrows():
        cor_positiva = Tema.CORES[Tema.detectar_tema_atual()]['sucesso']
        cor_negativa = Tema.CORES[Tema.detectar_tema_atual()]['destaque']
        
        fig.add_annotation(
            x=max(row['quantidade_p1'], row['quantidade_p2']) + 1,
            y=row['cliente'],
            text=f"{row['variacao']:+.1f}%",
            showarrow=False,
            font=dict(
                color=cor_positiva if row['variacao'] >= 0 else cor_negativa,
                size=12
            )
        )
    
    # Configura o layout para barras empilhadas horizontais
    fig.update_layout(
        title=dict(
            text='Comparativo de Movimentação por Cliente',
            font=dict(size=18)  # Tamanho da fonte do título
        ),
        barmode='stack',  # Empilha as barras
        height=400 + (len(df_comp) * 20),
        showlegend=True,
        xaxis=dict(
            title="Quantidade de Atendimentos",
            title_font=dict(size=14),
            tickfont=dict(size=12),
            gridcolor=Tema.CORES[Tema.detectar_tema_atual()]['borda']
        ),
        yaxis=dict(
            title="Cliente",
            title_font=dict(size=14),
            tickfont=dict(size=12),
            gridcolor=Tema.CORES[Tema.detectar_tema_atual()]['borda']
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=12)
        ),
        plot_bgcolor=Tema.CORES[Tema.detectar_tema_atual()]['fundo'],
        paper_bgcolor=Tema.CORES[Tema.detectar_tema_atual()]['fundo']
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
        
    except Exception as e:
        st.error("Erro ao gerar a aba de Movimentação por Cliente")
        st.exception(e)