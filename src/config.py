import os
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

# Configurações GitHub simplificadas
GITHUB_CONFIG = {
    'owner': 'RobsonFSVieira',
    'repo': 'dashboard_desempenho',
    'branch': 'main',
}

# IDs dos arquivos no Drive (mantidos apenas como fallback)
GOOGLE_DRIVE_IDS = {
    'base': '1YYaTE-zEi-TIL1quQ5VPsZqeZPQzGFNK',
    'codigo': '18QcILseDPRrFMM-I81_ZephiAAJcD1Tf',
    'medias': '17m7LLKLlwksbSyXlRBYKYniNPNL3f_ds'
}

DRIVE_CONFIG = {
    'files': {
        'base': '1-ehU_r7OW5mloHRldWj-Az3yf1LCsC-B',
        'codigo': '1W8ym32etpHhYeqkJcRLjNAbb7tjQPJUr',
        'medias': '1PNAJGVESOh76hh3eaPHIbL6FIeVyiLX9'
    }
}
