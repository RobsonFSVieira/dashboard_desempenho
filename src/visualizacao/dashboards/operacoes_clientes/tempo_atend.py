import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def calcular_tempos_por_periodo(dados, filtros, periodo, grupo='CLIENTE'):
    """Calcula tempos médios de atendimento por cliente/operação no período"""
    df = dados['base']
    df_medias = dados['medias']
    
    # Aplicar filtros de data
    mask = (
        (df['retirada'].dt.date >= filtros[periodo]['inicio']) &
        (df['retirada'].dt.date <= filtros[periodo]['fim'])
    )
    df_filtrado = df[mask]
    
    # Aplicar filtros adicionais
    if filtros['cliente'] != ['Todos'] and grupo == 'OPERAÇÃO':
        df_filtrado = df_filtrado[df_filtrado['CLIENTE'].isin(filtros['cliente'])]
    
    # Calcula média de atendimento
    tempos = df_filtrado.groupby(grupo)['tpatend'].agg([
        ('media', 'mean'),
        ('contagem', 'count')
    ]).reset_index()
    
    # Converte tempo para minutos
    tempos['media'] = tempos['media'] / 60
    
    return tempos

def criar_grafico_comparativo(dados_p1, dados_p2, dados_medias, grupo='CLIENTE'):
    """Cria gráfico comparativo de tempos médios entre períodos"""
    # Merge dos dados dos dois períodos
    df_comp = pd.merge(
        dados_p1,
        dados_p2,
        on=grupo,
        suffixes=('_p1', '_p2')
    )
    
    # Calcula variação percentual
    df_comp['variacao'] = ((df_comp['media_p2'] - df_comp['media_p1']) 
                          / df_comp['media_p1'] * 100)
    
    # Ordena por média do período 2
    df_comp = df_comp.sort_values('media_p2', ascending=True)
    
    # Cria o gráfico
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Adiciona barras para cada período
    fig.add_trace(
        go.Bar(
            name='Período 1',
            y=df_comp[grupo],
            x=df_comp['media_p1'],
            orientation='h',
            marker_color='lightgray'
        )
    )
    
    fig.add_trace(
        go.Bar(
            name='Período 2',
            y=df_comp[grupo],
            x=df_comp['media_p2'],
            orientation='h',
            marker_color='darkblue'
        )
    )
    
    # Adiciona linha de meta se disponível
    if dados_medias is not None:
        fig.add_trace(
            go.Scatter(
                name='Meta',
                y=df_comp[grupo],
                x=dados_medias['Total Geral'],
                mode='markers+lines',
                line=dict(color='red', dash='dash'),
                marker=dict(symbol='diamond')
            ),
            secondary_y=False
        )
    
    # Adiciona anotações com a variação percentual
    for i, row in df_comp.iterrows():
        fig.add_annotation(
            x=max(row['media_p1'], row['media_p2']),
            y=row[grupo],
            text=f"{row['variacao']:+.1f}%",
            showarrow=False,
            xshift=10,
            font=dict(
                color='green' if row['variacao'] < 0 else 'red'
            )
        )
    
    # Atualiza o layout
    fig.update_layout(
        title=f'Comparativo de Tempo Médio de Atendimento por {grupo}',
        barmode='group',
        height=400 + (len(df_comp) * 20),
        showlegend=True,
        xaxis_title="Tempo Médio (minutos)",
        yaxis_title=grupo
    )
    
    return fig

def mostrar_aba(dados, filtros):
    """Mostra a aba de Tempo de Atendimento"""
    st.header("Tempo de Atendimento")
    
    try:
        # Seletor de visualização
        tipo_analise = st.radio(
            "Analisar por:",
            ["Cliente", "Operação"],
            horizontal=True
        )
        
        grupo = "CLIENTE" if tipo_analise == "Cliente" else "OPERAÇÃO"
        
        # Calcula tempos para os dois períodos
        tempos_p1 = calcular_tempos_por_periodo(dados, filtros, 'periodo1', grupo)
        tempos_p2 = calcular_tempos_por_periodo(dados, filtros, 'periodo2', grupo)
        
        # Cria e exibe o gráfico comparativo
        fig = criar_grafico_comparativo(tempos_p1, tempos_p2, dados['medias'], grupo)
        st.plotly_chart(fig, use_container_width=True)
        
        # Insights
        st.subheader("📊 Insights")
        with st.expander("Ver insights"):
            df_comp = pd.merge(
                tempos_p1,
                tempos_p2,
                on=grupo,
                suffixes=('_p1', '_p2')
            )
            df_comp['variacao'] = ((df_comp['media_p2'] - df_comp['media_p1']) 
                                 / df_comp['media_p1'] * 100)
            
            # Identifica melhorias e pioras
            melhorias = df_comp[df_comp['variacao'] < 0].sort_values('variacao')
            pioras = df_comp[df_comp['variacao'] > 0].sort_values('variacao', ascending=False)
            
            st.write("#### Principais Observações:")
            
            # Média geral
            media_geral_p1 = (df_comp['media_p1'] * df_comp['contagem_p1']).sum() / df_comp['contagem_p1'].sum()
            media_geral_p2 = (df_comp['media_p2'] * df_comp['contagem_p2']).sum() / df_comp['contagem_p2'].sum()
            var_media = ((media_geral_p2 - media_geral_p1) / media_geral_p1 * 100)
            
            st.write(f"**Variação na Média Geral**: {var_media:+.1f}%")
            
            if not melhorias.empty:
                st.write("**Maiores Reduções no Tempo:**")
                for _, row in melhorias.head(3).iterrows():
                    st.write(f"- {row[grupo]}: {row['variacao']:.1f}%")
            
            if not pioras.empty:
                st.write("**Maiores Aumentos no Tempo:**")
                for _, row in pioras.head(3).iterrows():
                    st.write(f"- {row[grupo]}: +{row['variacao']:.1f}%")
    
    except Exception as e:
        st.error("Erro ao gerar a aba de Tempo de Atendimento")
        st.exception(e)