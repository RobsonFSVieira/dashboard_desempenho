import streamlit as st
import plotly.io as pio
from streamlit.components.v1 import html

class Tema:
    """Classe para gerenciar o tema e estilos do dashboard"""
    
    # Definições de cores para diferentes usos
    CORES = {
        'claro': {
            'primaria': '#0068c9',           # Azul escuro
            'secundaria': '#83c9ff',         # Azul claro
            'terciaria': '#ffaa55',          # Laranja
            'destaque': '#ff5757',           # Vermelho
            'sucesso': '#29b09d',            # Verde-azulado
            'alerta': '#ffcf56',             # Amarelo
            'texto': '#2c3e50',              # Cinza escuro
            'fundo': '#ffffff',              # Branco
            'fundo_secundario': '#f8f9fa',   # Cinza bem claro
            'borda': '#e9ecef'               # Cinza claro
        },
        'escuro': {
            'primaria': '#4dabf7',           # Azul claro
            'secundaria': '#3282b8',         # Azul médio
            'terciaria': '#ff9e4d',          # Laranja
            'destaque': '#ff6b6b',           # Vermelho
            'sucesso': '#2dd4bf',            # Verde-azulado
            'alerta': '#ffd43b',             # Amarelo
            'texto': '#f1f3f5',              # Branco acinzentado
            'fundo': '#1e1e1e',              # Cinza muito escuro
            'fundo_secundario': '#2d2d2d',   # Cinza escuro
            'borda': '#495057'               # Cinza médio
        }
    }

    # Paletas de cores para gráficos
    PALETAS = {
        'claro': {
            'sequencial': ['#0068c9', '#2183d2', '#439edc', '#64b9e5', '#85d4ef', '#a5f0f9'],
            'divergente': ['#0068c9', '#83c9ff', '#ffffff', '#ffaa55', '#ff5757'],
            'categorica': ['#0068c9', '#ff5757', '#29b09d', '#ffaa55', '#83c9ff', '#ffcf56', 
                          '#9d4edd', '#a5e0e7', '#ff7c43', '#3282b8', '#8ac926']
        },
        'escuro': {
            'sequencial': ['#4dabf7', '#569ed6', '#6191b5', '#6c8595', '#777975', '#836d54'],
            'divergente': ['#4dabf7', '#3282b8', '#495057', '#ff9e4d', '#ff6b6b'],
            'categorica': ['#4dabf7', '#ff6b6b', '#2dd4bf', '#ff9e4d', '#3282b8', '#ffd43b', 
                          '#b980f0', '#8ce3d4', '#ff9b85', '#61a8ff', '#a8eb12']
        }
    }
    
    @classmethod
    def aplicar_tema(cls):
        """Configura o tema do dashboard"""
        # Detecta o modo do tema (claro/escuro)
        tema_atual = cls.detectar_tema_atual()
        
        # Configura o tema para Plotly
        cls.configurar_tema_plotly(tema_atual)
        
        # Aplica CSS personalizado
        cls.aplicar_css_personalizado(tema_atual)
        
        return tema_atual
    
    @classmethod
    def detectar_tema_atual(cls):
        """Detecta se o tema atual é claro ou escuro"""
        # Utilizando o localStorage para detectar o tema atual do Streamlit
        script = """
        <script>
        const theme = window.localStorage.getItem('theme') || 'light';
        if (theme === 'dark') {
            document.getElementById('tema-atual').innerHTML = 'escuro';
        } else {
            document.getElementById('tema-atual').innerHTML = 'claro';
        }
        </script>
        <div id="tema-atual" style="display: none;">claro</div>
        """
        
        html(script)
        
        # Por padrão, assumir tema claro
        # (O mecanismo acima funcionará apenas após a primeira renderização)
        return 'claro'
    
    @classmethod
    def configurar_tema_plotly(cls, tema):
        """Configura o tema padrão para gráficos Plotly"""
        cores = cls.CORES[tema]
        
        template = {
            'layout': {
                'font': {'color': cores['texto']},
                'plot_bgcolor': cores['fundo'],
                'paper_bgcolor': cores['fundo'],
                'colorway': cls.PALETAS[tema]['categorica'],
                'colorscale': {
                    'sequential': cls.PALETAS[tema]['sequencial'],
                    'diverging': cls.PALETAS[tema]['divergente']
                },
                'xaxis': {
                    'gridcolor': cores['borda'],
                    'zerolinecolor': cores['borda']
                },
                'yaxis': {
                    'gridcolor': cores['borda'],
                    'zerolinecolor': cores['borda']
                },
                'legend': {
                    'bgcolor': cores['fundo'],
                    'bordercolor': cores['borda']
                },
                'title': {
                    'font': {'color': cores['texto']}
                }
            }
        }
        
        pio.templates['dashboard_tema'] = template
        pio.templates.default = 'plotly+dashboard_tema'
    
    @classmethod
    def aplicar_css_personalizado(cls, tema):
        """Aplica CSS personalizado para aprimorar a aparência do dashboard"""
        cores = cls.CORES[tema]
        
        css = f"""
        <style>
            /* Estilos gerais */
            .stApp {{
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                color: {cores['texto']};
            }}
            
            /* Estilização dos insights */
            .insights-container {{
                padding: 1rem;
                border-radius: 0.5rem;
                background-color: {cores['fundo_secundario'] + '22'};  /* Com transparência */
                border-left: 3px solid {cores['primaria']};
                margin: 1rem 0;
            }}
            
            /* Estilização para métricas */
            .metric-container {{
                background-color: {cores['fundo_secundario']};
                border-radius: 0.5rem;
                padding: 1rem;
                transition: transform 0.3s ease;
                border: 1px solid {cores['borda']};
            }}
            
            .metric-container:hover {{
                transform: translateY(-3px);
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
            }}
            
            /* Botões de ação */
            .stButton > button {{
                background-color: {cores['primaria']};
                color: white;
                border-radius: 0.3rem;
                border: none;
                padding: 0.5rem 1rem;
                transition: all 0.2s ease;
            }}
            
            .stButton > button:hover {{
                background-color: {cores['secundaria']};
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
            }}
            
            /* Cabeçalhos e divisores */
            h1, h2, h3, h4, h5 {{
                color: {cores['texto']};
                font-weight: 600;
                letter-spacing: -0.02em;
            }}
            
            hr {{
                border-color: {cores['borda']};
                margin: 2rem 0;
            }}
            
            /* Estilização da sidebar */
            .css-1d391kg, .css-12oz5g7 {{
                background-color: {cores['fundo_secundario']};
            }}
            
            /* Notificações e alertas */
            .stAlert {{
                border-radius: 0.5rem;
                border-left-width: 5px;
            }}
            
            /* Seletores e filtros */
            .stSelectbox label, .stMultiSelect label, .stDateInput label {{
                font-weight: 500;
                color: {cores['texto']};
            }}
        </style>
        """
        
        st.markdown(css, unsafe_allow_html=True)
    
    @classmethod
    def obter_cores_grafico(cls, num_cores=2, modo='categorico', tema=None):
        """
        Retorna uma lista de cores para uso em gráficos
        
        Args:
            num_cores (int): Número de cores necessárias
            modo (str): Tipo de paleta ('categorico', 'sequencial', 'divergente')
            tema (str): Força um tema específico ('claro' ou 'escuro')
            
        Returns:
            list: Lista de cores no formato adequado para plotly
        """
        if tema is None:
            tema = cls.detectar_tema_atual()
        
        if modo == 'sequencial':
            paleta = cls.PALETAS[tema]['sequencial']
        elif modo == 'divergente':
            paleta = cls.PALETAS[tema]['divergente']
        else:
            paleta = cls.PALETAS[tema]['categorica']
            
        # Assegura que temos cores suficientes repetindo a paleta se necessário
        while len(paleta) < num_cores:
            paleta = paleta + paleta
            
        return paleta[:num_cores]
    
    @classmethod
    def estilizar_tabela(cls, df, tema=None):
        """
        Estiliza um DataFrame para exibição
        
        Args:
            df: DataFrame do pandas
            tema (str): Força um tema específico ('claro' ou 'escuro')
            
        Returns:
            DataFrame estilizado
        """
        if tema is None:
            tema = cls.detectar_tema_atual()
            
        cores = cls.CORES[tema]
        
        # Define o estilo da tabela
        return df.style.set_table_styles([
            {'selector': 'th', 'props': [
                ('background-color', cores['fundo_secundario']),
                ('color', cores['texto']),
                ('font-weight', 'bold'),
                ('border', f"1px solid {cores['borda']}"),
                ('padding', '0.5rem')
            ]},
            {'selector': 'td', 'props': [
                ('border', f"1px solid {cores['borda']}"),
                ('padding', '0.5rem')
            ]},
            {'selector': 'tr:nth-child(even)', 'props': [
                ('background-color', cores['fundo_secundario'] + '40')
            ]}
        ])

    @classmethod
    def configurar_grafico_padrao(cls, fig, titulo=None, tema=None):
        """
        Aplica configurações padrão a um gráfico plotly
        
        Args:
            fig: Figura do plotly
            titulo (str): Título do gráfico
            tema (str): Força um tema específico ('claro' ou 'escuro')
            
        Returns:
            Figura com configurações aplicadas
        """
        if tema is None:
            tema = cls.detectar_tema_atual()
        
        cores = cls.CORES[tema]
        
        # Configurações básicas
        fig.update_layout(
            title=titulo if titulo else None,
            paper_bgcolor=cores['fundo'],
            plot_bgcolor=cores['fundo'],
            font=dict(color=cores['texto']),
            margin=dict(l=40, r=40, t=50, b=40),
            hovermode="closest"
        )
        
        # Configurações dos eixos
        fig.update_xaxes(
            gridcolor=cores['borda'],
            zeroline=True,
            zerolinecolor=cores['borda'],
            showline=True,
            linewidth=1,
            linecolor=cores['borda']
        )
        
        fig.update_yaxes(
            gridcolor=cores['borda'],
            zeroline=True,
            zerolinecolor=cores['borda'],
            showline=True,
            linewidth=1,
            linecolor=cores['borda']
        )
        
        return fig

def inicializar():
    """Inicializa o tema ao importar o módulo"""
    tema_atual = Tema.aplicar_tema()
    return tema_atual
