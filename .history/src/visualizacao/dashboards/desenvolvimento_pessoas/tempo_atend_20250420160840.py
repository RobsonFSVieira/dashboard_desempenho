import streamlit as st
import plotly.graph_objects as go
import pandas as pd
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

def formatar_tempo(minutos):
    """Formata o tempo em minutos para o formato mm:ss"""
    minutos_int = int(minutos)
    segundos = int((minutos - minutos_int) * 60)
    return f"{minutos_int:02d}:{segundos:02d}"

def calcular_metricas_por_periodo(dados, filtros, periodo_key):
    """Calcula métricas por colaborador para um período específico"""
    df = dados['base']
    
    # Aplicar filtros de data
    mask = (
        (df['retirada'].dt.date >= filtros[periodo_key]['inicio']) &
        (df['retirada'].dt.date <= filtros[periodo_key]['fim'])
    )
    
    # Calcular métricas
    metricas = df[mask].groupby('usuário').agg({
        'id': 'count',
        'tpatend': 'mean'
    }).reset_index()
    
    # Converter tempo para minutos
    metricas['tpatend'] = metricas['tpatend'] / 60
    
    return metricas

def criar_grafico_comparativo(dados_p1, dados_p2, filtros):
    """Cria gráfico comparativo entre períodos"""
    try:
        # Merge e prepara dados
        df_comp = pd.merge(
            dados_p1, 
            dados_p2,
            on='usuário',
            suffixes=('_p1', '_p2')
        )
        
        # Calcula total e variação percentual
        df_comp['total'] = df_comp['tpatend_p1'] + df_comp['tpatend_p2']
        df_comp['variacao'] = ((df_comp['tpatend_p2'] - df_comp['tpatend_p1']) / 
                              df_comp['tpatend_p1'] * 100)
        
        # Ordena por tempo do período 2 decrescente (maiores tempos no topo)
        df_comp = df_comp.sort_values('tpatend_p2', ascending=False)
        
        # Obtém cores do tema atual
        cores_tema = obter_cores_tema()
        
        # Prepara legendas com data formatada
        legenda_p1 = (f"Período 1 ({filtros['periodo1']['inicio'].strftime('%d/%m/%Y')} "
                      f"a {filtros['periodo1']['fim'].strftime('%d/%m/%Y')})")
        legenda_p2 = (f"Período 2 ({filtros['periodo2']['inicio'].strftime('%d/%m/%Y')} "
                      f"a {filtros['periodo2']['fim'].strftime('%d/%m/%Y')})")
        
        # Cria o gráfico
        fig = go.Figure()
        
        # Adiciona barras para período 1
        fig.add_trace(go.Bar(
            name=legenda_p1,
            y=df_comp['usuário'],
            x=df_comp['tpatend_p1'],
            orientation='h',
            text=[f"{formatar_tempo(x)} min" for x in df_comp['tpatend_p1']],
            textposition='inside',
            marker_color=cores_tema['primaria'],
            textfont={
                'size': 16,
                'color': '#ffffff',
                'family': 'Arial Black'
            },
            opacity=0.85
        ))
        
        # Adiciona barras para período 2
        fig.add_trace(go.Bar(
            name=legenda_p2,
            y=df_comp['usuário'],
            x=df_comp['tpatend_p2'],
            orientation='h',
            text=[f"{formatar_tempo(x)} min" for x in df_comp['tpatend_p2']],
            textposition='inside',
            marker_color=cores_tema['secundaria'],
            textfont={
                'size': 16,
                'color': '#000000',
                'family': 'Arial Black'
            },
            opacity=0.85
        ))

        # Adiciona anotações de variação percentual
        df_comp['posicao_total'] = df_comp['tpatend_p1'] + df_comp['tpatend_p2']
        for i, row in df_comp.iterrows():
            cor = cores_tema['sucesso'] if row['variacao'] < 0 else cores_tema['erro']
            
            fig.add_annotation(
                y=row['usuário'],
                x=row['posicao_total'],
                text=f"{row['variacao']:+.1f}%",
                showarrow=False,
                font=dict(color=cor, size=14),
                xanchor='left',
                yanchor='middle',
                xshift=10
            )
        
        # Atualiza layout
        fig.update_layout(
            title={
                'text': 'Comparativo de Tempo Médio de Atendimento por Colaborador',
                'font': {'size': 16, 'color': cores_tema['texto']}
            },
            barmode='stack',
            bargap=0.15,
            bargroupgap=0.1,
            height=max(600, len(df_comp) * 45),
            font={'size': 12, 'color': cores_tema['texto']},
            showlegend=True,
            legend={
                'orientation': 'h',
                'yanchor': 'bottom',
                'y': 1.02,
                'xanchor': 'right',
                'x': 1,
                'font': {'color': cores_tema['texto']},
                'traceorder': 'normal',
                'itemsizing': 'constant'
            },
            margin=dict(l=20, r=160, t=80, b=40),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor=cores_tema['fundo']
        )
        
        # Atualiza eixos
        fig.update_xaxes(
            title='Tempo de Atendimento (minutos)',
            title_font={'color': cores_tema['texto']},
            tickfont={'color': cores_tema['texto']},
            gridcolor=cores_tema['grid'],
            showline=True,
            linewidth=1,
            linecolor=cores_tema['grid'],
            zeroline=False
        )
        
        fig.update_yaxes(
            title='Colaborador',
            title_font={'color': cores_tema['texto']},
            tickfont={'color': cores_tema['texto']},
            gridcolor=cores_tema['grid'],
            showline=True,
            linewidth=1,
            linecolor=cores_tema['grid'],
            zeroline=False
        )
        
        return fig, df_comp
    except Exception as e:
        st.error(f"Erro ao criar gráfico: {str(e)}")
        return None, None

def mostrar_aba(dados, filtros):
    """Mostra a aba de tempo de atendimento"""
    try:
        # Calcular métricas para cada período
        dados_p1 = calcular_metricas_por_periodo(dados, filtros, 'periodo1')
        dados_p2 = calcular_metricas_por_periodo(dados, filtros, 'periodo2')
        
        # Criar gráfico comparativo
        fig, df_merged = criar_grafico_comparativo(dados_p1, dados_p2, filtros)
        
        # Exibir gráfico
        st.plotly_chart(fig, use_container_width=True)
        
        # Métricas gerais de variação
        col1, col2, col3 = st.columns(3)
        
        with col1:
            var_media = df_merged['variacao'].mean()
            status_emoji = "🟢" if var_media < 0 else "🔴"
            st.metric(
                "Variação Média",
                f"{var_media:+.1f}%",
                delta=None,
                help="Média das variações individuais"
            )
        
        with col2:
            melhor_var = df_merged.loc[df_merged['variacao'].idxmin()]
            st.metric(
                "Maior Redução",
                f"{melhor_var['variacao']:.1f}%",
                f"{melhor_var['usuário']}",
                delta_color="inverse"
            )
        
        with col3:
            pior_var = df_merged.loc[df_merged['variacao'].idxmax()]
            st.metric(
                "Maior Aumento",
                f"{pior_var['variacao']:.1f}%",
                f"{pior_var['usuário']}"
            )
        
        # Tabela detalhada
        with st.expander("Ver dados detalhados", expanded=False):
            st.dataframe(
                df_merged.style.format({
                    'tpatend_p1': '{:.1f}',
                    'tpatend_p2': '{:.1f}',
                    'variacao': '{:+.1f}%'
                }),
                use_container_width=True
            )
    
    except Exception as e:
        st.error("Erro ao gerar análise de tempo de atendimento")
        st.exception(e)
