import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import timedelta

def analisar_colaborador(dados, filtros, colaborador, adicional_filters=None):adicional_filters=None):
    """Analisa dados de um colaborador específico"""
    df = dados['base']
    
    # Aplicar filtros de data
    mask = (
        (df['retirada'].dt.date >= filtros['periodo2']['inicio']) &
        (df['retirada'].dt.date <= filtros['periodo2']['fim']) &
        (df['usuário'] == colaborador)
    )
    
    # Aplicar filtros adicionaisonais
    if adicional_filters:
        if adicional_filters['turno'] != "Todos":ilters['turno'] != "Todos":
            # Mapear hora para turnodf_filtrado[df_filtrado['TURNO'] == adicional_filters['turno']]
            df['turno'] = df['inicio'].dt.hour.map(ers['cliente'] != "Todos":
                lambda x: 'TURNO A' if 6 <= x < 14 ado = df_filtrado[df_filtrado['CLIENTE'] == adicional_filters['cliente']]
                else ('TURNO B' if 14 <= x < 22 else 'TURNO C')
            )
            mask &= (df['turno'] == adicional_filters['turno'])
        
        if adicional_filters['cliente'] != "Todos":    'tpatend': 'mean',
            mask &= (df['CLIENTE'] == adicional_filters['cliente'])
    
    df_filtrado = df[mask]
    
    # Métricas por operação
    metricas_op = df_filtrado.groupby('OPERAÇÃO').agg({er'] / 60
        'id': 'count',
        'tpatend': 'mean',
        'tpesper': 'mean'in dados:
    }).reset_index()
    
    # Converter tempos para minutoss necessárias existem
    metricas_op['tpatend'] = metricas_op['tpatend'] / 60
    metricas_op['tpesper'] = metricas_op['tpesper'] / 60 de médias (pode ser 'Total Geral' ou outra)
    col for col in df_medias.columns if 'Total' in col or 'Média' in col), None)
    # Adicionar coluna de meta (tempo médio geral por operação)
    if 'medias' in dados:
        try:
            df_medias = dados['medias']   metricas_op,
            # Verificar se as colunas necessárias existem,
            if 'OPERAÇÃO' in df_medias.columns:
                # Identificar a coluna de médias (pode ser 'Total Geral' ou outra)       how='left'
                media_col = next((col for col in df_medias.columns if 'Total' in col or 'Média' in col), None)
                
                if media_col:p = metricas_op.rename(columns={media_col: 'meta_tempo'})
                    metricas_op = pd.merge(
                        metricas_op,
                        df_medias[['OPERAÇÃO', media_col]],           metricas_op['meta_tempo'] = df_filtrado['tpatend'].mean() / 60
                        on='OPERAÇÃO',
                        how='left'
                    )            metricas_op['meta_tempo'] = df_filtrado['tpatend'].mean() / 60
                    # Renomear coluna de média para um nome padrãon as e:
                    metricas_op = metricas_op.rename(columns={media_col: 'meta_tempo'})
                else:.mean() / 60
                    # Usar média geral dos dados como metaelse:
                    metricas_op['meta_tempo'] = df_filtrado['tpatend'].mean() / 60eral dos dados como meta
            else:        metricas_op['meta_tempo'] = df_filtrado['tpatend'].mean() / 60
                # Usar média geral dos dados como meta
                metricas_op['meta_tempo'] = df_filtrado['tpatend'].mean() / 60
        except Exception as e:icas_op['tpatend'] - metricas_op['meta_tempo']) / 
            st.warning("Não foi possível carregar as metas. Usando médias gerais.")
            metricas_op['meta_tempo'] = df_filtrado['tpatend'].mean() / 60
    else:    return metricas_op
        # Usar média geral dos dados como meta
        metricas_op['meta_tempo'] = df_filtrado['tpatend'].mean() / 60coes(metricas_op):
    
    # Calcular variação
    metricas_op['variacao'] = ((metricas_op['tpatend'] - metricas_op['meta_tempo']) / ados_qtd = metricas_op.sort_values('id', ascending=True)  # Para o gráfico de barras ficar de baixo para cima
                              metricas_op['meta_tempo'] * 100)dados_tempo = metricas_op.sort_values('tpatend', ascending=False)  # Tempos maiores em baixo
    
    return metricas_opplots(
 cols=2,
def criar_grafico_operacoes(metricas_op):de Atendimentos", "Tempo Médio vs Meta"),
    """Cria gráfico comparativo por operação"""}, {"type": "bar"}]]
    # Ordenar dados para os gráficos
    dados_qtd = metricas_op.sort_values('id', ascending=True)  # Para o gráfico de barras ficar de baixo para cima
    dados_tempo = metricas_op.sort_values('tpatend', ascending=False)  # Tempos maiores em baixorra horizontal (maiores quantidades no topo)

    fig = make_subplots(
        rows=1, cols=2,  y=dados_qtd['OPERAÇÃO'],
        subplot_titles=("Quantidade de Atendimentos", "Tempo Médio vs Meta"),qtd['id'],
        specs=[[{"type": "bar"}, {"type": "bar"}]]       name="Atendimentos",
    )        text=dados_qtd['id'],
    
    # Gráfico de quantidade - barra horizontal (maiores quantidades no topo)_color='royalblue',
    fig.add_trace(entation='h'
        go.Bar(
            y=dados_qtd['OPERAÇÃO'],
            x=dados_qtd['id'],
            name="Atendimentos",
            text=dados_qtd['id'],meta - barra horizontal (menores tempos no topo)
            textposition='auto',
            marker_color='royalblue',
            orientation='h'  y=dados_tempo['OPERAÇÃO'],
        ),tempo['tpatend'],
        row=1, col=1       name="Tempo Médio",
    )        text=dados_tempo['tpatend'].round(1),
    
    # Gráfico de tempo médio vs meta - barra horizontal (menores tempos no topo)_color='lightblue',
    fig.add_trace(tion='h'
        go.Bar(
            y=dados_tempo['OPERAÇÃO'],
            x=dados_tempo['tpatend'],
            name="Tempo Médio",
            text=dados_tempo['tpatend'].round(1),e ordenada igual ao tempo
            textposition='auto',d_trace(
            marker_color='lightblue',
            orientation='h'       y=dados_tempo['OPERAÇÃO'],
        ),        x=dados_tempo['meta_tempo'],
        row=1, col=2",
    )s+markers',
    
    # Linha de meta - adaptada para horizontal e ordenada igual ao tempo
    fig.add_trace(
        go.Scatter(
            y=dados_tempo['OPERAÇÃO'],
            x=dados_tempo['meta_tempo'],t
            name="Meta",
            mode='lines+markers',a dinâmica baseada no número de operações
            line=dict(color='red', dash='dash')
        ),
        row=1, col=2)
    )
        # Atualizar eixos
    # Atualizar layout
    fig.update_layout(, row=1, col=2)
        height=max(400, len(metricas_op) * 40),  # Altura dinâmica baseada no número de operaçõesitle_text="", row=1, col=1)
        showlegend=True,fig.update_yaxes(title_text="", row=1, col=2)
        title_text="Análise por Operação"
    )ig
    
    # Atualizar eixos:
    fig.update_xaxes(title_text="Quantidade", row=1, col=1)""Cria gráfico de evolução diária"""
    fig.update_xaxes(title_text="Minutos", row=1, col=2)
    fig.update_yaxes(title_text="", row=1, col=1)
    fig.update_yaxes(title_text="", row=1, col=2) de data
    
    return fig].dt.date >= filtros['periodo2']['inicio']) &
t.date <= filtros['periodo2']['fim'])
def criar_grafico_evolucao_diaria(dados, filtros, colaborador):
    """Cria gráfico de evolução diária"""df_filtrado = df[mask & (df['usuário'] == colaborador)]
    df = dados['base']
    # Agrupar por dia
    # Aplicar filtros de datado.groupby(df_filtrado['retirada'].dt.date).agg({
    mask = (
        (df['retirada'].dt.date >= filtros['periodo2']['inicio']) &
        (df['retirada'].dt.date <= filtros['periodo2']['fim'])
    )
    df_filtrado = df[mask & (df['usuário'] == colaborador)]evolucao['tpatend'] = evolucao['tpatend'] / 60
    
    # Agrupar por dialots(
    evolucao = df_filtrado.groupby(df_filtrado['retirada'].dt.date).agg({
        'id': 'count',dimentos por Dia", "Tempo Médio por Dia"),
        'tpatend': 'mean'"}, {"type": "scatter"}]]
    }).reset_index()
    
    evolucao['tpatend'] = evolucao['tpatend'] / 60d_trace(
    
    fig = make_subplots(       x=evolucao['retirada'],
        rows=1, cols=2,        y=evolucao['id'],
        subplot_titles=("Atendimentos por Dia", "Tempo Médio por Dia"),lines+markers',
        specs=[[{"type": "scatter"}, {"type": "scatter"}]]tendimentos",
    )lue')
    
    fig.add_trace(
        go.Scatter(
            x=evolucao['retirada'],
            y=evolucao['id'],d_trace(
            mode='lines+markers',
            name="Atendimentos",       x=evolucao['retirada'],
            line=dict(color='royalblue')        y=evolucao['tpatend'],
        ),s+markers',
        row=1, col=1empo Médio",
    )lor='lightblue')
    
    fig.add_trace(   row=1, col=2
        go.Scatter()
            x=evolucao['retirada'],
            y=evolucao['tpatend'],    fig.update_layout(
            mode='lines+markers',
            name="Tempo Médio",
            line=dict(color='lightblue')
        ),)
        row=1, col=2
    )
    
    fig.update_layout(
        height=400,ual do colaborador"""
        showlegend=True,do Colaborador")
        title_text="Evolução Diária"
    )
    # Linha de seletores
    return fig3 = st.columns(3)

def mostrar_aba(dados, filtros):
    """Mostra a aba de análise individual do colaborador"""colaboradores = sorted(dados['base']['usuário'].unique())
    st.header("Análise Individual do Colaborador")ctbox(
    
    try:    options=colaboradores,
        # Seletor de colaboradorEscolha um colaborador para análise detalhada"
        colaboradores = sorted(dados['base']['usuário'].unique())
        colaborador = st.selectbox(
            "Selecione o Colaborador",
            options=colaboradores,s = ["Todos", "TURNO A", "TURNO B", "TURNO C"]
            help="Escolha um colaborador para análise detalhada"turno = st.selectbox(
        )ione o Turno",
        
        if colaborador:re por turno específico"
            # Análise do colaborador
            metricas_op = analisar_colaborador(dados, filtros, colaborador)
            :
            # Métricas principaisclientes = ["Todos"] + sorted(dados['base']['CLIENTE'].unique().tolist())
            col1, col2, col3, col4 = st.columns(4)st.selectbox(
            
            with col1:
                st.metric(re por cliente específico"
                    "Total de Atendimentos",
                    metricas_op['id'].sum()
                )
            alizar a máscara de filtro na função analisar_colaborador
            with col2:adicional_filters = {
                tempo_medio = metricas_op['tpatend'].mean()': turno,
                st.metric(
                    "Tempo Médio",
                    f"{tempo_medio:.1f} min"
                )ros adicionais
            cas_op = analisar_colaborador(dados, filtros, colaborador, adicional_filters)
            with col3:
                meta_media = metricas_op['meta_tempo'].mean() principais
                variacao = ((tempo_medio - meta_media) / meta_media * 100)
                st.metric(
                    "Variação da Meta",with col1:
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
            st.plotly_chart(criar_grafico_evolucao_diaria(dados, filtros, colaborador), use_container_width=True)media = metricas_op['meta_tempo'].mean()
            variacao = ((tempo_medio - meta_media) / meta_media * 100)
            # Análise Detalhada
            st.subheader("📊 Análise Detalhada")
            with st.expander("Ver análise", expanded=True):    f"{variacao:+.1f}%",
                # Performance por operação
                st.write("#### Performance por Operação")
                for _, row in metricas_op.iterrows():
                    status = "✅" if abs(row['variacao']) <= 10 else "⚠️"
                    st.write(
                        f"**{row['OPERAÇÃO']}** {status}\n\n"t.metric(
                        f"- Atendimentos: {row['id']}\n"    "Tempo Médio de Espera",
                        f"- Tempo Médio: {row['tpatend']:.1f} min\n"
                        f"- Meta: {row['meta_tempo']:.1f} min\n"
                        f"- Variação: {row['variacao']:+.1f}%"
                    )
                th=True)
                # Insights geraistros, colaborador), use_container_width=True)
                st.write("#### 📈 Insights")
                álise Detalhada
                # Identificar pontos fortes📊 Análise Detalhada")
                melhor_op = metricas_op.loc[metricas_op['variacao'].abs().idxmin()]):
                st.write(rmance por operação
                    f"- Melhor performance em **{melhor_op['OPERAÇÃO']}** "                st.write("#### Performance por Operação")















        st.exception(e)        st.error("Erro ao analisar dados do colaborador")    except Exception as e:                                    )                        f"(variação de {pior_op['variacao']:+.1f}%)"                        f"- Oportunidade de melhoria em **{pior_op['OPERAÇÃO']}** "                    st.write(                if abs(pior_op['variacao']) > 10:                pior_op = metricas_op.loc[metricas_op['variacao'].abs().idxmax()]                # Identificar pontos de melhoria                                )                    f"(variação de {melhor_op['variacao']:+.1f}%)"                for _, row in metricas_op.iterrows():
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
