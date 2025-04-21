import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json

def criar_grafico_top_colaboradores(dados, filtros):
    """Cria gráfico dos top 10 colaboradores por quantidade de atendimentos"""
    df = dados['base']
    mask = (df['retirada'].dt.date >= filtros['periodo2']['inicio']) & 
           (df['retirada'].dt.date <= filtros['periodo2']['fim'])
    df = df[mask]

    # Agrupar por colaborador e contar atendimentos
    df_colab = df.groupby('usuário')['id'].count().reset_index()
    df_colab.columns = ['colaborador', 'quantidade']
    df_colab = df_colab.nlargest(10, 'quantidade')

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df_colab['colaborador'],
        x=df_colab['quantidade'],
        orientation='h',
        text=df_colab['quantidade'],
        textposition='inside',
        marker_color='#1a5fb4'
    ))
    
    fig.update_layout(
        title='Top 10 Colaboradores por Volume',
        height=300,
        showlegend=False
    )
    return fig

def criar_grafico_tempo_medio(dados, filtros):
    """Cria gráfico dos 10 melhores tempos médios"""
    df = dados['base']
    mask = (df['retirada'].dt.date >= filtros['periodo2']['inicio']) & 
           (df['retirada'].dt.date <= filtros['periodo2']['fim'])
    df = df[mask]

    # Calcular tempo médio por colaborador
    df_tempo = df.groupby('usuário')['tpatend'].mean().reset_index()
    df_tempo['tpatend'] = df_tempo['tpatend'] / 60  # Converter para minutos
    df_tempo = df_tempo.nsmallest(10, 'tpatend')

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df_tempo['usuário'],
        x=df_tempo['tpatend'],
        orientation='h',
        text=[f"{x:.1f} min" for x in df_tempo['tpatend']],
        textposition='inside',
        marker_color='#4dabf7'
    ))
    
    fig.update_layout(
        title='Top 10 Menores Tempos Médios',
        height=300,
        showlegend=False
    )
    return fig

def criar_grafico_ociosidade(dados, filtros):
    """Cria gráfico dos 10 melhores tempos de ociosidade"""
    df = dados['base']
    mask = (df['retirada'].dt.date >= filtros['periodo2']['inicio']) & 
           (df['retirada'].dt.date <= filtros['periodo2']['fim'])
    df = df[mask]

    ociosidade = []
    for usuario in df['usuário'].unique():
        df_user = df[df['usuário'] == usuario].copy()
        df_user = df_user.sort_values('inicio')
        
        tempo_ocioso = 0
        for i in range(len(df_user)-1):
            intervalo = (df_user.iloc[i+1]['inicio'] - df_user.iloc[i]['fim']).total_seconds()
            if 0 < intervalo <= 7200:  # Entre 0 e 2 horas
                tempo_ocioso += intervalo
                
        if len(df_user) > 0:
            ociosidade.append({
                'colaborador': usuario,
                'tempo_ocioso': tempo_ocioso / (len(df_user) * 60)  # Média em minutos
            })

    df_ocio = pd.DataFrame(ociosidade)
    df_ocio = df_ocio.nsmallest(10, 'tempo_ocioso')

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df_ocio['colaborador'],
        x=df_ocio['tempo_ocioso'],
        orientation='h',
        text=[f"{x:.1f} min" for x in df_ocio['tempo_ocioso']],
        textposition='inside',
        marker_color='#ff6b6b'
    ))
    
    fig.update_layout(
        title='Top 10 Menor Ociosidade',
        height=300,
        showlegend=False
    )
    return fig

def mostrar_aba(dados, filtros):
    """Mostra a aba de visão geral"""
    st.header("Visão Geral dos Colaboradores")

    # Seção dos gráficos
    st.markdown("""
        <style>
            .performance-card {
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 10px;
                padding: 20px;
                margin: 10px 0;
            }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fig_vol = criar_grafico_top_colaboradores(dados, filtros)
        st.plotly_chart(fig_vol, use_container_width=True)
    
    with col2:
        fig_tempo = criar_grafico_tempo_medio(dados, filtros)
        st.plotly_chart(fig_tempo, use_container_width=True)
    
    with col3:
        fig_ocio = criar_grafico_ociosidade(dados, filtros)
        st.plotly_chart(fig_ocio, use_container_width=True)
