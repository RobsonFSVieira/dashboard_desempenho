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
