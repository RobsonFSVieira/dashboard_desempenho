import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json

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

def obter_cores_tema():
    """Retorna as cores baseadas no tema atual"""
    is_dark = detectar_tema() == 'dark'
    return {
        'primaria': '#1a5fb4' if is_dark else '#1864ab',
        'secundaria': '#4dabf7' if is_dark else '#83c9ff',
        'texto': '#ffffff' if is_dark else '#2c3e50',
        'fundo': '#0e1117' if is_dark else '#ffffff',
        'grid': '#2c3e50' if is_dark else '#e9ecef',
        'sucesso': '#2dd4bf' if is_dark else '#29b09d',
        'erro': '#ff6b6b' if is_dark else '#ff5757'
    }

def identificar_turno(hora):
    """Identifica o turno com base na hora"""
    if 7 <= hora < 15:
        return 'A'
    elif 15 <= hora < 23:
        return 'B'
    else:
        return 'C'

def calcular_metricas_turno(dados, filtros):
    """Calcula métricas por turno"""
    df = dados['base']
    
    # Aplicar filtros de data
    mask = (
        (df['retirada'].dt.date >= filtros['periodo2']['inicio']) &
        (df['retirada'].dt.date <= filtros['periodo2']['fim'])
    )
    
    # Aplicar filtros adicionais
    if filtros['cliente'] != ['Todos']:
        mask &= df['CLIENTE'].isin(filtros['cliente'])
    if filtros['operacao'] != ['Todas']:
        mask &= df['OPERAÇÃO'].isin(filtros['operacao'])
    
    df_filtrado = df[mask]
    
    # Identificar turno
    df_filtrado['turno'] = df_filtrado['retirada'].dt.hour.apply(identificar_turno)
    
    # Calcular métricas por turno
    metricas = df_filtrado.groupby('turno').agg({
        'id': 'count',
        'tpatend': 'mean',
        'tpesper': 'mean',
        'tempo_permanencia': 'mean'
    }).reset_index()
    
    # Converter tempos para minutos
    for col in ['tpatend', 'tpesper', 'tempo_permanencia']:
        metricas[col] = metricas[col] / 60
    
    return metricas

def criar_graficos_turno(metricas, tipo_grafico='barras'):
    """Cria conjunto de gráficos para análise por turno"""
    cores_tema = obter_cores_tema()
    
    # Criar subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Quantidade de Atendimentos por Turno',
            'Tempo Médio de Atendimento por Turno',
            'Tempo Médio de Espera por Turno',
            'Tempo Médio de Permanência por Turno'
        ),
        vertical_spacing=0.16,
        horizontal_spacing=0.1
    )
    
    # Função para criar traço baseado no tipo de gráfico
    def criar_trace(x, y, nome, cor, texto, row, col):
        if tipo_grafico == 'barras':
            return go.Bar(
                x=x, y=y,
                name=nome,
                marker_color=cor,
                text=texto,
                textposition='auto',
                textfont={'color': '#ffffff' if cor == cores_tema['primaria'] else '#000000', 'size': 14}
            )
        elif tipo_grafico == 'linha':
            return go.Scatter(
                x=x, y=y,
                name=nome,
                line=dict(color=cor, width=3),
                mode='lines+markers+text',
                text=texto,
                textposition='top center',
                textfont={'size': 14},
                marker=dict(size=10)
            )
        else:  # pizza
            return go.Pie(
                values=y,
                labels=x,
                name=nome,
                hole=0.3,
                textinfo='label+percent+value',
                marker_colors=[cor, cores_tema['secundaria'], cores_tema['erro']]
            )

    # Lista de dados para cada gráfico
    graficos_data = [
        (metricas['turno'], metricas['id'], 'Quantidade', 'id'),
        (metricas['turno'], metricas['tpatend'], 'Tempo Atendimento', 'tpatend'),
        (metricas['turno'], metricas['tpesper'], 'Tempo Espera', 'tpesper'),
        (metricas['turno'], metricas['tempo_permanencia'], 'Tempo Total', 'tempo_permanencia')
    ]
    
    # Adicionar cada gráfico
    for idx, (x, y, nome, coluna) in enumerate(graficos_data):
        row = (idx // 2) + 1
        col = (idx % 2) + 1
        
        texto = y if coluna == 'id' else [f"{v:.1f} min" for v in y]
        cor = cores_tema['primaria'] if idx % 2 == 0 else cores_tema['secundaria']
        
        trace = criar_trace(x, y, nome, cor, texto, row, col)
        fig.add_trace(trace, row=row, col=col)

    # Atualizar layout
    fig.update_layout(
        height=800,
        title={
            'text': f"Análise por Turno - Visualização em {tipo_grafico.title()}",
            'font': {'size': 16, 'color': cores_tema['texto']}
        },
        showlegend=tipo_grafico == 'pizza',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor=cores_tema['fundo'],
        font={'color': cores_tema['texto']},
        margin=dict(l=20, r=20, t=80, b=20)
    )
    
    if tipo_grafico != 'pizza':
        # Atualizar eixos apenas para gráficos de barra e linha
        for i in range(1, 3):
            for j in range(1, 3):
                fig.update_xaxes(
                    row=i, col=j,
                    showgrid=True,
                    gridcolor=cores_tema['grid'],
                    tickfont={'color': cores_tema['texto']},
                    showline=True,
                    linewidth=1,
                    linecolor=cores_tema['grid']
                )
                fig.update_yaxes(
                    row=i, col=j,
                    showgrid=True,
                    gridcolor=cores_tema['grid'],
                    tickfont={'color': cores_tema['texto']},
                    showline=True,
                    linewidth=1,
                    linecolor=cores_tema['grid'],
                    zeroline=False
                )
    
    return fig

def mostrar_aba(dados, filtros):
    """Mostra a aba de análise por Turno"""
    st.header("Análise por Turno")
    
    try:
        st.session_state['tema_atual'] = detectar_tema()
        
        # Seletor de tipo de gráfico
        tipo_grafico = st.selectbox(
            "Tipo de Visualização",
            options=['barras', 'linha', 'pizza'],
            format_func=lambda x: x.title(),
            key="tipo_grafico_turno"
        )
        
        # Calcular métricas por turno
        metricas = calcular_metricas_turno(dados, filtros)
        
        # Mostrar gráficos
        fig = criar_graficos_turno(metricas, tipo_grafico)
        st.plotly_chart(
            fig, 
            use_container_width=True,
            key=f"grafico_turnos_{tipo_grafico}_{st.session_state['tema_atual']}"
        )
        
        # Insights
        st.subheader("📊 Insights")
        with st.expander("Ver insights"):
            # Encontrar turno mais movimentado
            turno_max = metricas.loc[metricas['id'].idxmax()]
            
            # Encontrar turno com maior tempo de espera
            turno_espera = metricas.loc[metricas['tpesper'].idxmax()]
            
            st.write("#### Principais Observações:")
            
            st.write(f"**Turno mais movimentado:** Turno {turno_max['turno']}")
            st.write(f"- {turno_max['id']} atendimentos")
            st.write(f"- {turno_max['tempo_permanencia']:.1f} min de permanência média")
            
            st.write(f"\n**Turno com maior tempo de espera:** Turno {turno_espera['turno']}")
            st.write(f"- {turno_espera['tpesper']:.1f} min de espera média")
            st.write(f"- {turno_espera['id']} atendimentos")
            
            # Comparação entre turnos
            st.write("\n**Distribuição dos Atendimentos:**")
            for _, row in metricas.iterrows():
                percentual = (row['id'] / metricas['id'].sum()) * 100
                st.write(f"- Turno {row['turno']}: {percentual:.1f}% dos atendimentos")
    
    except Exception as e:
        st.error("Erro ao gerar a aba de Análise por Turno")
        st.exception(e)