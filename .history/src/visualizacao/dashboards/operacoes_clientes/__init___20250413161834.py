import streamlit as st
from . import tempo_atend
from . import espera  # Add import for wait time module

def mostrar_dashboard(dados, filtros):
    """Mostra o dashboard de operações e clientes"""
    # Create tabs in specific order
    aba_tempo_atend, aba_espera = st.tabs([
        "Tempo de Atendimento",
        "Tempo de Espera em Fila"
    ])
    
    with aba_tempo_atend:
        tempo_atend.mostrar_aba(dados, filtros)
    
    with aba_espera:
        espera.mostrar_aba(dados, filtros)
