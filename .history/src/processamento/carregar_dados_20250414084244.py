import streamlit as st
import pandas as pd
from datetime import datetime

def normalizar_colunas(df):
    """Normaliza os nomes das colunas para manter consistência"""
    mapeamento = {
        'id': 'id',
        'prefixo': 'prefixo', 
        'numero': 'numero',
        'complemento': 'complemento',
        'status_descricao': 'status_descricao',
        'retirada': 'retirada',
        'inicio': 'inicio',
        'fim': 'fim',
        'guiche': 'guiche',
        'usuario': 'usuário',  # Normaliza para padrão com acento
        'tpatend': 'tpatend',
        'tpesper': 'tpesper',
        'id_senha_origem': 'id_senha_origem',
        'classificacao': 'classificacao',
        'CLIENTE': 'CLIENTE',
        'OPERAÇÃO': 'OPERAÇÃO'
    }
    
    df.columns = [mapeamento.get(col.lower(), col) for col in df.columns]
    return df

def verificar_colunas_obrigatorias(df):
    """Verifica se todas as colunas obrigatórias estão presentes"""
    colunas_obrigatorias = [
        'id', 'retirada', 'inicio', 'fim', 'usuario', 
        'tpatend', 'tpesper'
    ]
    
    colunas_faltantes = [col for col in colunas_obrigatorias if col not in df.columns]
    if colunas_faltantes:
        raise ValueError(f"Colunas obrigatórias faltando: {', '.join(colunas_faltantes)}")
    
    return True

def carregar_dados():
    """Carrega e processa os dados do arquivo Excel"""
    st.sidebar.header("Upload de Arquivos")
    
    # Upload dos arquivos
    arquivo_base = st.sidebar.file_uploader(
        "Base de Dados (base.xlsx)", 
        type="xlsx",
        help="Arquivo com os dados brutos de atendimento"
    )
    
    arquivo_medias = st.sidebar.file_uploader(
        "Médias (medias_atend.xlsx)", 
        type="xlsx",
        help="Arquivo com as médias de atendimento"
    )
    
    if arquivo_base:
        try:
            with st.spinner('Carregando dados...'):
                # Carrega os arquivos
                df_base = pd.read_excel(arquivo_base)
                
                # Normalizar nomes das colunas
                df_base = normalizar_colunas(df_base)
                
                # Verificar colunas obrigatórias
                verificar_colunas_obrigatorias(df_base)
                
                # Converter colunas de data/hora
                for col in ['retirada', 'inicio', 'fim']:
                    df_base[col] = pd.to_datetime(df_base[col], errors='coerce')
                
                # Calcular tempo de permanência
                df_base['tempo_permanencia'] = (df_base['fim'] - df_base['inicio']).dt.total_seconds()
                
                # Carregar arquivo de médias se existir
                df_medias = None
                if arquivo_medias:
                    try:
                        df_medias = pd.read_excel(arquivo_medias)
                        df_medias = normalizar_colunas(df_medias)
                    except Exception as e:
                        st.warning("Arquivo de médias não encontrado. Algumas funcionalidades podem estar limitadas.")
                
                st.sidebar.success("✅ Dados carregados com sucesso!")
                
                return {
                    'base': df_base,
                    'medias': df_medias
                }
                
        except Exception as e:
            st.sidebar.error(f"❌ Erro ao carregar arquivos: {str(e)}")
            if 'colunas obrigatórias' in str(e):
                st.info("Verifique se o arquivo base.xlsx contém todas as colunas necessárias.")
            return None
    
    return None