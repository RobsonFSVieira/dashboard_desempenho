import streamlit as st
from visualizacao.dashboards.operacoes_clientes import (
    mov_cliente, mov_operacao, tempo_atend, permanencia, turnos, comboio_i, comboio_ii
)
from visualizacao.dashboards.desenvolvimento_pessoas import tempo_atend as dev_tempo_atend

# Importação da aba Geral
from visualizacao.dashboards.operacoes_clientes import visao_geral

def criar_dashboard(dados, filtros, tipo_dashboard):
    """Cria o dashboard com base no tipo selecionado"""
    if dados is None or filtros is None:
        st.info("📊 Carregue os dados e selecione os filtros para visualizar o dashboard.")
        return
    
    try:
        if tipo_dashboard == "Performance Cliente/Operação":
            tabs = st.tabs([
                "Geral",
                "Movimentação por Cliente", 
                "Movimentação por Operação",
                "Tempo de Atendimento",
                "Permanência",
                "Turnos",
                "Chegada em Comboio I",
                "Chegada em Comboio II"
            ])
            
            with tabs[0]:
                visao_geral.mostrar_aba(dados, filtros)
            
            with tabs[1]:
                mov_cliente.mostrar_aba(dados, filtros)
            
            with tabs[2]:
                mov_operacao.mostrar_aba(dados, filtros)
                
            with tabs[3]:
                tempo_atend.mostrar_aba(dados, filtros)
                
            with tabs[4]:
                permanencia.mostrar_aba(dados, filtros)
                
            with tabs[5]:
                turnos.mostrar_aba(dados, filtros)
                
            with tabs[6]:
                comboio_i.mostrar_aba(dados, filtros)
                
            with tabs[7]:
                comboio_ii.mostrar_aba(dados, filtros)
                
        elif tipo_dashboard == "Desenvolvimento de Pessoas":
            tabs = st.tabs([
                "Tempo de Atendimento"
            ])
            
            with tabs[0]:
                dev_tempo_atend.mostrar_aba(dados, filtros)
                
    except Exception as e:
        st.error(f"Erro ao gerar o dashboard: {str(e)}")
        st.exception(e)