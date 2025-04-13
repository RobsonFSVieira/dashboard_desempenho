import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

def criar_mapa_calor(dados, filtros, cliente=None):
    """Cria mapa de calor de retirada de senhas"""
    df = dados['base']
    
    # Aplicar filtros de data para período 2
    mask = (
        (df['retirada'].dt.date >= filtros['periodo2']['inicio']) &
        (df['retirada'].dt.date <= filtros['periodo2']['fim'])
    )
    df_filtrado = df[mask]
    
    # Filtrar por cliente se especificado
    if cliente:
        df_filtrado = df_filtrado[df_filtrado['CLIENTE'] == cliente]
    
    # Criar matriz de dados para o mapa de calor
    pivot = pd.pivot_table(
        df_filtrado,
        values='id',
        index=df_filtrado['retirada'].dt.date,
        columns=df_filtrado['retirada'].dt.hour,
        aggfunc='count',
        fill_value=0
    )
    
    # Criar mapa de calor
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=pivot.index,
        colorscale='YlOrRd',
        hoverongaps=False
    ))
    
    # Atualizar layout
    titulo = f"Mapa de Calor - Retirada de Senhas {'- ' + cliente if cliente else 'Geral'}"
    fig.update_layout(
        title=titulo,
        xaxis_title="Hora do Dia",
        yaxis_title="Data",
        height=600
    )
    
    return fig

def mostrar_aba(dados, filtros):
    """Mostra a aba de análise de chegada em comboio"""
    st.header("Análise de Chegada em Comboio I")
    st.write("Mapa de calor mostrando a concentração de retirada de senhas por hora e dia")
    
    try:
        # Seleção de visualização
        tipo_analise = st.radio(
            "Visualizar:",
            ["Geral", "Por Cliente"],
            horizontal=True
        )
        
        if tipo_analise == "Por Cliente":
            # Lista de clientes disponíveis
            clientes = sorted(dados['base']['CLIENTE'].unique())
            cliente_selecionado = st.selectbox(
                "Selecione o Cliente:",
                clientes
            )
            
            # Criar mapa de calor para o cliente selecionado
            fig = criar_mapa_calor(dados, filtros, cliente_selecionado)
        else:
            # Criar mapa de calor geral
            fig = criar_mapa_calor(dados, filtros)
        
        # Exibir gráfico
        st.plotly_chart(fig, use_container_width=True)
        
        # Insights
        st.subheader("📊 Insights")
        with st.expander("Ver insights"):
            df = dados['base']
            
            # Identificar horários de pico
            df['hora'] = df['retirada'].dt.hour
            picos = df.groupby('hora')['id'].count()
            hora_pico = picos.idxmax()
            
            # Identificar dias mais movimentados
            df['dia_semana'] = df['retirada'].dt.day_name()
            dias_mov = df.groupby('dia_semana')['id'].count()
            dia_mais_mov = dias_mov.idxmax()
            
            st.write("#### Principais Observações:")
            st.write(f"**Horário de Maior Movimento:** {hora_pico}:00h")
            st.write(f"**Dia Mais Movimentado:** {dia_mais_mov}")
            
            # Identificar padrões de comboio
            st.write("\n**Padrões de Chegada em Comboio:**")
            horarios_criticos = picos[picos > picos.mean() + picos.std()].index
            if len(horarios_criticos) > 0:
                st.write("Horários críticos com potencial formação de comboio:")
                for hora in sorted(horarios_criticos):
                    st.write(f"- {hora}:00h")
    
    except Exception as e:
        st.error("Erro ao gerar a aba de Análise de Chegada em Comboio")
        st.exception(e)