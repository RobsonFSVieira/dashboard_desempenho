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

def criar_tabela_ranking(dados, turno):
    """Cria uma tabela estilizada com o ranking de colaboradores"""
    df = dados['base']
    df['turno'] = df['inicio'].dt.hour.map(
        lambda x: 'TURNO A' if 6 <= x < 14 else ('TURNO B' if 14 <= x < 22 else 'TURNO C')
    )
    
    if turno != "Todos":
        df = df[df['turno'] == turno]
    
    # Filtrar usuários, excluindo 'Ceparking'
    usuarios = [user for user in df['usuário'].unique() if user != 'Ceparking']
    
    # Calcular métricas por colaborador
    ranking = []
    for usuario in usuarios:
        df_user = df[df['usuário'] == usuario]
        ops_count = len(df_user['OPERAÇÃO'].unique())
        clientes_count = len(df_user['CLIENTE'].unique())
        total_atend = len(df_user)
        
        # Calcular score normalizado
        score = (ops_count / df_user['OPERAÇÃO'].nunique() * 0.4 +
                clientes_count / df_user['CLIENTE'].nunique() * 0.4 +
                total_atend / len(df) * 0.2)
        
        ranking.append({
            'POS': '',  # Será preenchido após ordenação
            'Colaborador': usuario,
            'Score': score * 100  # Converter para percentual
        })
    
    # Criar DataFrame e ordenar
    ranking_df = pd.DataFrame(ranking)
    ranking_df = ranking_df.sort_values('Score', ascending=False).reset_index(drop=True)
    
    # Adicionar posição com º
    ranking_df['POS'] = ranking_df.index.map(lambda x: f"{x+1}º")
    
    # Formatar score com uma casa decimal
    ranking_df['Score'] = ranking_df['Score'].map(lambda x: f"{x:.1f}")
    
    return ranking_df

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
                key="turno_selectbox_polivalencia_turnos"
            )
        
        with col2:
            cliente_filtro = st.selectbox(
                "Selecionar Cliente",
                options=["Todos"] + sorted(dados['base']['CLIENTE'].unique().tolist()),
                key="cliente_selectbox_polivalencia_turnos"
            )
        
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
        
        # Adicionar tabela de ranking
        st.markdown("### 📊 Ranking de Polivalência")
        ranking_df = criar_tabela_ranking(dados, turno_selecionado)
        
        # Estilizar e exibir a tabela
        st.dataframe(
            ranking_df,
            column_config={
                "POS": st.column_config.Column(
                    "POS",
                    width=70,
                ),
                "Colaborador": st.column_config.Column(
                    "Colaborador",
                    width=300,
                ),
                "Score": st.column_config.Column(
                    "Score",
                    width=100,
                )
            },
            hide_index=True
        )
    
    except Exception as e:
        st.error("Erro ao analisar dados de polivalência por turnos")
        st.exception(e)
