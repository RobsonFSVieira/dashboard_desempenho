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

def criar_grafico_comparativo(dados_p1, dados_p2, dados_medias, grupo):
    """Cria gráfico comparativo entre períodos"""
    fig = go.Figure()
    cores = TemaDashboard.get_cores_tema()

    # Merge dos dados dos dois períodos
    df_comp = pd.merge(
        dados_p1, 
        dados_p2, 
        on=grupo, 
        suffixes=('_p1', '_p2')
    )

    # Calcula a variação percentual
    df_comp['variacao'] = ((df_comp['tempo_p2'] - df_comp['tempo_p1']) 
                          / df_comp['tempo_p1'] * 100)

    # Ordena pelo tempo do período mais recente
    df_comp = df_comp.sort_values('tempo_p2', ascending=True)

    # Adiciona linha de média geral período 1
    fig.add_hline(
        y=dados_medias['media_p1'],
        line_dash="dash",
        line_color=cores['secundaria'],
        opacity=0.5,
        annotation_text=f"Média P1: {dados_medias['media_p1']:.1f}min",
        annotation_position="top right"
    )

    # Adiciona linha de média geral período 2
    fig.add_hline(
        y=dados_medias['media_p2'],
        line_dash="dash",
        line_color=cores['principal'],
        opacity=0.5,
        annotation_text=f"Média P2: {dados_medias['media_p2']:.1f}min",
        annotation_position="bottom right"
    )

    # ...rest of the code...

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