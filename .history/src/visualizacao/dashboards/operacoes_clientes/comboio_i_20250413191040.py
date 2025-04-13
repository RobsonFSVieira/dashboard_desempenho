import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import json

def criar_mapa_calor(dados, filtros, cliente=None):
    """Cria mapa de calor de retirada de senhas"""
    df = dados['base']
    cores_tema = obter_cores_tema()
    
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
        index=df_filtrado['retirada'].dt.strftime('%d/%m/%Y'),
        columns=df_filtrado['retirada'].dt.hour,
        aggfunc='count',
        fill_value=0
    )
    
    # Garantir todas as horas do dia (0-23)
    todas_horas = range(24)
    for hora in todas_horas:
        if hora not in pivot.columns:
            pivot[hora] = 0
    pivot = pivot.reindex(columns=sorted(pivot.columns))
    
    # Criar mapa de calor com configurações atualizadas
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=[f"{h:02d}:00" for h in pivot.columns],
        y=pivot.index,
        text=pivot.values,
        texttemplate="%{text}",
        textfont={"size": 16, "family": "Arial Black", "color": cores_tema['texto']},
        customdata=pivot.values,
        hovertemplate="Data: %{y}<br>Hora: %{x}<br>Quantidade: %{customdata}<extra></extra>",
        colorscale=[
            [0.0, cores_tema['fundo']],
            [0.2, cores_tema['secundaria']],
            [1.0, cores_tema['primaria']]
        ],
        showscale=True,
        colorbar=dict(
            title=dict(
                text="Quantidade",
                font={"size": 14, "color": cores_tema['texto']}
            ),
            tickfont={"size": 12, "color": cores_tema['texto']},
            len=0.9
        )
    ))
    
    # Título do gráfico
    titulo = f"Mapa de Calor - Retirada de Senhas {'- ' + cliente if cliente else ''}"
    
    # Atualizar layout com configurações seguras
    fig.update_layout(
        title_text=titulo,
        title_font_size=16,
        title_font_color=cores_tema['texto'],
        paper_bgcolor=cores_tema['fundo'],
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=cores_tema['texto']),
        xaxis=dict(
            title="Hora do Dia",
            ticktext=[f"{h:02d}:00" for h in range(24)],
            tickvals=list(range(24)),
            tickangle=-45,
            gridcolor=cores_tema['grid'],
            title_font=dict(size=14),
            tickfont=dict(size=12)
        ),
        yaxis=dict(
            title="Data",
            gridcolor=cores_tema['grid'],
            title_font=dict(size=14),
            tickfont=dict(size=12)
        ),
        height=max(400, len(pivot.index) * 25),
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig

def obter_cores_tema():
    """Retorna as cores baseadas no tema atual"""
    is_dark = detectar_tema() == 'dark'
    return {
        'primaria': '#1a5fb4' if is_dark else '#1864ab',
        'secundaria': '#4dabf7' if is_dark else '#83c9ff',
        'texto': '#ffffff' if is_dark else '#2c3e50',
        'fundo': '#0e1117' if is_dark else '#ffffff',
        'grid': '#2c3e50' if is_dark else '#d3d3d3'
    }

def detectar_tema():
    """Detecta se o tema atual é claro ou escuro"""
    try:
        theme_param = st.query_params.get('theme', None)
        if theme_param:
            return json.loads(theme_param)['base']
        else:
            return st.config.get_option('theme.base')
    except:
        return 'light'

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