import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
from datetime import datetime, timedelta

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

def formatar_tempo(segundos):
    """Formata o tempo em segundos para o formato HH:MM:SS"""
    horas = int(segundos // 3600)
    minutos = int((segundos % 3600) // 60)
    segs = int(segundos % 60)
    return f"{horas:02d}:{minutos:02d}:{segs:02d} min"

def calcular_ociosidade_por_periodo(dados, filtros, periodo):
    """Calcula o tempo de ociosidade por colaborador no período especificado"""
    df = dados['base']
    
    if df.empty:
        st.warning("Base de dados está vazia")
        return pd.DataFrame()
    
    # Aplicar filtros de data
    mask = (
        (df['retirada'].dt.date >= filtros[periodo]['inicio']) &
        (df['retirada'].dt.date <= filtros[periodo]['fim'])
    )
    df_filtrado = df[mask].copy()
    
    # Aplicar filtros adicionais
    if filtros['cliente'] != ['Todos']:
        df_filtrado = df_filtrado[df_filtrado['CLIENTE'].isin(filtros['cliente'])]
        
    if filtros['operacao'] != ['Todas']:
        df_filtrado = df_filtrado[df_filtrado['OPERAÇÃO'].isin(filtros['operacao'])]
        
    if filtros['turno'] != ['Todos']:
        def get_turno(hour):
            if 7 <= hour < 15:
                return 'TURNO A'
            elif 15 <= hour < 23:
                return 'TURNO B'
            else:
                return 'TURNO C'
        df_filtrado = df_filtrado[df_filtrado['retirada'].dt.hour.apply(get_turno).isin(filtros['turno'])]
    
    # Ordenar por usuário e data/hora
    df_filtrado = df_filtrado.sort_values(['usuário', 'fim'])
    
    # Calcular ociosidade entre atendimentos
    ociosidade = []
    for usuario in df_filtrado['usuário'].unique():
        atendimentos_usuario = df_filtrado[df_filtrado['usuário'] == usuario]
        
        # Agrupar por dia
        for data in atendimentos_usuario['fim'].dt.date.unique():
            atend_dia = atendimentos_usuario[atendimentos_usuario['fim'].dt.date == data]
            
            if len(atend_dia) > 1:
                # Calcular intervalos entre atendimentos
                inicio_prox = atend_dia['inicio'].iloc[1:].values
                fim_atual = atend_dia['fim'].iloc[:-1].values
                
                # Converter para datetime do Python antes de calcular a diferença
                tempos_ociosos = []
                for t1, t2 in zip(fim_atual, inicio_prox):
                    try:
                        # Converter para datetime do Python
                        t1_py = pd.Timestamp(t1).to_pydatetime()
                        t2_py = pd.Timestamp(t2).to_pydatetime()
                        # Calcular diferença em segundos
                        diferenca = (t2_py - t1_py).total_seconds()
                        tempos_ociosos.append(diferenca)
                    except Exception as e:
                        st.warning(f"Erro ao calcular diferença: {str(e)}")
                        continue
                
                # Desconsiderar intervalos maiores que 2 horas (7200 segundos)
                tempos_validos = [t for t in tempos_ociosos if t <= 7200]
                
                if tempos_validos:
                    tempo_medio = sum(tempos_validos) / len(tempos_validos)
                    ociosidade.append({
                        'colaborador': usuario,
                        'tempo_ocioso': tempo_medio
                    })
    
    if not ociosidade:
        return pd.DataFrame()
    
    # Criar DataFrame com média por colaborador
    df_ociosidade = pd.DataFrame(ociosidade)
    df_ociosidade = df_ociosidade.groupby('colaborador')['tempo_ocioso'].mean().reset_index()
    
    return df_ociosidade

def criar_grafico_comparativo(dados_p1, dados_p2, filtros):
    """Cria gráfico comparativo de ociosidade entre períodos"""
    # ...código similar ao qtd_atendimento.py, adaptado para tempos...

def gerar_insights_ociosidade(ocio_p1, ocio_p2):
    """Gera insights sobre a ociosidade dos colaboradores"""
    # ...código similar ao qtd_atendimento.py, adaptado para análise de tempos...

def mostrar_aba(dados, filtros):
    """Mostra a aba de Análise de Ociosidade"""
    st.header("Análise de Ociosidade")
    
    try:
        st.session_state['tema_atual'] = detectar_tema()
        
        ocio_p1 = calcular_ociosidade_por_periodo(dados, filtros, 'periodo1')
        ocio_p2 = calcular_ociosidade_por_periodo(dados, filtros, 'periodo2')
        
        if ocio_p1.empty or ocio_p2.empty:
            st.warning("Não há dados suficientes para análise de ociosidade no período selecionado.")
            return
        
        fig = criar_grafico_comparativo(ocio_p1, ocio_p2, filtros)
        if fig:
            st.plotly_chart(
                fig,
                use_container_width=True,
                key=f"grafico_ociosidade_{st.session_state['tema_atual']}"
            )
        
        st.markdown("---")
        st.subheader("📈 Análise Detalhada")
        with st.expander("Ver análise detalhada", expanded=True):
            gerar_insights_ociosidade(ocio_p1, ocio_p2)
    
    except Exception as e:
        st.error(f"Erro ao mostrar aba: {str(e)}")
        st.exception(e)
