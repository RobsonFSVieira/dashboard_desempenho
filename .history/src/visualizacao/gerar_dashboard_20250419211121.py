import streamlit as st
from visualizacao.dashboards.operacoes_clientes import geral, mov_cliente, mov_operacao, tempo_atend, espera, permanencia, turnos, comboio_i, comboio_ii, gates_hora
from visualizacao.dashboards.desenvolvimento_pessoas import visao_geral, colaborador

def criar_dashboard(dados, filtros, tipo_dashboard):
    """Cria o dashboard com base no tipo selecionado"""
    if dados is None or filtros is None:
        st.info("📊 Carregue os dados e selecione os filtros para visualizar o dashboard.")
        return
    
    # Validar dados de entrada
    if not isinstance(dados, dict) or 'base' not in dados:
        st.error("Formato de dados inválido. Verifique a estrutura dos dados.")
        return
    
    try:
        # Verificar se há dados para o período selecionado
        df = dados['base']
        if len(df) == 0:
            st.warning("Não há dados disponíveis para o período selecionado.")
            return
            
        if tipo_dashboard == "Performance Cliente/Operação":
            # Criar cache de estado para evitar recálculos
            if 'dashboard_state' not in st.session_state:
                st.session_state['dashboard_state'] = {}
            
            tabs = st.tabs([
                "Visão Geral", 
                "Movimentação por Cliente", 
                "Movimentação por Operação",
                "Tempo de Atendimento",
                "Tempo de Espera em Fila",
                "Permanência",
                "Turnos",
                "Gates em Atividade/Hora",
                "Chegada em Comboio I",
                "Chegada em Comboio II"
            ])
            
            # Dicionário de funções de aba com tratamento de erro
            tab_functions = {
                0: ('Visão Geral', geral.mostrar_aba),
                1: ('Movimentação por Cliente', mov_cliente.mostrar_aba),
                2: ('Movimentação por Operação', mov_operacao.mostrar_aba),
                3: ('Tempo de Atendimento', tempo_atend.mostrar_aba),
                4: ('Tempo de Espera em Fila', espera.mostrar_aba),
                5: ('Permanência', permanencia.mostrar_aba),
                6: ('Turnos', turnos.mostrar_aba),
                7: ('Gates em Atividade/Hora', gates_hora.mostrar_aba),
                8: ('Chegada em Comboio I', comboio_i.mostrar_aba),
                9: ('Chegada em Comboio II', comboio_ii.mostrar_aba)
            }
            
            # Exibir abas com tratamento de erro aprimorado
            for i, tab in enumerate(tabs):
                with tab:
                    try:
                        tab_name, tab_func = tab_functions[i]
                        st.session_state['current_tab'] = tab_name
                        
                        # Adicionar spinner durante o carregamento
                        with st.spinner(f'Carregando {tab_name}...'):
                            tab_func(dados, filtros)
                            
                    except Exception as e:
                        st.error(f"Erro ao carregar a aba {tab_functions[i][0]}")
                        with st.expander("Detalhes do erro"):
                            st.exception(e)
                        st.warning("Tente recarregar a página ou verificar os dados de entrada.")
                        
        elif tipo_dashboard == "Desenvolvimento de Pessoas":
            tabs = st.tabs([
                "Visão Geral",
                "Colaborador"
            ])
            
            with tabs[0]:
                try:
                    visao_geral.mostrar_aba(dados, filtros)
                except Exception as e:
                    st.error(f"Erro na aba Visão Geral: {str(e)}")
            
            with tabs[1]:
                try:
                    colaborador.mostrar_aba(dados, filtros)
                except Exception as e:
                    st.error(f"Erro na aba Colaborador: {str(e)}")

    except Exception as e:
        st.error("Erro crítico ao gerar o dashboard")
        with st.expander("Detalhes do erro"):
            st.exception(e)
        st.warning("Por favor, verifique os dados de entrada e tente novamente.")