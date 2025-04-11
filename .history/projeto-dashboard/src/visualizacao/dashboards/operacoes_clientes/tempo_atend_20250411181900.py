import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.tema import TemaDashboard  # Adicionada importação do TemaDashboard

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

def calcular_medias(dados, filtros):
    """Calcula médias gerais dos tempos para os dois períodos"""
    df = dados['base']
    
    # Médias do período 1
    mask_p1 = (
        (df['retirada'].dt.date >= filtros['periodo1']['inicio']) &
        (df['retirada'].dt.date <= filtros['periodo1']['fim'])
    )
    media_p1 = df[mask_p1]['tpatend'].mean() / 60  # Converte para minutos
    
    # Médias do período 2
    mask_p2 = (
        (df['retirada'].dt.date >= filtros['periodo2']['inicio']) &
        (df['retirada'].dt.date <= filtros['periodo2']['fim'])
    )
    media_p2 = df[mask_p2]['tpatend'].mean() / 60  # Converte para minutos
    
    return {
        'media_p1': media_p1,
        'media_p2': media_p2
    }

def criar_grafico_comparativo(dados_p1, dados_p2, dados_medias, grupo, filtros):  # Adicionado parâmetro filtros
    """Cria gráfico comparativo entre períodos"""
    fig = go.Figure()
    cores = TemaDashboard.get_cores_tema()

    # Formata as datas para exibição
    periodo1 = f"Período 1 ({filtros['periodo1']['inicio'].strftime('%d/%m/%Y')} - {filtros['periodo1']['fim'].strftime('%d/%m/%Y')})"
    periodo2 = f"Período 2 ({filtros['periodo2']['inicio'].strftime('%d/%m/%Y')} - {filtros['periodo2']['fim'].strftime('%d/%m/%Y')})"

    # Merge dos dados dos dois períodos
    df_comp = pd.merge(
        dados_p1, 
        dados_p2, 
        on=grupo, 
        suffixes=('_p1', '_p2')
    )

    # Calcula a variação percentual usando a coluna 'media' ao invés de 'tempo'
    df_comp['variacao'] = ((df_comp['media_p2'] - df_comp['media_p1']) 
                          / df_comp['media_p1'] * 100)

    # Ordena pelo tempo do período mais recente (menores tempos no topo)
    df_comp = df_comp.sort_values('media_p2', ascending=False)  # Mudado para False

    # Adiciona barras do período 1
    fig.add_trace(
        go.Bar(
            name=periodo1,  # Usa período com datas
            x=df_comp['media_p1'],
            y=df_comp[grupo],
            orientation='h',
            marker_color=cores['secundaria'],
            text=df_comp['media_p1'].round(1).astype(str) + ' min',
            textposition='inside',
            textfont=dict(size=16, color='white')
        )
    )

    # Adiciona barras do período 2
    fig.add_trace(
        go.Bar(
            name=periodo2,  # Usa período com datas
            x=df_comp['media_p2'],
            y=df_comp[grupo],
            orientation='h',
            marker_color=cores['principal'],
            text=[
                f"{v:.1f} min (<span style='color: {cores['positivo'] if var >= 0 else cores['negativo']}'>{var:+.1f}%</span>)" 
                for v, var in zip(df_comp['media_p2'], df_comp['variacao'])
            ],
            textposition='outside',
            textfont=dict(size=16, color='white')
        )
    )

    # Ajusta altura dinâmica baseada no grupo
    altura_base = 450
    altura_por_item = 35 if grupo == "OPERAÇÃO" else 25  # Menor altura por item para Clientes
    altura_minima = 450 if grupo == "OPERAÇÃO" else 600  # Altura mínima maior para Clientes
    
    altura_final = max(altura_minima, len(df_comp) * altura_por_item)

    # Layout específico ajustado
    fig.update_layout(
        title=dict(text=''),
        barmode='stack',  # Mudado para 'stack' para empilhar as barras
        plot_bgcolor='#262730',
        paper_bgcolor='#262730',
        height=altura_final,  # Usa altura calculada
        margin=dict(
            l=180,   # Margem esquerda para nomes
            r=150,   # Margem direita para valores e porcentagens
            t=50,    # Margem superior reduzida
            b=50,    # Margem inferior
            pad=5    # Padding reduzido
        ),
        xaxis=dict(
            title=dict(
                text='Tempo Médio (minutos)',
                font=dict(size=14, color='white')
            ),
            showgrid=True,
            gridcolor='#404040',
            zeroline=False,
            tickfont=dict(size=12, color='white'),
            range=[0, df_comp['media_p2'].max() * 1.15]  # Range com 15% de margem
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
        fig = criar_grafico_comparativo(tempos_p1, tempos_p2, dados['medias'], grupo, filtros)  # Adicionado filtros como parâmetro
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