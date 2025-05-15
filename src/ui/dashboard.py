import streamlit as st
from ..core.data_loader import DataLoader
from .components import upload_widget
from datetime import datetime, timedelta

# Alterar importações para usar caminho relativo correto
from ..visualizacao.dashboards.operacoes_clientes.geral import mostrar_aba as mostrar_geral
from ..visualizacao.dashboards.operacoes_clientes.permanencia import mostrar_aba as mostrar_permanencia
from ..visualizacao.dashboards.desenvolvimento_pessoas.colaborador import mostrar_aba as mostrar_colaborador
from ..visualizacao.dashboards.desenvolvimento_pessoas.tempo_atend import mostrar_aba as mostrar_tempo_atend
from ..visualizacao.dashboards.desenvolvimento_pessoas.qtd_atendimento import mostrar_aba as mostrar_qtd_atend
from ..visualizacao.dashboards.desenvolvimento_pessoas.polivalencia import mostrar_aba as mostrar_polivalencia
from ..visualizacao.dashboards.desenvolvimento_pessoas.ociosidade import mostrar_aba as mostrar_ociosidade

def criar_filtros():
    """Cria filtros de data para análise"""
    st.sidebar.title("📊 Filtros de Análise")
    
    # Data final (atual)
    data_fim = datetime.now().date()
    # Data inicial (30 dias atrás)
    data_inicio = data_fim - timedelta(days=30)
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        inicio_p1 = st.date_input("Início P1", value=data_inicio)
        fim_p1 = st.date_input("Fim P1", value=data_fim)
    
    with col2:
        inicio_p2 = st.date_input("Início P2", value=data_inicio)
        fim_p2 = st.date_input("Fim P2", value=data_fim)
    
    return {
        'periodo1': {'inicio': inicio_p1, 'fim': fim_p1},
        'periodo2': {'inicio': inicio_p2, 'fim': fim_p2}
    }

def render_dashboard():
    """Renderiza o dashboard principal"""
    st.title("Dashboard de Atendimento 📊")
    
    files = upload_widget()
    
    with st.spinner("Carregando dados..."):
        try:
            data = DataLoader.load_data(files)
            if data is not None:
                st.success("✅ Dados carregados com sucesso!")
                
                filtros = criar_filtros()
                filtros['meta_permanencia'] = 30
                
                # Seleção do dashboard principal
                tipo_dashboard = st.sidebar.radio(
                    "Selecione o Dashboard:",
                    ["Performance Cliente/Operação", "Desenvolvimento de Pessoas"]
                )
                
                if tipo_dashboard == "Performance Cliente/Operação":
                    render_dashboard_operacoes(data, filtros)
                else:
                    render_dashboard_pessoas(data, filtros)
                    
            else:
                st.error("❌ Falha ao carregar dados. Tente upload manual.")
                
        except Exception as e:
            st.error(f"❌ Erro: {str(e)}")
            if st.session_state.debug:
                st.exception(e)

def render_dashboard_operacoes(data, filtros):
    """Renderiza dashboard de operações/clientes"""
    st.sidebar.markdown("### Filtros de Cliente/Operação")
    
    # Configurar filtros específicos
    clientes = sorted(data['base']['CLIENTE'].dropna().unique())
    operacoes = sorted(data['base']['OPERAÇÃO'].dropna().unique())
    
    filtros.update({
        'cliente': st.sidebar.multiselect("Cliente", ["Todos"] + clientes, default=["Todos"]),
        'operacao': st.sidebar.multiselect("Operação", ["Todas"] + operacoes, default=["Todas"]),
        'turno': st.sidebar.multiselect("Turno", ["Todos", "TURNO A", "TURNO B", "TURNO C"], default=["Todos"])
    })
    
    # Renderizar abas
    tabs = st.tabs(["Visão Geral", "Permanência"])
    renderers = [mostrar_geral, mostrar_permanencia]
    
    for tab, renderer in zip(tabs, renderers):
        with tab:
            try:
                renderer(data, filtros)
            except Exception as e:
                st.error(f"Erro ao renderizar aba: {str(e)}")
                if st.session_state.debug:
                    st.exception(e)

def render_dashboard_pessoas(data, filtros):
    """Renderiza dashboard de desenvolvimento de pessoas"""
    # Renderizar abas
    tabs = st.tabs([
        "Visão Geral", 
        "Colaborador",
        "Tempo de Atendimento",
        "Quantidade",
        "Ociosidade",
        "Polivalência"
    ])
    
    renderers = [
        mostrar_geral,
        mostrar_colaborador,
        mostrar_tempo_atend,
        mostrar_qtd_atend,
        mostrar_ociosidade,
        mostrar_polivalencia
    ]
    
    for tab, renderer in zip(tabs, renderers):
        with tab:
            try:
                renderer(data, filtros)
            except Exception as e:
                st.error(f"Erro ao renderizar aba: {str(e)}")
                if st.session_state.debug:
                    st.exception(e)
