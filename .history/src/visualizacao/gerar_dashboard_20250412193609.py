import streamlit as st
from visualizacao.dashboards.operacoes_clientes import (
    geral, mov_cliente, mov_operacao, tempo_atend,
    permanencia, turnos, comboio_i, comboio_ii, gates
)
from visualizacao.dashboards.desenvolvimento_pessoas import (
    performance, tempo_atend as tempo_atend_rh,
    ociosidade, ocorrencias
)

def criar_dashboard(dados, filtros, tipo_dashboard):
    """Cria o dashboard com base no tipo selecionado"""
    if dados is None or filtros is None:
        st.warning("⚠️ Carregue os arquivos e configure os filtros para continuar.")
        return
    
    try:
        if tipo_dashboard == "Performance Cliente/Operação":
            criar_dashboard_operacoes(dados, filtros)
        else:
            criar_dashboard_pessoas(dados, filtros)
            
    except Exception as e:
        st.error("❌ Erro ao gerar o dashboard")
        st.exception(e)

def criar_dashboard_operacoes(dados, filtros):
    """Cria o dashboard de operações"""
    abas = st.tabs([
        "Geral",
        "Movimentação por Cliente",
        "Movimentação por Operação",
        "Tempo de Atendimento",
        "Permanência",
        "Turno",
        "Chegada em Comboio I",
        "Chegada em Comboio II",
        "Gates em Atividade"
    ])
    
    with abas[0]:
        geral.mostrar_aba(dados, filtros)
    
    with abas[1]:
        mov_cliente.mostrar_aba(dados, filtros)
        
    with abas[2]:
        mov_operacao.mostrar_aba(dados, filtros)
        
    with abas[3]:
        tempo_atend.mostrar_aba(dados, filtros)
        
    with abas[4]:
        permanencia.mostrar_aba(dados, filtros)
        
    with abas[5]:
        turnos.mostrar_aba(dados, filtros)
        
    with abas[6]:
        comboio_i.mostrar_aba(dados, filtros)
        
    with abas[7]:
        comboio_ii.mostrar_aba(dados, filtros)
        
    with abas[8]:
        gates.mostrar_aba(dados, filtros)

def criar_dashboard_pessoas(dados, filtros):
    """Cria o dashboard de desenvolvimento de pessoas"""
    abas = st.tabs([
        "Performance de Atendimento",
        "Tempo de Atendimento",
        "Tempo de Ociosidade",
        "Ocorrências"
    ])
    
    with abas[0]:
        performance.mostrar_aba(dados, filtros)
        
    with abas[1]:
        tempo_atend_rh.mostrar_aba(dados, filtros)
        
    with abas[2]:
        ociosidade.mostrar_aba(dados, filtros)
        
    with abas[3]:
        ocorrencias.mostrar_aba(dados, filtros)