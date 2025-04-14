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

def formatar_tempo(minutos):
    """Formata o tempo em minutos para o formato mm:ss"""
    minutos_int = int(minutos)
    segundos = int((minutos - minutos_int) * 60)
    return f"{minutos_int:02d}:{segundos:02d}"

def determinar_turno(hora):
    """Determina o turno com base na hora"""
    if isinstance(hora, pd.Timestamp):
        hora = hora.hour
    
    if 7 <= hora < 15:
        return 'TURNO A'
    elif 15 <= hora < 23:
        return 'TURNO B'
    else:  # 23-7
        return 'TURNO C'

def calcular_tempos_por_periodo(dados, filtros, periodo, grupo='CLIENTE'):
    """Calcula tempos médios de espera por cliente/operação no período"""
    df = dados['base']
    df_medias = dados['medias']
    
    # Aplicar filtros de data
    mask = (
        (df['retirada'].dt.date >= filtros[periodo]['inicio']) &
        (df['retirada'].dt.date <= filtros[periodo]['fim'])
    )
    df_filtrado = df[mask].copy()
    
    # Determina o turno com base no horário de retirada
    df_filtrado['TURNO'] = df_filtrado['retirada'].apply(determinar_turno)
    
    # Aplicar filtros
    if filtros['cliente'] != ['Todos']:
        df_filtrado = df_filtrado[df_filtrado['CLIENTE'].isin(filtros['cliente'])]
    
    if filtros['operacao'] != ['Todas']:
        df_filtrado = df_filtrado[df_filtrado['OPERAÇÃO'].isin(filtros['operacao'])]
    
    if filtros['turno'] != ['Todos']:
        df_filtrado = df_filtrado[df_filtrado['TURNO'].isin(filtros['turno'])]
    
    if len(df_filtrado) == 0:
        st.warning(f"Nenhum dado encontrado para o período {periodo} com os filtros selecionados.")
        return pd.DataFrame()
    
    # Calcula média de espera usando 'tpesper' ao invés de 'tpespera'
    tempos = df_filtrado.groupby(grupo)['tpesper'].agg([
        ('media', 'mean'),
        ('contagem', 'count')
    ]).reset_index()
    
    # Converte tempo para minutos
    tempos['media'] = tempos['media'] / 60
    
    return tempos

def converter_para_minutos(valor):
    """Converte diferentes formatos de tempo para minutos"""
    if pd.isna(valor):
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    if isinstance(valor, str):
        try:
            partes = valor.split(':')
            if len(partes) == 2:
                horas, minutos = map(int, partes)
                return horas * 60 + minutos
            elif len(partes) == 3:
                horas, minutos, segundos = map(int, partes)
                return horas * 60 + minutos + segundos / 60
        except:
            return None
    if hasattr(valor, 'hour') and hasattr(valor, 'minute'):
        return valor.hour * 60 + valor.minute
    return None

def criar_grafico_comparativo(dados_p1, dados_p2, dados_medias, grupo='CLIENTE', filtros=None):
    """Cria gráfico comparativo de tempos médios entre períodos"""
    cores_tema = obter_cores_tema()
    
    # Ajusta os dados de meta se disponíveis
    if dados_medias is not None:
        try:
            dados_medias = dados_medias.iloc[1:].copy()
            dados_medias.columns = ['CLIENTE', 'OPERAÇÃO', 'TEMPO DE ATENDIMENTO (MEDIA)', 'TURNO A', 'TURNO B']
            dados_medias = dados_medias.reset_index(drop=True)
            
            dados_medias['TEMPO DE ATENDIMENTO (MEDIA)'] = pd.to_numeric(
                dados_medias['TEMPO DE ATENDIMENTO (MEDIA)'],
                errors='coerce'
            )
            dados_medias = dados_medias.dropna(subset=['TEMPO DE ATENDIMENTO (MEDIA)'])
        except Exception as e:
            dados_medias = None
    
    # Merge dos dados dos dois períodos
    df_comp = pd.merge(
        dados_p1,
        dados_p2,
        on=grupo,
        suffixes=('_p1', '_p2')
    )
    
    df_comp['variacao'] = ((df_comp['media_p2'] - df_comp['media_p1']) 
                          / df_comp['media_p1'] * 100)
    
    # Ordena por total decrescente
    df_comp['total'] = df_comp['media_p1'] + df_comp['media_p2']
    df_comp = df_comp.sort_values('total', ascending=False)
    
    fig = go.Figure()
    
    # Prepara legendas com data formatada
    legenda_p1 = "Período 1"
    legenda_p2 = "Período 2"
    if filtros:
        legenda_p1 = (f"Período 1 ({filtros['periodo1']['inicio'].strftime('%d/%m/%Y')} "
                      f"a {filtros['periodo1']['fim'].strftime('%d/%m/%Y')})")
        legenda_p2 = (f"Período 2 ({filtros['periodo2']['inicio'].strftime('%d/%m/%Y')} "
                      f"a {filtros['periodo2']['fim'].strftime('%d/%m/%Y')})")
    
    # Calcula o tamanho do texto baseado na largura das barras
    max_valor = max(df_comp['media_p1'].max(), df_comp['media_p2'].max())
    
    def calcular_tamanho_fonte(valor, is_periodo1=False, grupo='CLIENTE'):
        """Calcula o tamanho da fonte baseado no valor, período e grupo"""
        if grupo == 'OPERAÇÃO':
            if is_periodo1:
                min_size, max_size = 18, 24
            else:
                min_size, max_size = 16, 22
        else:
            if is_periodo1:
                min_size, max_size = 16, 22
            else:
                min_size, max_size = 14, 20
        
        if grupo == 'OPERAÇÃO':
            tamanho = min_size + (max_size - min_size) * (valor / max_valor) ** 0.15
        else:
            tamanho = min_size + (max_size - min_size) * (valor / max_valor) ** 0.25
        
        return max(min_size, min(max_size, tamanho))
    
    # Adiciona barras para período 1
    fig.add_trace(
        go.Bar(
            name=legenda_p1,
            y=df_comp[grupo],
            x=df_comp['media_p1'],
            orientation='h',
            text=[f"{formatar_tempo(x)} min" for x in df_comp['media_p1']],
            textposition='inside',
            marker_color=cores_tema['primaria'],
            textfont={
                'size': df_comp['media_p1'].apply(lambda x: calcular_tamanho_fonte(x, True, grupo)),
                'color': '#ffffff'
            },
            opacity=0.85
        )
    )
    
    # Adiciona barras para período 2
    fig.add_trace(
        go.Bar(
            name=legenda_p2,
            y=df_comp[grupo],
            x=df_comp['media_p2'],
            orientation='h',
            text=[f"{formatar_tempo(x)} min" for x in df_comp['media_p2']],
            textposition='inside',
            marker_color=cores_tema['secundaria'],
            textfont={
                'size': df_comp['media_p2'].apply(lambda x: calcular_tamanho_fonte(x, False, grupo)),
                'color': '#000000'
            },
            opacity=0.85
        )
    )
    
    # Adiciona linha de meta se disponível
    if dados_medias is not None and isinstance(dados_medias, pd.DataFrame) and not dados_medias.empty:
        try:
            coluna_meta = 'TEMPO DE ATENDIMENTO (MEDIA)'
            if coluna_meta in dados_medias.columns:
                metas = dados_medias[[grupo, coluna_meta]].dropna(subset=[coluna_meta])
                
                if not metas.empty:
                    df_metas = pd.merge(df_comp[[grupo]], metas, on=grupo, how='left')
                    df_metas = df_metas.dropna(subset=[coluna_meta])
                    
                    if not df_metas.empty:
                        fig.add_trace(
                            go.Scatter(
                                name='Meta Individual',
                                y=df_metas[grupo],
                                x=df_metas[coluna_meta],
                                mode='markers+text',
                                marker=dict(
                                    symbol='diamond',
                                    size=10,
                                    color=cores_tema['erro']
                                ),
                                text=[f"{formatar_tempo(x)} min" for x in df_metas[coluna_meta]],
                                textposition='middle right',
                                textfont=dict(color=cores_tema['erro'])
                            )
                        )
        except Exception as e:
            pass
    
    # Adiciona anotações de variação
    for i, row in df_comp.iterrows():
        cor = cores_tema['sucesso'] if row['variacao'] < 0 else cores_tema['erro']
        fig.add_annotation(
            y=row[grupo],
            x=row['total'],
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
            'text': f'Comparativo de Tempo Médio de Espera por {grupo}',
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
        title='Tempo Médio (minutos)',
        title_font={'color': cores_tema['texto']},
        tickfont={'color': cores_tema['texto']},
        gridcolor=cores_tema['grid'],
        showline=True,
        linewidth=1,
        linecolor=cores_tema['grid'],
        zeroline=False
    )
    
    fig.update_yaxes(
        title=grupo,
        title_font={'color': cores_tema['texto']},
        tickfont={'color': cores_tema['texto']},
        gridcolor=cores_tema['grid'],
        showline=True,
        linewidth=1,
        linecolor=cores_tema['grid'],
        zeroline=False
    )
    
    return fig

def gerar_insights(df_comp, grupo='CLIENTE', titulo="Insights", dados_medias=None):
    """Gera insights sobre os tempos de espera"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Visão Geral")
        media_geral_p1 = (df_comp['media_p1'] * df_comp['contagem_p1']).sum() / df_comp['contagem_p1'].sum()
        media_geral_p2 = (df_comp['media_p2'] * df_comp['contagem_p2']).sum() / df_comp['contagem_p2'].sum()
        var_media = ((media_geral_p2 - media_geral_p1) / media_geral_p1 * 100)
        
        st.markdown(f"""
        - Tempo médio de espera período 1: **{formatar_tempo(media_geral_p1)} min**
        - Tempo médio de espera período 2: **{formatar_tempo(media_geral_p2)} min**
        - Variação média: **{var_media:+.1f}%**
        """)
        
        # Análise de metas se disponível
        if dados_medias is not None and isinstance(dados_medias, pd.DataFrame):
            colunas_disponiveis = dados_medias.columns
            coluna_meta = None
            
            for nome_coluna in ['TEMPO DE ATENDIMENTO (MEDIA)', 'META', 'MÉDIA', 'MEDIA']:
                if nome_coluna in colunas_disponiveis:
                    coluna_meta = nome_coluna
                    break
            
            if coluna_meta and grupo in colunas_disponiveis:
                st.markdown("---")
                st.markdown("📋 **Análise de Espera x Meta**")
                
                try:
                    dados_medias[coluna_meta] = dados_medias[coluna_meta].apply(converter_para_minutos)
                    dados_medias = dados_medias.dropna(subset=[coluna_meta])
                    
                    df_analise = pd.merge(
                        df_comp,
                        dados_medias[[grupo, coluna_meta]],
                        on=grupo,
                        how='left'
                    )
                    
                    # Análise de espera x meta
                    dentro_meta = df_analise[df_analise['media_p2'] <= df_analise[coluna_meta]]
                    fora_meta = df_analise[df_analise['media_p2'] > df_analise[coluna_meta]]
                    
                    total = len(df_analise)
                    perc_dentro = (len(dentro_meta) / total * 100) if total > 0 else 0
                    
                    st.markdown(f"""
                    No período mais recente:
                    - **{len(dentro_meta)}** ({perc_dentro:.1f}%) dentro da meta
                    - **{len(fora_meta)}** ({100-perc_dentro:.1f}%) acima da meta
                    """)
                
                except Exception as e:
                    st.warning(f"Não foi possível analisar as metas: {str(e)}")
    
    with col2:
        st.subheader("📈 Maiores Variações")
        melhorias = df_comp[df_comp['variacao'] < 0].sort_values('variacao')
        pioras = df_comp[df_comp['variacao'] > 0].sort_values('variacao', ascending=False)
        
        if not melhorias.empty:
            st.markdown("**Maiores Reduções no Tempo de Espera:**")
            for _, row in melhorias.head(3).iterrows():
                reducao = row['media_p1'] - row['media_p2']
                st.markdown(f"""
                - {row[grupo]}: 
                    - Redução: {row['variacao']:.1f}% :green[⬇]
                    - De {formatar_tempo(row['media_p1'])} para {formatar_tempo(row['media_p2'])} min
                    - Economia de {formatar_tempo(reducao)} min por atendimento
                """)
        
        if not pioras.empty:
            st.markdown("**Maiores Aumentos no Tempo de Espera:**")
            for _, row in pioras.head(3).iterrows():
                aumento = row['media_p2'] - row['media_p1']
                st.markdown(f"""
                - {row[grupo]}:
                    - Aumento: +{row['variacao']:.1f}% :red[⬆]
                    - De {formatar_tempo(row['media_p1'])} para {formatar_tempo(row['media_p2'])} min
                    - Acréscimo de {formatar_tempo(aumento)} min por atendimento
                """)
    
    # Nova seção de alertas
    st.markdown("---")
    st.subheader("⚠️ Pontos de Atenção")
    
    # Análise de tendências
    media_global = df_comp['media_p2'].mean()
    desvio_padrao = df_comp['media_p2'].std()
    
    muito_acima = df_comp[df_comp['media_p2'] > (media_global + 2*desvio_padrao)]
    tendencia_alta = df_comp[(df_comp['variacao'] > 20) & (df_comp['media_p2'] > media_global)]
    
    col1, col2 = st.columns(2)
    
    with col1:
        if not muito_acima.empty:
            st.markdown("**Tempos Críticos de Espera:**")
            for _, row in muito_acima.iterrows():
                st.markdown(f"""
                - {row[grupo]}:
                    - Tempo atual: {formatar_tempo(row['media_p2'])} min
                    - {row['variacao']:+.1f}% vs período anterior
                    - :red[⚠️ Muito acima da média geral de {formatar_tempo(media_global)} min]
                """)
    
    with col2:
        if not tendencia_alta.empty:
            st.markdown("**Tendência de Aumento Significativo:**")
            for _, row in tendencia_alta.iterrows():
                st.markdown(f"""
                - {row[grupo]}:
                    - Aumento de {row['variacao']:+.1f}%
                    - De {formatar_tempo(row['media_p1'])} para {formatar_tempo(row['media_p2'])} min
                    - :orange[⚠️ Necessita investigação]
                """)

    # Seção de Recomendações
    st.markdown("---")
    st.subheader("💡 Recomendações")
    
    # Análise de volume vs tempo
    alto_volume = df_comp.nlargest(3, 'contagem_p2')
    st.markdown("**Foco em Alto Volume:**")
    for _, row in alto_volume.iterrows():
        st.markdown(f"""
        - {row[grupo]}:
            - Volume: {row['contagem_p2']} atendimentos
            - Tempo médio de espera: {formatar_tempo(row['media_p2'])} min
            - Impacto na operação: {'🔴 Alto' if row['media_p2'] > media_global else '🟢 Dentro do esperado'}
        """)

def mostrar_aba(dados, filtros):
    """Mostra a aba de Tempo de Espera"""
    st.header("Tempo de Espera em Fila")
    
    try:
        st.session_state['tema_atual'] = detectar_tema()
        
        tipo_analise = st.radio(
            "Analisar por:",
            ["Cliente", "Operação"],
            horizontal=True,
            key="radio_espera"
        )
        
        grupo = "CLIENTE" if tipo_analise == "Cliente" else "OPERAÇÃO"
        
        tempos_p1 = calcular_tempos_por_periodo(dados, filtros, 'periodo1', grupo)
        tempos_p2 = calcular_tempos_por_periodo(dados, filtros, 'periodo2', grupo)
        
        if tempos_p1.empty or tempos_p2.empty:
            st.warning("Não há dados para exibir no período selecionado.")
            return
        
        medias = dados.get('medias')
        if medias is not None:
            medias = medias.iloc[1:].copy()
            medias.columns = ['CLIENTE', 'OPERAÇÃO', 'TEMPO DE ATENDIMENTO (MEDIA)', 'TURNO A', 'TURNO B']
            medias = medias.reset_index(drop=True)
        
        fig = criar_grafico_comparativo(tempos_p1, tempos_p2, medias, grupo, filtros)
        st.plotly_chart(
            fig, 
            use_container_width=True,
            key=f"grafico_espera_{grupo}_{st.session_state['tema_atual']}"
        )
        
        st.markdown("---")
        with st.expander("📊 Ver Insights", expanded=True):
            df_comp = pd.merge(
                tempos_p1,
                tempos_p2,
                on=grupo,
                suffixes=('_p1', '_p2')
            )
            df_comp['variacao'] = ((df_comp['media_p2'] - df_comp['media_p1']) 
                                 / df_comp['media_p1'] * 100)
            gerar_insights(df_comp, grupo, dados_medias=medias)
    
    except Exception as e:
        st.error("Erro ao gerar a aba de Tempo de Espera")
        st.exception(e)
