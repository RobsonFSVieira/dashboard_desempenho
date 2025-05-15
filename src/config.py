import os
from dotenv import load_dotenv
import streamlit as st

# Carregar variáveis de ambiente
load_dotenv()

# Configurações GitHub - prioriza secrets do Streamlit
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"] if "GITHUB_TOKEN" in st.secrets else os.getenv('GITHUB_TOKEN', '')

GITHUB_CONFIG = {
    'owner': 'RobsonFSVieira',
    'repo': 'dashboard_desempenho',
    'branch': 'main',
    'retry_attempts': 5,  # Aumentado número de tentativas
    'retry_delay': 5,     # Aumentado delay entre tentativas
    'timeout': 30        # Timeout em segundos
}

# Ordem de carregamento dos dados (GitHub primeiro)
ORDEM_CARREGAMENTO = ['github', 'drive', 'upload']

# Configurações de debug
DEBUG = True
SHOW_LOAD_DETAILS = True

# Configurações de carregamento de dados
FONTE_DADOS_PREFERIDA = "github"

# IDs dos arquivos no Google Drive
GOOGLE_DRIVE_IDS = {
    'base': '1YYaTE-zEi-TIL1quQ5VPsZqeZPQzGFNK',
    'codigo': '18QcILseDPRrFMM-I81_ZephiAAJcD1Tf',
    'medias': '17m7LLKLlwksbSyXlRBYKYniNPNL3f_ds'
}
