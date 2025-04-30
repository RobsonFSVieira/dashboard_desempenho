import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def calcular_metricas_turno(dados, turno, filtros):
    """Calcula métricas agregadas por turno"""
    df = dados['base']
    
    # Aplicar filtros de período
    mask = (
        (df['retirada'].dt.date >= filtros['periodo2']['inicio']) &
        (df['retirada'].dt.date <= filtros['periodo2']['fim'])
    )
    df_filtrado = df[mask]
    
    # Calcular turno para cada registro
    df_filtrado['turno'] = df_filtrado['inicio'].dt.hour.map(
        lambda x: 'TURNO A' if 6 <= x < 14 else ('TURNO B' if 14 <= x < 22 else 'TURNO C')
    )
    
    # Filtrar por turno específico
    df_turno = df_filtrado[df_filtrado['turno'] == turno]
    
    return {
        'total_atendimentos': len(df_turno),
        'media_tempo': df_turno['tpatend'].mean() / 60,
        'colaboradores': len(df_turno['usuário'].unique()),
        'operacoes': len(df_turno['OPERAÇÃO'].unique()),
        'clientes': len(df_turno['CLIENTE'].unique()),
        'distribuicao_ops': df_turno['OPERAÇÃO'].value_counts().to_dict(),
        'distribuicao_clientes': df_turno['CLIENTE'].value_counts().to_dict()
    }

def mostrar_comparativo_turnos(dados, metricas_turnos):
    """Mostra gráficos comparativos entre turnos"""
    # Criar DataFrame para comparação
    comp_data = pd.DataFrame.from_dict(metricas_turnos, orient='index')
    
    # Gráfico de barras para métricas principais
    fig_metricas = go.Figure()
    metricas = ['total_atendimentos', 'colaboradores', 'operacoes', 'clientes']
    
    for metrica in metricas:
        fig_metricas.add_trace(go.Bar(
            name=metrica.replace('_', ' ').title(),
            x=list(metricas_turnos.keys()),
            y=comp_data[metrica]
        ))
    
    fig_metricas.update_layout(
        title="Comparativo de Métricas por Turno",
        barmode='group'
    )
    
    st.plotly_chart(fig_metricas, use_container_width=True)

def mostrar_aba(dados, filtros):
    """Mostra a aba de análise de polivalência por turnos"""
    st.header(f"Análise de Polivalência por Turnos ({filtros['periodo2']['inicio'].strftime('%d/%m/%Y')} até {filtros['periodo2']['fim'].strftime('%d/%m/%Y')})")
    
    try:
        # Calcular métricas para cada turno
        metricas_turnos = {
            'TURNO A': calcular_metricas_turno(dados, 'TURNO A', filtros),
            'TURNO B': calcular_metricas_turno(dados, 'TURNO B', filtros),
            'TURNO C': calcular_metricas_turno(dados, 'TURNO C', filtros)
        }
        
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            turno_selecionado = st.selectbox(
                "Selecionar Turno",
                options=["Todos"] + sorted(metricas_turnos.keys()),
                key="turno_selectbox_polivalencia_turnos"  # Added unique key
            )
        
        with col2:
            cliente_filtro = st.selectbox(
                "Selecionar Cliente",
                options=["Todos"] + sorted(dados['base']['CLIENTE'].unique().tolist()),
                key="cliente_selectbox_polivalencia_turnos"  # Added unique key
            )
        
        # Mostrar comparativo geral de turnos
        mostrar_comparativo_turnos(dados, metricas_turnos)
        
        # Mostrar detalhes do turno selecionado se não for "Todos"
        if turno_selecionado != "Todos":
            metricas = metricas_turnos[turno_selecionado]
            
            # Métricas do turno
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Atendimentos", metricas['total_atendimentos'])
            with col2:
                st.metric("Média Tempo (min)", f"{metricas['media_tempo']:.1f}")
            with col3:
                st.metric("Colaboradores", metricas['colaboradores'])
            with col4:
                st.metric("Operações", metricas['operacoes'])
    
    except Exception as e:
        st.error("Erro ao analisar dados de polivalência por turnos")
        st.exception(e)
