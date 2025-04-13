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
    try:
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
        
        # Obtém cores do tema atual
        tema_atual = Tema.detectar_tema_atual()
        cores = Tema.PALETAS[tema_atual]['categorica'][:2]
        
        # Cria o gráfico
        fig = go.Figure()
        
        # Adiciona barras horizontais
        fig.add_trace(
            go.Bar(
                name=legenda_p1,
                y=df_comp['cliente'],
                x=df_comp['quantidade_p1'],
                orientation='h',
                marker_color=cores[0]
            )
        )
        
        fig.add_trace(
            go.Bar(
                name=legenda_p2,
                y=df_comp['cliente'],
                x=df_comp['quantidade_p2'],
                orientation='h',
                marker_color=cores[1]
            )
        )
        
        # Atualiza o layout usando cores do tema
        fig.update_layout(
            title={
                'text': 'Comparativo de Movimentação por Cliente',
                'font': {'size': 18}
            },
            barmode='group',
            height=400 + (len(df_comp) * 30),
            font={'size': 12},
            plot_bgcolor=Tema.CORES[tema_atual]['fundo'],
            paper_bgcolor=Tema.CORES[tema_atual]['fundo'],
            font_color=Tema.CORES[tema_atual]['texto'],
            showlegend=True,
            legend={
                'orientation': 'h',
                'yanchor': 'bottom',
                'y': 1.02,
                'xanchor': 'right',
                'x': 1
            }
        )
        
        # Atualiza os eixos
        fig.update_xaxes(
            title="Quantidade de Atendimentos",
            gridcolor=Tema.CORES[tema_atual]['borda'],
            title_font={'size': 14}
        )
        
        fig.update_yaxes(
            title="Cliente",
            gridcolor=Tema.CORES[tema_atual]['borda'],
            title_font={'size': 14}
        )
        
        return fig
    
    except Exception as e:
        st.error(f"Erro ao criar gráfico: {str(e)}")
        return None

def mostrar_aba(dados, filtros):
    """Mostra a aba de Movimentação por Cliente"""
    st.header("Movimentação por Cliente")
    
    try:
        # Calcula movimentação para os dois períodos
        mov_p1 = calcular_movimentacao_por_periodo(dados, filtros, 'periodo1')
        mov_p2 = calcular_movimentacao_por_periodo(dados, filtros, 'periodo2')
        
        if mov_p1.empty or mov_p2.empty:
            st.warning("Não há dados para exibir no período selecionado.")
            return
        
        # Cria e exibe o gráfico comparativo
        fig = criar_grafico_comparativo(mov_p1, mov_p2, filtros)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"Erro ao mostrar aba: {str(e)}")
        st.exception(e)