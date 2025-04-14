import pandas as pd
import streamlit as st
from datetime import datetime

def carregar_dados():
    """Carrega e processa os dados do arquivo Excel"""
    try:
        # Carregar arquivo base
        df_base = pd.read_excel('base.xlsx')
        
        # Converter colunas de data/hora
        for col in ['retirada', 'inicio', 'fim']:
            df_base[col] = pd.to_datetime(df_base[col])
        
        # Calcular tempo de permanência
        df_base['tempo_permanencia'] = (df_base['fim'] - df_base['inicio']).dt.total_seconds()
        
        # Carregar arquivo de médias se existir
        try:
            df_medias = pd.read_excel('medias.xlsx')
        except Exception as e:
            st.warning("Arquivo de médias não encontrado. Algumas funcionalidades podem estar limitadas.")
            df_medias = None
        
        return {
            'base': df_base,
            'medias': df_medias
        }
        
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return None