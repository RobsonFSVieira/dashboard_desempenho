import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from datetime import datetime
import base64
import os

def validar_dados(df):
    """Valida os dados conforme as premissas do projeto"""
    try:
        # Identificar formato da data baseado nos primeiros valores não-nulos
        date_sample = df['retirada'].dropna().iloc[0]
        
        # Converter datas usando formato adequado
        try:
            # Tentar primeiro como datetime
            df['retirada'] = pd.to_datetime(df['retirada'], format='mixed', dayfirst=True)
            df['inicio'] = pd.to_datetime(df['inicio'], format='mixed', dayfirst=True)
            df['fim'] = pd.to_datetime(df['fim'], format='mixed', dayfirst=True)
        except:
            # Se falhar, tentar como string e converter
            df['retirada'] = pd.to_datetime(df['retirada'].astype(str), format='mixed', dayfirst=True)
            df['inicio'] = pd.to_datetime(df['inicio'].astype(str), format='mixed', dayfirst=True)
            df['fim'] = pd.to_datetime(df['fim'].astype(str), format='mixed', dayfirst=True)
        
        # Remover registros com datas futuras
        hoje = pd.Timestamp.now()
        df = df[df['retirada'] <= hoje]
        df = df[df['inicio'] <= hoje]
        df = df[df['fim'] <= hoje]
        
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

def carregar_dados_github():
    """Carrega dados do repositório GitHub"""
    try:
        # Configuração base da API do GitHub
        repo_owner = "RobsonFSVieira"
        repo_name = "dashboard_desempenho"
        branch = "main"
        
        # URLs para download direto (usando a URL correta do GitHub)
        files = {
            'base': f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/{branch}/dados/base.xlsx",
            'codigo': f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/{branch}/dados/codigo.xlsx",
            'medias': f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/{branch}/dados/medias_atend.xlsx"
        }
        
        headers = {
            'Accept': 'application/vnd.github.v3.raw',
            'User-Agent': 'Python/requests'
        }
        
        dados = {}
        
        for key, url in files.items():
            try:
                response = requests.get(url, headers=headers, timeout=30)
                if response.status_code == 200:
                    content = BytesIO(response.content)
                    if key == 'medias':
                        dados[key] = pd.read_excel(content, sheet_name="DADOS", engine='openpyxl')
                    else:
                        dados[key] = pd.read_excel(content, engine='openpyxl')
                else:
                    st.warning(f"⚠️ Arquivo {key}.xlsx não encontrado no GitHub (Status: {response.status_code})")
                    return None
                    
            except Exception as e:
                st.warning(f"⚠️ Erro ao carregar {key}.xlsx: {str(e)}")
                return None
        
        if len(dados) == 3:  # Verificar se todos os arquivos foram carregados
            st.success("✅ Dados carregados com sucesso do GitHub!")
            return dados
        return None
        
    except Exception as e:
        st.warning(f"⚠️ Erro ao acessar GitHub: {str(e)}")
        return None

def carregar_dados_drive():
    """Carrega dados do Google Drive"""
    try:
        # IDs dos arquivos no Google Drive
        files = {
            'base': '1YYaTE-zEi-TIL1quQ5VPsZqeZPQzGFNK',
            'codigo': '18QcILseDPRrFMM-I81_ZephiAAJcD1Tf',
            'medias': '17m7LLKLlwksbSyXlRBYKYniNPNL3f_ds'
        }
        
        dados = {}
        for key, file_id in files.items():
            try:
                url = f'https://drive.google.com/uc?id={file_id}&export=download'
                response = requests.get(url)
                content = BytesIO(response.content)
                if key == 'medias':
                    dados[key] = pd.read_excel(content, sheet_name="DADOS", engine='openpyxl')
                else:
                    dados[key] = pd.read_excel(content, engine='openpyxl')
            except Exception as e:
                st.warning(f"⚠️ Erro ao carregar {key}: {str(e)}")
                return None
        
        if len(dados) == 3:
            st.success("✅ Dados carregados com sucesso do Drive!")
            return dados
        return None
    except Exception as e:
        st.warning(f"⚠️ Erro no carregamento do Drive: {str(e)}")
        return None

def processar_dados(dados):
    """Processa os dados carregados"""
    try:
        df_base = validar_colunas(dados['base'])
        df_base = validar_dados(df_base)
        
        if df_base is None:
            st.error("Falha ao validar dados da base")
            return None
            
        # Garantir que temos dados válidos antes de continuar
        if df_base.empty:
            st.error("Base de dados vazia após validação")
            return None
            
        # Verificar datas mais antiga e mais recente
        data_min = df_base['retirada'].min().date()
        data_max = df_base['retirada'].max().date()
        
        st.info(f"""
        📅 Período disponível na base:
        • De: {data_min.strftime('%d/%m/%Y')}
        • Até: {data_max.strftime('%d/%m/%Y')}
        """)
        
        df_final = pd.merge(
            df_base,
            dados['codigo'][['prefixo', 'CLIENTE', 'OPERAÇÃO']],
            on='prefixo',
            how='left'
        )
        df_final['tempo_permanencia'] = df_final['tpatend'] + df_final['tpesper']
        
        return {
            'base': df_final,
            'medias': dados['medias'],
            'codigo': dados['codigo']
        }
    except Exception as e:
        st.error(f"❌ Erro no processamento: {str(e)}")
        return None

def carregar_dados():
    """Carrega e processa os arquivos necessários"""
    # Verifica se está rodando no Streamlit Cloud
    is_cloud = os.getenv('STREAMLIT_CLOUD', 'false').lower() == 'true'
    
    if is_cloud:
        # Tenta carregar do Drive primeiro
        dados = carregar_dados_drive()
        if dados:
            return processar_dados(dados)
    
    # Se não estiver na nuvem ou falhar, usa interface de upload
    with st.sidebar.expander("📁 Upload Manual de Arquivos", expanded=not is_cloud):
        arquivo_base = st.file_uploader(
            "Base de Dados (base.xlsx)", 
            type="xlsx",
            help="Arquivo com os dados brutos de atendimento"
        )
        
        arquivo_codigo = st.file_uploader(
            "Códigos (codigo.xlsx)", 
            type="xlsx",
            help="Arquivo com os códigos de cliente e operação"
        )
        
        arquivo_medias = st.file_uploader(
            "Médias (medias_atend.xlsx)", 
            type="xlsx",
            help="Arquivo com as médias de atendimento"
        )

        # Se arquivos foram enviados manualmente, usar eles
        if all([arquivo_base, arquivo_codigo, arquivo_medias]):
            with st.spinner('Carregando dados enviados...'):
                try:
                    df_base = pd.read_excel(arquivo_base)
                    df_codigo = pd.read_excel(arquivo_codigo)
                    df_medias = pd.read_excel(arquivo_medias, sheet_name="DADOS")
                    
                    # Validações e processamento
                    df_base = validar_colunas(df_base)
                    df_base = validar_dados(df_base)
                    
                    if df_base is not None:
                        df_final = pd.merge(
                            df_base,
                            df_codigo[['prefixo', 'CLIENTE', 'OPERAÇÃO']],
                            on='prefixo',
                            how='left'
                        )
                        df_final['tempo_permanencia'] = df_final['tpatend'] + df_final['tpesper']
                        
                        return {
                            'base': df_final,
                            'medias': df_medias,
                            'codigo': df_codigo
                        }
                except Exception as e:
                    st.error(f"❌ Erro ao processar arquivos enviados: {str(e)}")
                    return None

        # Se não tem upload manual, tenta carregar do GitHub
        dados_github = carregar_dados_github()
        if dados_github:
            return processar_dados(dados_github)

        return None