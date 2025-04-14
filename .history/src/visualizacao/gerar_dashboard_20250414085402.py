import streamlit as st
from visualizacao.dashboards.operacoes_clientes import geral, mov_cliente, mov_operacao, tempo_atend, espera, permanencia, turnos, comboio_i, comboio_ii
from visualizacao.dashboards.desenvolvimento_pessoas import tempo_atend as dev_tempo_atend

def criar_dashboard(dados, filtros, tipo_dashboard):
    """Cria o dashboard com base no tipo selecionado"""
    if dados is None:
        st.info("📊 Carregue os dados para visualizar o dashboard.")
        return
    
    # Verifica e ajusta as datas dos filtros com base nos dados disponíveis
    df = dados['base']
    data_min = df['retirada'].dt.date.min()
    data_max = df['retirada'].dt.date.max()
    
    if filtros is None or filtros['periodo2']['inicio'] > data_max or filtros['periodo2']['fim'] < data_min:
        if filtros is None:
            filtros = {}
        filtros['periodo2'] = {'inicio': data_min, 'fim': data_max}
    
    try:
        if tipo_dashboard == "Performance Cliente/Operação":
            tabs = st.tabs([
                "Visão Geral", 
                "Movimentação por Cliente", 
                "Movimentação por Operação",
                "Tempo de Atendimento",
                "Tempo de Espera em Fila",
                "Permanência",
                "Turnos",
                "Chegada em Comboio I",
                "Chegada em Comboio II"
            ])
            
            # Exibe cada aba com tratamento de erro individualizado
            with tabs[0]:
                try:
                    geral.mostrar_aba(dados, filtros)
                except Exception as e:
                    st.error(f"Erro na aba Visão Geral: {str(e)}")
                    st.exception(e)
            
            with tabs[1]:
                try:
                    mov_cliente.mostrar_aba(dados, filtros)
                except Exception as e:
                    st.error(f"Erro na aba Movimentação por Cliente: {str(e)}")
                    st.exception(e)
            
            with tabs[2]:
                try:
                    mov_operacao.mostrar_aba(dados, filtros)
                except Exception as e:
                    st.error(f"Erro na aba Movimentação por Operação: {str(e)}")
                    st.exception(e)
            
            with tabs[3]:
                try:
                    tempo_atend.mostrar_aba(dados, filtros)
                except Exception as e:
                    st.error(f"Erro na aba Tempo de Atendimento: {str(e)}")
            
            with tabs[4]:
                try:
                    espera.mostrar_aba(dados, filtros)
                except Exception as e:
                    st.error(f"Erro na aba Tempo de Espera em Fila: {str(e)}")
            
            with tabs[5]:
                try:
                    permanencia.mostrar_aba(dados, filtros)
                except Exception as e:
                    st.error(f"Erro na aba Permanência: {str(e)}")
            
            with tabs[6]:
                try:
                    turnos.mostrar_aba(dados, filtros)
                except Exception as e:
                    st.error(f"Erro na aba Turnos: {str(e)}")
            
            with tabs[7]:
                try:
                    comboio_i.mostrar_aba(dados, filtros)
                except Exception as e:
                    st.error(f"Erro na aba Chegada em Comboio I: {str(e)}")
            
            with tabs[8]:
                try:
                    comboio_ii.mostrar_aba(dados, filtros)
                except Exception as e:
                    st.error(f"Erro na aba Chegada em Comboio II: {str(e)}")
                
        elif tipo_dashboard == "Desenvolvimento de Pessoas":
            tabs = st.tabs([
                "Tempo de Atendimento"
            ])
            
            with tabs[0]:
                try:
                    dev_tempo_atend.mostrar_aba(dados, filtros)
                except Exception as e:
                    st.error(f"Erro na aba Desenvolvimento de Pessoas: {str(e)}")
                
    except Exception as e:
        st.error(f"Erro ao gerar o dashboard: {str(e)}")
        st.exception(e)