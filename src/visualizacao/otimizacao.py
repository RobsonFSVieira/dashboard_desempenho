import streamlit as st

@st.cache_resource
def criar_layout_padrao():
    """Define layout padrão para reutilização"""
    return {
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'showlegend': True,
        'legend': {
            'orientation': 'h',
            'yanchor': 'bottom',
            'y': 1.02,
            'xanchor': 'right',
            'x': 1
        }
    }

@st.cache_data
def preparar_dados_grafico(_df, grupo_by, metricas):
    """Prepara dados para gráficos com cache"""
    return _df.groupby(grupo_by)[metricas].agg(['mean', 'count']).reset_index()
