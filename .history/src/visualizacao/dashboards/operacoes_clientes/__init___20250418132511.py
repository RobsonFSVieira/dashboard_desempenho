import streamlit as st
from . import tempo_atend
from . import espera
from . import permanencia
from . import gates_hora  # Novo import

def mostrar_dashboard(dados, filtros):
    """Mostra o dashboard de operações e clientes"""
    aba_tempo_atend, aba_espera, aba_permanencia, aba_gates = st.tabs([
        "Tempo de Atendimento",
        "Tempo de Espera em Fila",
        "Permanência",
        "Gates em Atividade/Hora"  # Nova aba
    ])
    
    with aba_tempo_atend:
        tempo_atend.mostrar_aba(dados, filtros)
    
    with aba_espera:
        espera.mostrar_aba(dados, filtros)
    
    with aba_permanencia:
        permanencia.mostrar_aba(dados, filtros)
        
    with aba_gates:  # Novo bloco
        gates_hora.mostrar_aba(dados, filtros)
