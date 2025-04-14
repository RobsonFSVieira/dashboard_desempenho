import streamlit as st
import pandas as pd
from datetime import datetime

def normalizar_colunas(df):
    """Normaliza os nomes das colunas para garantir consistência"""
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
        'usuario': 'usuário',
        'tpatend': 'tpatend',
        'tpesper': 'tpesper',
        'id_senha_origem': 'id_senha_origem',
        'classificacao': 'classificacao',
        'CLIENTE': 'CLIENTE',
        'OPERAÇÃO': 'OPERAÇÃO'
    }
    
    df.columns = [mapeamento.get(col, col) for col in df.columns]
    return df

def validar_dados(df):
    """Valida os dados conforme as premissas do projeto"""
    try:
        # Convertendo colunas de tempo para datetime
        df['retirada'] = pd.to_datetime(df['retirada'])
        df['inicio'] = pd.to_datetime(df['inicio'])
        df['fim'] = pd.to_datetime(df['fim'])
        
        # Aplicando filtros conforme premissas
        df = df[
            (df['tpatend'] >= 60) &  # Mínimo 1 minuto
            (df['tpatend'] <= 1800) &  # Máximo 30 minutos
            (df['tpesper'] <= 14400) &  # Máximo 4 horas de espera
            (df['status'].isin(['ATENDIDO', 'TRANSFERIDA']))
        ]
        
        return df
    
    except Exception as e:
        st.error(f"Erro na validação dos dados: {str(e)}")
        return None

def validar_colunas(df):
    """Valida e padroniza os nomes das colunas"""
    # Mapeamento de possíveis nomes para nomes padronizados
    mapa_colunas = {
        # Status
        'status_descricao': 'status',
        'status descrição': 'status',
        'Status Descrição': 'status',
        'Status': 'status',
        'STATUS': 'status',
        
        # Guichê
        'guiche': 'guichê',
        'guichê': 'guichê',
        'Guichê': 'guichê',
        'Guiche': 'guichê',
        'GUICHE': 'guichê',
        
        # Usuário
        'usuario': 'usuário',
        'usuário': 'usuário',
        'Usuário': 'usuário',
        'Usuario': 'usuário',
        'USUARIO': 'usuário',
        
        # Datas e Tempos (já estão corretos)
        'retirada': 'retirada',
        'inicio': 'inicio',
        'fim': 'fim',
        'tpatend': 'tpatend',
        'tpesper': 'tpesper'
    }
    
    # Mostrar colunas para debug
    with st.sidebar.expander("Debug"):
        st.write("Colunas no arquivo:", df.columns.tolist())
        st.write("Colunas após merge com códigos serão adicionadas: CLIENTE, OPERAÇÃO")
    
    # Renomear colunas existentes
    for col_atual in df.columns:
        col_lower = col_atual.lower().strip()
        for key, value in mapa_colunas.items():
            if col_lower == key.lower():
                df = df.rename(columns={col_atual: value})
                break
    
    # Verificar colunas obrigatórias da base
    colunas_obrigatorias = [
        'status', 'guichê', 'usuário',
        'retirada', 'inicio', 'fim', 
        'tpatend', 'tpesper', 'prefixo'  # prefixo necessário para merge
    ]
    
    colunas_faltantes = [col for col in colunas_obrigatorias if col not in df.columns]
    
    if colunas_faltantes:
        st.error(f"❌ Colunas não encontradas: {', '.join(colunas_faltantes)}")
        st.write("Por favor, verifique se seu arquivo possui as seguintes colunas:")
        for col in colunas_obrigatorias:
            st.write(f"- {col}")
        raise ValueError("Estrutura do arquivo inválida")
    
    return df

def carregar_dados():
    """Carrega e processa os dados do arquivo Excel"""
    try:
        # Carregar base de dados
        df_base = pd.read_excel('base.xlsx')
        df_base = normalizar_colunas(df_base)
        
        # Converter colunas de data/hora
        for col in ['retirada', 'inicio', 'fim']:
            if col in df_base.columns:
                df_base[col] = pd.to_datetime(df_base[col])
        
        # Calcular tempo de permanência
        if 'fim' in df_base.columns and 'inicio' in df_base.columns:
            df_base['tempo_permanencia'] = (df_base['fim'] - df_base['inicio']).dt.total_seconds()
        
        # Carregar médias (se existir)
        try:
            df_medias = pd.read_excel('medias.xlsx')
        except Exception as e:
            st.warning("Arquivo de médias não encontrado. Algumas funcionalidades podem estar limitadas.")
            df_medias = None
        
        dados = {
            'base': df_base,
            'medias': df_medias
        }
        
        return dados
    
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return None