import streamlit as st
from datetime import datetime, timedelta
from visualizacao.tema import Tema

def criar_filtros():
    """Cria e gerencia os filtros na sidebar"""
    st.sidebar.header("Filtros de Análise")
    
    # Configuração do formato de data brasileiro
    locale_date = lambda x: x.strftime('%d/%m/%Y')
    
    # Seleção de períodos
    st.sidebar.subheader("Períodos de Análise")
    
    # Período 1 (Comparação)
    col1, col2 = st.sidebar.columns(2)
    with col1:
        data_inicio_p1 = st.date_input(
            "Início P1",
            value=(datetime.now() - timedelta(days=60)).date(),
            help="Data inicial do primeiro período",
            format="DD/MM/YYYY"  # Formato brasileiro
        )
    with col2:
        data_fim_p1 = st.date_input(
            "Fim P1",
            value=(datetime.now() - timedelta(days=31)).date(),
            help="Data final do primeiro período",
            format="DD/MM/YYYY"  # Formato brasileiro
        )
    
    # Período 2 (Base)
    col3, col4 = st.sidebar.columns(2)
    with col3:
        data_inicio_p2 = st.date_input(
            "Início P2",
            value=(datetime.now() - timedelta(days=30)).date(),
            help="Data inicial do segundo período",
            format="DD/MM/YYYY"  # Formato brasileiro
        )
    with col4:
        data_fim_p2 = st.date_input(
            "Fim P2",
            value=datetime.now().date(),
            help="Data final do segundo período",
            format="DD/MM/YYYY"  # Formato brasileiro
        )
    
    # Validação das datas
    if data_fim_p1 < data_inicio_p1 or data_fim_p2 < data_inicio_p2:
        st.sidebar.error("⚠️ Data final deve ser maior que data inicial!")
        return None
    
    # Filtros adicionais
    st.sidebar.subheader("Filtros Adicionais")
    
    # Só mostra os filtros se houver dados carregados
    if st.session_state.dados is not None:
        df = st.session_state.dados['base']
        
        # Cliente
        clientes = ["Todos"] + sorted(df['CLIENTE'].unique().tolist())
        cliente = st.sidebar.multiselect(
            "Cliente",
            options=clientes,
            default="Todos",
            help="Selecione um ou mais clientes"
        )
        
        # Operação
        operacoes = ["Todas"] + sorted(df['OPERAÇÃO'].unique().tolist())
        operacao = st.sidebar.multiselect(
            "Operação",
            options=operacoes,
            default="Todas",
            help="Selecione uma ou mais operações"
        )
        
        # Turno
        turnos = ["Todos", "A", "B", "C"]
        turno = st.sidebar.multiselect(
            "Turno",
            options=turnos,
            default="Todos",
            help="Selecione um ou mais turnos"
        )
        
        # Meta de permanência
        meta_permanencia = st.sidebar.number_input(
            "Meta de Permanência (minutos)",
            min_value=1,
            max_value=60,
            value=15,
            help="Meta de tempo total de permanência (espera + atendimento)"
        )
        
        filtros = {
            'periodo1': {
                'inicio': data_inicio_p1,
                'fim': data_fim_p1
            },
            'periodo2': {
                'inicio': data_inicio_p2,
                'fim': data_fim_p2
            },
            'cliente': cliente,
            'operacao': operacao,
            'turno': turno,
            'meta_permanencia': meta_permanencia
        }
    
    # Adicionar ao final da sidebar
    adicionar_seletor_tema()
    
    return filtros

def adicionar_seletor_tema():
    """Adiciona seletor de tema (claro/escuro) discretamente no final da sidebar"""
    # Cria um separador visual
    st.sidebar.markdown("---")
    
    # Detecta o tema atual
    tema_atual = Tema.detectar_tema_atual()
    tema_index = 0 if tema_atual == 'claro' else 1
    
    # Cria um container com estilo mais discreto
    with st.sidebar.container():
        # Título discreto
        st.markdown("<p style='font-size: 0.85rem; opacity: 0.8;'>Aparência</p>", unsafe_allow_html=True)
        
        # Seletor de tema discreto
        tema_selecionado = st.radio(
            label="Modo",
            options=["Claro", "Escuro"],
            index=tema_index,
            horizontal=True,
            label_visibility="collapsed",
            key="tema_selecionado"
        )
        
        # Aplica o tema com JavaScript se for alterado
        if (tema_selecionado == "Claro" and tema_atual == 'escuro') or \
           (tema_selecionado == "Escuro" and tema_atual == 'claro'):
            
            # Prepara o script JavaScript para alternar o tema
            tema_js = "dark" if tema_selecionado == "Escuro" else "light"
            js = f"""
            <script>
                const setTheme = (theme) => {{
                    window.localStorage.setItem('theme', theme);
                    document.body.classList.remove('light', 'dark');
                    document.body.classList.add(theme);
                    setTimeout(() => {{
                        window.location.reload();
                    }}, 100);
                }};
                setTheme('{tema_js}');
            </script>
            """
            st.components.v1.html(js)