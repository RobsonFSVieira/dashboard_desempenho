import streamlit as st
from visualizacao.dashboards.desenvolvimento_pessoas import visao_geral, colaborador, tempo_atend as dp_tempo_atend

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
            
        elif tipo_dashboard == "Desenvolvimento de Pessoas":
            tabs = st.tabs([
                "Visão Geral",
                "Colaborador",
                "Tempo de Atendimento"
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
            
            with tabs[2]:
                try:
                    dp_tempo_atend.mostrar_aba(dados, filtros)
                except Exception as e:
                    st.error(f"Erro na aba Tempo de Atendimento: {str(e)}")

    except Exception as e:
        st.error("Erro crítico ao gerar o dashboard")
        with st.expander("Detalhes do erro"):
            st.exception(e)
        st.warning("Por favor, verifique os dados de entrada e tente novamente.")