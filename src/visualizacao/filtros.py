import streamlit as st
from datetime import datetime, timedelta
from visualizacao.tema import Tema
import pandas as pd

def obter_datas_disponiveis(df):
    """Obtém as datas mínima e máxima disponíveis no DataFrame"""
    try:
        # Garantir que as datas estão no formato correto
        df['retirada'] = pd.to_datetime(df['retirada'], format='mixed', dayfirst=True)
        
        # Obter data mínima e máxima
        data_min = df['retirada'].dt.date.min()
        data_max = df['retirada'].dt.date.max()
        
        # Garantir que não temos datas futuras
        hoje = datetime.now().date()
        if data_max > hoje:
            data_max = hoje
            
        return data_min, data_max
    except Exception as e:
        st.error("Erro ao processar datas. Verifique o formato da coluna DATA no arquivo.")
        hoje = datetime.now().date()
        return hoje - timedelta(days=60), hoje

def criar_filtros_master():
    """Cria filtros master que afetam todo o dashboard"""
    st.sidebar.title("📊 Filtros Principais")
    
    # Período de análise
    with st.sidebar.expander("📅 Período de Análise", expanded=True):
        # Data final (atual)
        data_fim = datetime.now().date()
        data_inicio = data_fim - timedelta(days=30)
        
        col1, col2 = st.columns(2)
        with col1:
            inicio_p1 = st.date_input("Início P1", value=data_inicio)
            fim_p1 = st.date_input("Fim P1", value=data_fim)
        
        with col2:
            inicio_p2 = st.date_input("Início P2", value=data_inicio)
            fim_p2 = st.date_input("Fim P2", value=data_fim)

    # Filtros globais
    with st.sidebar.expander("🌐 Filtros Globais", expanded=True):
        df = st.session_state.dados['base']
        
        clientes = ["Todos"] + sorted(df['CLIENTE'].dropna().unique().tolist())
        cliente = st.multiselect("Cliente", options=clientes, default=["Todos"])
        
        operacoes = ["Todas"] + sorted(df['OPERAÇÃO'].dropna().unique().tolist())
        operacao = st.multiselect("Operação", options=operacoes, default=["Todas"])
        
        turnos = ["Todos", "TURNO A", "TURNO B", "TURNO C"]
        turno = st.multiselect("Turno", options=turnos, default=["Todos"])
    
    return {
        'periodo1': {'inicio': inicio_p1, 'fim': fim_p1},
        'periodo2': {'inicio': inicio_p2, 'fim': fim_p2},
        'cliente': cliente,
        'operacao': operacao,
        'turno': turno
    }

def criar_filtros_pagina(nome_pagina, dados):
    """Cria filtros específicos para cada página"""
    filtros_pagina = {}
    
    with st.expander("🔍 Filtros da Página", expanded=False):
        if nome_pagina == "polivalencia":
            col1, col2 = st.columns(2)
            with col1:
                filtros_pagina['colaborador'] = st.selectbox(
                    "Colaborador",
                    options=["Todos"] + sorted(dados['base']['usuário'].unique().tolist())
                )
            with col2:
                filtros_pagina['nivel_exp'] = st.selectbox(
                    "Nível de Experiência",
                    options=["Todos", "Junior", "Pleno", "Sênior"]
                )
            filtros_pagina['min_atendimentos'] = st.number_input(
                "Mínimo de Atendimentos",
                min_value=0,
                value=0,
                help="Número mínimo de atendimentos realizados pelo colaborador"
            )
                
        elif nome_pagina == "tempo_atendimento":
            filtros_pagina['faixa_tempo'] = st.slider(
                "Faixa de Tempo (min)",
                min_value=1,
                max_value=60,
                value=(5, 30)
            )
            
        # Adicionar outros casos específicos aqui
    
    return filtros_pagina

def aplicar_filtros(df, filtros_master, filtros_pagina=None):
    """Aplica filtros master e da página aos dados"""
    mask = pd.Series(True, index=df.index)
    
    # Aplicar filtros master primeiro
    if "Todos" not in filtros_master['cliente']:
        mask &= df['CLIENTE'].isin(filtros_master['cliente'])
    
    if "Todas" not in filtros_master['operacao']:
        mask &= df['OPERAÇÃO'].isin(filtros_master['operacao'])
    
    if "Todos" not in filtros_master['turno']:
        mask &= df['turno'].isin(filtros_master['turno'])
    
    # Aplicar filtros da página se existirem
    if filtros_pagina:
        if 'colaborador' in filtros_pagina and filtros_pagina['colaborador'] != "Todos":
            mask &= df['usuário'] == filtros_pagina['colaborador']
            
        if 'faixa_tempo' in filtros_pagina:
            min_tempo, max_tempo = filtros_pagina['faixa_tempo']
            mask &= df['tpatend'].between(min_tempo * 60, max_tempo * 60)
        
        if 'nivel_exp' in filtros_pagina and filtros_pagina['nivel_exp'] != "Todos":
            # Lógica para filtrar por nível de experiência
            if filtros_pagina['nivel_exp'] == "Junior":
                mask &= df['tempo_cargo'] <= 180  # 6 meses
            elif filtros_pagina['nivel_exp'] == "Pleno":
                mask &= (df['tempo_cargo'] > 180) & (df['tempo_cargo'] <= 365)
            elif filtros_pagina['nivel_exp'] == "Sênior":
                mask &= df['tempo_cargo'] > 365
        
        if 'min_atendimentos' in filtros_pagina:
            # Agrupar por usuário para contar atendimentos
            atend_por_usuario = df.groupby('usuário').size()
            usuarios_validos = atend_por_usuario[atend_por_usuario >= filtros_pagina['min_atendimentos']].index
            mask &= df['usuário'].isin(usuarios_validos)
    
    return df[mask]

def criar_filtros():
    """Cria e gerencia os filtros na sidebar"""
    st.sidebar.header("Filtros de Análise")
    
    # Verifica se há dados carregados
    if 'dados' not in st.session_state or st.session_state.dados is None:
        return None
    
    df = st.session_state.dados['base']
    data_min, data_max = obter_datas_disponiveis(df)
    
    # Seção de Períodos em um expander
    with st.sidebar.expander("📅 Períodos de Análise", expanded=True):
        # Mostra o período disponível na base dentro do expander
        st.info(f"📅 Período disponível na base:\nDe {data_min.strftime('%d/%m/%Y')} até {data_max.strftime('%d/%m/%Y')}")
        
        # Ajusta as datas padrão para garantir que estejam dentro do intervalo
        hoje = min(data_max, datetime.now().date())
        um_mes_atras = max(hoje - timedelta(days=30), data_min)
        dois_meses_atras = max(hoje - timedelta(days=60), data_min)
        
        # Período 1 (Comparação)
        col1, col2 = st.columns(2)
        with col1:
            data_inicio_p1 = st.date_input(
                "Início P1",
                value=dois_meses_atras,
                min_value=data_min,
                max_value=data_max,
                help="Data inicial do primeiro período",
                format="DD/MM/YYYY"
            )
        with col2:
            data_fim_p1 = st.date_input(
                "Fim P1",
                value=um_mes_atras,
                min_value=data_min,
                max_value=data_max,
                help="Data final do primeiro período",
                format="DD/MM/YYYY"
            )
        
        # Período 2 (Base)
        col3, col4 = st.columns(2)
        with col3:
            data_inicio_p2 = st.date_input(
                "Início P2",
                value=um_mes_atras,
                min_value=data_min,
                max_value=data_max,
                help="Data inicial do segundo período",
                format="DD/MM/YYYY"
            )
        with col4:
            data_fim_p2 = st.date_input(
                "Fim P2",
                value=hoje,
                min_value=data_min,
                max_value=data_max,
                help="Data final do segundo período",
                format="DD/MM/YYYY"
            )
        
        # Verificar se as datas selecionadas estão dentro do intervalo válido
        periodo_valido = (
            data_inicio_p1 >= data_min and
            data_fim_p1 <= data_max and
            data_inicio_p2 >= data_min and
            data_fim_p2 <= data_max and
            data_fim_p1 >= data_inicio_p1 and
            data_fim_p2 >= data_inicio_p2
        )
        
        if not periodo_valido:
            st.error(f"""
            ⚠️ Período selecionado fora do intervalo disponível!
            
            Período disponível na base de dados:
            • De: {data_min.strftime('%d/%m/%Y')}
            • Até: {data_max.strftime('%d/%m/%Y')}
            """)
            return None

    # Só mostra os filtros se houver dados carregados
    if st.session_state.dados is not None:
        # Filtro de Clientes em um expander
        with st.sidebar.expander("👥 Clientes", expanded=False):
            # Convert all values to strings and handle NaN values
            clientes = ["Todos"] + sorted(df['CLIENTE'].fillna('').astype(str).unique().tolist())
            cliente = st.multiselect(
                "Cliente",
                options=clientes,
                default=["Todos"],
                help="Selecione um ou mais clientes"
            )
        
        # Filtro de Operações em um expander
        with st.sidebar.expander("🔧 Operações", expanded=False):
            operacoes = ["Todas"] + sorted(df['OPERAÇÃO'].fillna('').astype(str).unique().tolist())
            operacao = st.multiselect(
                "Operação",
                options=operacoes,
                default=["Todas"],
                help="Selecione uma ou mais operações"
            )
        
        # Filtro de Turnos em um expander
        with st.sidebar.expander("⏰ Turnos", expanded=False):
            turnos = ["Todos", "TURNO A", "TURNO B", "TURNO C"]
            turno = st.multiselect(
                "Turno",
                options=turnos,
                default=["Todos"],
                help="Selecione um ou mais turnos"
            )
        
        # Meta de permanência em um expander
        with st.sidebar.expander("🎯 Meta", expanded=False):
            meta_permanencia = st.number_input(
                "Meta de Permanência (minutos)",
                min_value=1,
                max_value=60,
                value=15,
                help="Meta de tempo total de permanência (espera + atendimento)"
            )
        
        resultado = {
            'periodo1': {'inicio': data_inicio_p1, 'fim': data_fim_p1},
            'periodo2': {'inicio': data_inicio_p2, 'fim': data_fim_p2},
            'cliente': cliente if 'Todos' not in cliente else ['Todos'],
            'operacao': operacao if 'Todas' not in operacao else ['Todas'],
            'turno': turno if 'Todos' not in turno else ['Todos'],
            'meta_permanencia': meta_permanencia
        }
        
        # Adiciona seletor de tema como último filtro
        adicionar_seletor_tema()
        
        return resultado
    
    return None

def adicionar_seletor_tema():
    """Adiciona um seletor de tema discreto como último filtro na sidebar"""
    # Cria espaço para separar dos outros filtros
    st.sidebar.markdown("---")
    
    # Detecta o tema atual
    tema_atual = Tema.detectar_tema_atual()
    tema_index = 0 if tema_atual == 'claro' else 1
    
    # Título muito discreto
    st.sidebar.markdown(
        "<p style='font-size: 0.8rem; color: rgba(150,150,150,0.7); margin-bottom: 0;'>Tema:</p>",
        unsafe_allow_html=True
    )
    
    # Seletor de tema
    tema_selecionado = st.sidebar.radio(
        "Selecionar tema",
        options=["Claro", "Escuro"],
        index=tema_index,
        label_visibility="collapsed",
        horizontal=True,
        key="tema_seletor"
    )
    
    # Aplica tema se alterado
    if (tema_selecionado == "Claro" and tema_atual == 'escuro') or \
       (tema_selecionado == "Escuro" and tema_atual == 'claro'):
        
        tema_js = "dark" if tema_selecionado == "Escuro" else "light"
        js = f"""
        <script>
            const theme = '{tema_js}';
            localStorage.setItem('theme', theme);
            setTimeout(() => window.location.reload(), 100);
        </script>
        """
        st.components.v1.html(js, height=0)
    
    # Adiciona pequeno espaço vazio após seletor para estética
    st.sidebar.write("")