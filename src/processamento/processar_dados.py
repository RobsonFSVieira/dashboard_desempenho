import streamlit as st
import pandas as pd

@st.cache_data
def criar_mascaras_periodo(df, filtros):
    """Cria máscaras de período reutilizáveis"""
    return {
        'periodo1': (
            (df['retirada'].dt.date >= filtros['periodo1']['inicio']) &
            (df['retirada'].dt.date <= filtros['periodo1']['fim'])
        ),
        'periodo2': (
            (df['retirada'].dt.date >= filtros['periodo2']['inicio']) &
            (df['retirada'].dt.date <= filtros['periodo2']['fim'])
        )
    }

@st.cache_data
def calcular_metricas_base(df):
    """Calcula métricas básicas reutilizáveis"""
    return {
        'media_atendimento': df['tpatend'].mean() / 60,
        'media_espera': df['tpesper'].mean() / 60,
        'clientes_unicos': df['CLIENTE'].nunique(),
        'operacoes_unicas': df['OPERAÇÃO'].nunique()
    }
