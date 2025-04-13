import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def formatar_tempo(minutos):
    """Formata o tempo em minutos para o formato mm:ss"""
    minutos_int = int(minutos)
    segundos = int((minutos - minutos_int) * 60)
    return f"{minutos_int:02d}:{segundos:02d}"

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
            marker_color='lightgray',
            text=[f"{formatar_tempo(x)} min" for x in df['tpesper']],
            textposition='inside',
            textfont={'color': 'black'}
        )
    )
    
    # Adiciona barra de tempo de atendimento
    fig.add_trace(
        go.Bar(
            name='Tempo de Atendimento',
            y=df[grupo],
            x=df['tpatend'],
            orientation='h',
            marker_color='darkblue',
            text=[f"{formatar_tempo(x)} min" for x in df['tpatend']],
            textposition='inside',
            textfont={'color': 'white'}
        )
    )
    
    # Adiciona linha de meta
    fig.add_vline(
        x=meta,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Meta: {formatar_tempo(meta)} min"
    )
    
    # Adiciona anotações com o tempo total
    for i, row in df.iterrows():
        fig.add_annotation(
            x=row['tempo_permanencia'],
            y=row[grupo],
            text=f"{formatar_tempo(row['tempo_permanencia'])} min",
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
        # Seletor de visualização com key única
        tipo_analise = st.radio(
            "Analisar por:",
            ["Cliente", "Operação"],
            horizontal=True,
            key="radio_permanencia"  # Adicionada chave única
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
        with st.expander("Ver insights", expanded=True):
            # Análise geral
            media_permanencia = tempos['tempo_permanencia'].mean()
            acima_meta = tempos[tempos['tempo_permanencia'] > meta]
            
            st.write("#### Principais Observações:")
            st.write(f"**Média Geral de Permanência**: {formatar_tempo(media_permanencia)} minutos")
            
            if len(acima_meta) > 0:
                st.write(f"**{len(acima_meta)} {grupo.lower()}s acima da meta:**")
                for _, row in acima_meta.sort_values('tempo_permanencia', ascending=False).head(3).iterrows():
                    excesso = row['tempo_permanencia'] - meta
                    st.write(f"- {row[grupo]}: {formatar_tempo(row['tempo_permanencia'])} min (:red[+{formatar_tempo(excesso)} min acima da meta])")
            
            # Composição do tempo
            media_espera = tempos['tpesper'].mean()
            media_atend = tempos['tpatend'].mean()
            
            st.write("\n**Composição do Tempo Médio:**")
            st.write(f"- Espera: {formatar_tempo(media_espera)} min ({(media_espera/media_permanencia)*100:.1f}%)")
            st.write(f"- Atendimento: {formatar_tempo(media_atend)} min ({(media_atend/media_permanencia)*100:.1f}%)")
            
            # Adiciona análise de distribuição do tempo
            st.write("\n**Distribuição do Tempo Total:**")
            dentro_meta = tempos[tempos['tempo_permanencia'] <= meta]
            perc_dentro = (len(dentro_meta) / len(tempos) * 100)
            st.write(f"- {len(dentro_meta)} ({perc_dentro:.1f}%) dentro da meta de {formatar_tempo(meta)} min")
            st.write(f"- {len(acima_meta)} ({100-perc_dentro:.1f}%) acima da meta")
    
    except Exception as e:
        st.error("Erro ao gerar a aba de Permanência")
        st.exception(e)