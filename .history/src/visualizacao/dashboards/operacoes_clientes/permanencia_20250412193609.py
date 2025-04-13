import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def calcular_permanencia(dados, filtros, grupo='CLIENTE'):
    """Calcula tempo de permanência por cliente/operação"""
    df = dados['base']
    
    # Aplicar filtros de data para período 2 (mais recente)
    mask = (
        (df['retirada'].dt.date >= filtros['periodo2']['inicio']) &
        (df['retirada'].dt.date <= filtros['periodo2']['fim'])
    )
    df_filtrado = df[mask]
    
    # Aplicar filtros adicionais
    if filtros['cliente'] != ['Todos'] and grupo == 'OPERAÇÃO':
        df_filtrado = df_filtrado[df_filtrado['CLIENTE'].isin(filtros['cliente'])]
    
    # Calcula médias de tempo
    tempos = df_filtrado.groupby(grupo).agg({
        'tpatend': 'mean',
        'tpesper': 'mean',
        'tempo_permanencia': 'mean',
        'id': 'count'
    }).reset_index()
    
    # Converte para minutos
    tempos['tpatend'] = tempos['tpatend'] / 60
    tempos['tpesper'] = tempos['tpesper'] / 60
    tempos['tempo_permanencia'] = tempos['tempo_permanencia'] / 60
    
    return tempos

def criar_grafico_permanencia(dados_tempo, meta, grupo='CLIENTE'):
    """Cria gráfico de barras empilhadas com tempo de espera e atendimento"""
    # Ordena por tempo total de permanência
    df = dados_tempo.sort_values('tempo_permanencia', ascending=True)
    
    # Cria o gráfico
    fig = go.Figure()
    
    # Adiciona barra de tempo de espera
    fig.add_trace(
        go.Bar(
            name='Tempo de Espera',
            y=df[grupo],
            x=df['tpesper'],
            orientation='h',
            marker_color='lightgray'
        )
    )
    
    # Adiciona barra de tempo de atendimento
    fig.add_trace(
        go.Bar(
            name='Tempo de Atendimento',
            y=df[grupo],
            x=df['tpatend'],
            orientation='h',
            marker_color='darkblue'
        )
    )
    
    # Adiciona linha de meta
    fig.add_vline(
        x=meta,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Meta: {meta} min"
    )
    
    # Adiciona anotações com o tempo total
    for i, row in df.iterrows():
        fig.add_annotation(
            x=row['tempo_permanencia'],
            y=row[grupo],
            text=f"{row['tempo_permanencia']:.1f} min",
            showarrow=False,
            xshift=10,
            font=dict(
                color='red' if row['tempo_permanencia'] > meta else 'green'
            )
        )
    
    # Atualiza o layout
    fig.update_layout(
        title=f'Tempo de Permanência por {grupo}',
        barmode='stack',
        height=400 + (len(df) * 20),
        showlegend=True,
        xaxis_title="Tempo (minutos)",
        yaxis_title=grupo
    )
    
    return fig

def mostrar_aba(dados, filtros):
    """Mostra a aba de Permanência"""
    st.header("Análise de Permanência")
    
    try:
        # Seletor de visualização
        tipo_analise = st.radio(
            "Analisar por:",
            ["Cliente", "Operação"],
            horizontal=True
        )
        
        grupo = "CLIENTE" if tipo_analise == "Cliente" else "OPERAÇÃO"
        
        # Calcula tempos de permanência
        tempos = calcular_permanencia(dados, filtros, grupo)
        
        # Meta de permanência
        meta = filtros['meta_permanencia']
        
        # Cria e exibe o gráfico
        fig = criar_grafico_permanencia(tempos, meta, grupo)
        st.plotly_chart(fig, use_container_width=True)
        
        # Insights
        st.subheader("📊 Insights")
        with st.expander("Ver insights"):
            # Análise geral
            media_permanencia = tempos['tempo_permanencia'].mean()
            acima_meta = tempos[tempos['tempo_permanencia'] > meta]
            
            st.write("#### Principais Observações:")
            st.write(f"**Média Geral de Permanência**: {media_permanencia:.1f} minutos")
            
            if len(acima_meta) > 0:
                st.write(f"**{len(acima_meta)} {grupo.lower()}s acima da meta:**")
                for _, row in acima_meta.sort_values('tempo_permanencia', ascending=False).head(3).iterrows():
                    st.write(f"- {row[grupo]}: {row['tempo_permanencia']:.1f} min")
            
            # Composição do tempo
            media_espera = tempos['tpesper'].mean()
            media_atend = tempos['tpatend'].mean()
            
            st.write("\n**Composição do Tempo Médio:**")
            st.write(f"- Espera: {media_espera:.1f} min ({(media_espera/media_permanencia)*100:.1f}%)")
            st.write(f"- Atendimento: {media_atend:.1f} min ({(media_atend/media_permanencia)*100:.1f}%)")
    
    except Exception as e:
        st.error("Erro ao gerar a aba de Permanência")
        st.exception(e)