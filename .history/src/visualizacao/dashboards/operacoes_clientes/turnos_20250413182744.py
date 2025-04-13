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

def calcular_metricas_turno(dados, filtros, periodo='periodo2'):
    """Calcula métricas por turno para um período específico"""
    df = dados['base']
    
    # Aplicar filtros de data para o período especificado
    mask = (
        (df['retirada'].dt.date >= filtros[periodo]['inicio']) &
        (df['retirada'].dt.date <= filtros[periodo]['fim'])
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

def criar_graficos_turno(metricas_p1, metricas_p2, filtros):
    """Cria conjunto de gráficos comparativos por turno"""
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
    
    # Lista de dados para cada gráfico
    graficos_data = [
        ('id', 'Quantidade', ''),
        ('tpatend', 'Tempo Atendimento', 'min'),
        ('tpesper', 'Tempo Espera', 'min'),
        ('tempo_permanencia', 'Tempo Total', 'min')
    ]
    
    # Prepara legendas com data formatada
    legenda_p1 = f"Período 1 ({filtros['periodo1']['inicio'].strftime('%d/%m/%Y')} a {filtros['periodo1']['fim'].strftime('%d/%m/%Y')})"
    legenda_p2 = f"Período 2 ({filtros['periodo2']['inicio'].strftime('%d/%m/%Y')} a {filtros['periodo2']['fim'].strftime('%d/%m/%Y')})"
    
    # Adicionar cada gráfico
    for idx, (coluna, nome, unidade) in enumerate(graficos_data):
        row = (idx // 2) + 1
        col = (idx % 2) + 1
        
        # Criar dicionário para mapear valores do período 1 por turno
        valores_p1 = dict(zip(metricas_p1['turno'], metricas_p1[coluna]))
        
        # Calcular diferenças percentuais com cores
        diferencas = []
        for _, row_p2 in metricas_p2.iterrows():
            turno = row_p2['turno']
            valor_p2 = row_p2[coluna]
            valor_p1 = valores_p1.get(turno, 0)
            
            if valor_p1 != 0:
                diff_percent = ((valor_p2 - valor_p1) / valor_p1) * 100
                # Definir cor baseado no tipo de gráfico e valor da diferença
                if idx == 0:  # Gráfico de quantidade de atendimentos
                    cor = cores_tema['sucesso'] if diff_percent > 0 else cores_tema['erro']
                else:  # Gráficos de tempo
                    cor = cores_tema['erro'] if diff_percent > 0 else cores_tema['sucesso']
                
                diferencas.append({
                    'value': diff_percent,
                    'color': cor,
                    'text': f"{diff_percent:+.1f}%"
                })
            else:
                diferencas.append({'value': 0, 'color': '#808080', 'text': 'N/A'})

        # Adiciona barras do período 1
        fig.add_trace(
            go.Bar(
                name=legenda_p1,
                x=metricas_p1['turno'],
                y=metricas_p1[coluna],
                text=[f"{x:.0f}{unidade}" if coluna == 'id' else f"{x:.1f}{unidade}" for x in metricas_p1[coluna]],
                textposition='auto',
                marker_color=cores_tema['primaria'],
                textfont={'color': '#ffffff', 'size': 14},
                showlegend=idx == 0
            ),
            row=row, col=col
        )
        
        # Adiciona barras do período 2 com valor dentro da barra
        fig.add_trace(
            go.Bar(
                name=legenda_p2,
                x=metricas_p2['turno'],
                y=metricas_p2[coluna],
                text=[f"{val:.0f}{unidade}" if coluna == 'id' else f"{val:.1f}{unidade}" 
                      for val in metricas_p2[coluna]],
                textposition='auto',
                marker_color=cores_tema['secundaria'],
                textfont={'color': '#000000', 'size': 14},
                showlegend=idx == 0
            ),
            row=row, col=col
        )

        # Adiciona as porcentagens acima das barras do período 2
        for i, diff in enumerate(diferencas):
            # Calcula a posição x considerando o agrupamento das barras
            x_pos = metricas_p2['turno'].iloc[i]
            
            fig.add_annotation(
                x=x_pos,
                y=metricas_p2[coluna].iloc[i],
                text=diff['text'],
                showarrow=False,
                yshift=15,  # Espaço vertical acima da barra
                xshift=0,   # Remove o xshift anterior
                font=dict(size=14, color=diff['color']),
                align='center',
                xanchor='center',
                yanchor='bottom',
                row=row,
                col=col,
                xref=f'x{idx+1}',
                yref=f'y{idx+1}'
            )

    # Atualizar layout
    fig.update_layout(
        height=800,
        title={
            'text': "Análise Comparativa por Turno",
            'font': {'size': 16, 'color': cores_tema['texto']}
        },
        barmode='group',
        bargap=0.15,
        bargroupgap=0.1,
        showlegend=True,
        legend={
            'orientation': 'h',
            'yanchor': 'bottom',
            'y': 1.02,
            'xanchor': 'right',
            'x': 1
        },
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor=cores_tema['fundo'],
        font={'color': cores_tema['texto']},
        margin=dict(l=20, r=20, t=80, b=20)
    )
    
    # Atualizar eixos
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
        
        # Calcular métricas para ambos os períodos
        metricas_p1 = calcular_metricas_turno(dados, filtros, 'periodo1')
        metricas_p2 = calcular_metricas_turno(dados, filtros, 'periodo2')
        
        # Mostrar gráficos comparativos
        fig = criar_graficos_turno(metricas_p1, metricas_p2, filtros)
        st.plotly_chart(
            fig, 
            use_container_width=True,
            key=f"grafico_turnos_{st.session_state['tema_atual']}"
        )
        
        # Insights
        st.subheader("📊 Insights")
        with st.expander("Ver insights"):
            # Encontrar turno mais movimentado no período 1
            turno_max_p1 = metricas_p1.loc[metricas_p1['id'].idxmax()]
            
            # Encontrar turno mais movimentado no período 2
            turno_max_p2 = metricas_p2.loc[metricas_p2['id'].idxmax()]
            
            st.write("#### Principais Observações:")
            
            st.write(f"**Período 1 - Turno mais movimentado:** Turno {turno_max_p1['turno']}")
            st.write(f"- {turno_max_p1['id']} atendimentos")
            st.write(f"- {turno_max_p1['tempo_permanencia']:.1f} min de permanência média")
            
            st.write(f"\n**Período 2 - Turno mais movimentado:** Turno {turno_max_p2['turno']}")
            st.write(f"- {turno_max_p2['id']} atendimentos")
            st.write(f"- {turno_max_p2['tempo_permanencia']:.1f} min de permanência média")
            
            # Comparação entre turnos
            st.write("\n**Distribuição dos Atendimentos:**")
            for _, row in metricas_p1.iterrows():
                percentual = (row['id'] / metricas_p1['id'].sum()) * 100
                st.write(f"- Período 1 - Turno {row['turno']}: {percentual:.1f}% dos atendimentos")
            for _, row in metricas_p2.iterrows():
                percentual = (row['id'] / metricas_p2['id'].sum()) * 100
                st.write(f"- Período 2 - Turno {row['turno']}: {percentual:.1f}% dos atendimentos")
    
    except Exception as e:
        st.error("Erro ao gerar a aba de Análise por Turno")
        st.exception(e)