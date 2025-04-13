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
    
    # Debug info
    st.write(f"Total registros antes dos filtros: {len(df)}")
    
    # Aplicar filtros de data
    mask = (
        (df['retirada'].dt.date >= filtros[periodo]['inicio']) &
        (df['retirada'].dt.date <= filtros[periodo]['fim'])
    )
    df_filtrado = df[mask].copy()
    st.write(f"Registros após filtro de data: {len(df_filtrado)}")
    
    # Determina o turno com base no horário de retirada
    df_filtrado['TURNO'] = df_filtrado['retirada'].apply(determinar_turno)
    
    # Aplicar filtros
    if filtros['cliente'] != ['Todos']:
        df_filtrado = df_filtrado[df_filtrado['CLIENTE'].isin(filtros['cliente'])]
        st.write(f"Registros após filtro de cliente: {len(df_filtrado)}")
    
    if filtros['operacao'] != ['Todas']:
        df_filtrado = df_filtrado[df_filtrado['OPERAÇÃO'].isin(filtros['operacao'])]
        st.write(f"Registros após filtro de operação: {len(df_filtrado)}")
    
    if filtros['turno'] != ['Todos']:
        df_filtrado = df_filtrado[df_filtrado['TURNO'].isin(filtros['turno'])]
        st.write(f"Registros após filtro de turno: {len(df_filtrado)}")
    
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
    
    # Calcula o tamanho do texto
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
    
    # Adiciona barras e anotações como em tempo_atend.py
    # ...rest of plotting code from tempo_atend.py...
    
    # Atualiza layout
    fig.update_layout(
        title={
            'text': f'Comparativo de Tempo Médio de Espera por {grupo}',
            'font': {'size': 16, 'color': cores_tema['texto']}
        },
        # ...rest of layout settings from tempo_atend.py...
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
        
        # Análise de metas como em tempo_atend.py
        # ...rest of insights code from tempo_atend.py...

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
