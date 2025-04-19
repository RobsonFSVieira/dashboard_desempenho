import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def analisar_tempos_colaborador(dados, filtros):
    """Analisa detalhadamente os tempos de atendimento por colaborador"""
    df = dados['base']
    df_medias = dados['medias']
    
    # Aplicar filtros de data para período 2
    mask = (
        (df['retirada'].dt.date >= filtros['periodo2']['inicio']) &
        (df['retirada'].dt.date <= filtros['periodo2']['fim'])
    )
    df_filtrado = df[mask]
    
    # Calcular métricas por colaborador e operação
    analise = df_filtrado.groupby(['usuário', 'OPERAÇÃO']).agg({
        'id': 'count',
        'tpatend': ['mean', 'std', 'min', 'max']
    }).reset_index()
    
    # Renomear colunas
    analise.columns = ['colaborador', 'operacao', 'atendimentos', 
                      'tempo_medio', 'desvio_padrao', 'tempo_min', 'tempo_max']
    
    # Converter tempos para minutos
    for col in ['tempo_medio', 'desvio_padrao', 'tempo_min', 'tempo_max']:
        analise[col] = analise[col] / 60
    
    return analise

def criar_grafico_boxplot(dados_filtrados):
    """Cria boxplot dos tempos de atendimento por colaborador"""
    fig = go.Figure()
    
    # Adiciona boxplot para cada colaborador
    for colaborador in dados_filtrados['usuário'].unique():
        dados_colab = dados_filtrados[dados_filtrados['usuário'] == colaborador]
        
        fig.add_trace(go.Box(
            y=dados_colab['tpatend'] / 60,  # Converter para minutos
            name=colaborador,
            boxpoints='outliers',
            jitter=0.3,
            pointpos=-1.8
        ))
    
    # Atualiza layout
    fig.update_layout(
        title="Distribuição dos Tempos de Atendimento por Colaborador",
        yaxis_title="Tempo de Atendimento (minutos)",
        showlegend=False,
        height=600
    )
    
    return fig

def mostrar_aba(dados, filtros):
    """Mostra a aba de Tempo de Atendimento"""
    st.header("Análise de Tempo de Atendimento")
    
    try:
        # Análise detalhada dos tempos
        analise = analisar_tempos_colaborador(dados, filtros)
        
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            colaboradores = sorted(analise['colaborador'].unique())
            colab_selecionado = st.selectbox(
                "Selecione o Colaborador:",
                colaboradores
            )
        
        with col2:
            operacoes = sorted(analise['operacao'].unique())
            op_selecionada = st.selectbox(
                "Selecione a Operação:",
                ["Todas"] + list(operacoes)
            )
        
        # Filtrar dados
        dados_viz = analise[analise['colaborador'] == colab_selecionado]
        if op_selecionada != "Todas":
            dados_viz = dados_viz[dados_viz['operacao'] == op_selecionada]
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Tempo Médio",
                f"{dados_viz['tempo_medio'].mean():.1f} min"
            )
        
        with col2:
            st.metric(
                "Desvio Padrão",
                f"{dados_viz['desvio_padrao'].mean():.1f} min"
            )
        
        with col3:
            st.metric(
                "Tempo Mínimo",
                f"{dados_viz['tempo_min'].min():.1f} min"
            )
        
        with col4:
            st.metric(
                "Tempo Máximo",
                f"{dados_viz['tempo_max'].max():.1f} min"
            )
        
        # Gráfico de distribuição
        st.subheader("Distribuição dos Tempos")
        dados_base = dados['base']
        mask = (
            (dados_base['retirada'].dt.date >= filtros['periodo2']['inicio']) &
            (dados_base['retirada'].dt.date <= filtros['periodo2']['fim']) &
            (dados_base['usuário'] == colab_selecionado)
        )
        
        if op_selecionada != "Todas":
            mask &= (dados_base['OPERAÇÃO'] == op_selecionada)
        
        dados_filtrados = dados_base[mask]
        fig = criar_grafico_boxplot(dados_filtrados)
        st.plotly_chart(fig, use_container_width=True)
        
        # Insights
        st.subheader("📊 Insights")
        with st.expander("Ver insights"):
            # Comparação com médias esperadas
            df_medias = dados['medias']
            
            st.write("#### Principais Observações:")
            
            # Análise por operação
            for _, row in dados_viz.iterrows():
                meta = df_medias[df_medias['OPERAÇÃO'] == row['operacao']]['Total Geral'].values[0]
                variacao = ((row['tempo_medio'] - meta) / meta * 100)
                
                st.write(f"**{row['operacao']}:**")
                st.write(f"- Tempo Médio: {row['tempo_medio']:.1f} min")
                st.write(f"- Meta: {meta:.1f} min")
                st.write(f"- Variação: {variacao:+.1f}%")
                
                if abs(variacao) > 20:
                    st.warning("⚠️ Variação significativa detectada")
    
    except Exception as e:
        st.error("Erro ao gerar a aba de Tempo de Atendimento")
        st.exception(e)