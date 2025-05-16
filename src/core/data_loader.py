import streamlit as st
import pandas as pd
from io import BytesIO
import requests
import time
from src.config import GITHUB_CONFIG, GITHUB_TOKEN, DRIVE_CONFIG

class DataLoader:
    """Classe responsável por carregar os dados"""
    
    @staticmethod
    @st.cache_data(ttl=3600, persist="disk", show_spinner=False)  # Adicionado persist e removido spinner
    def load_data(files=None):
        """Carrega dados de diferentes fontes"""
        # Tentar carregar do Drive primeiro
        dados = DataLoader.load_drive()
        if dados:
            return dados
        
        # Se falhar, tenta GitHub
        dados = DataLoader.load_github()
        if dados:
            return dados
        
        # Por último, tenta arquivos locais
        if files and all(files.values()):
            return DataLoader.load_files(files)
        
        return None

    @staticmethod
    def load_github():
        """Carrega dados do GitHub"""
        # Configurar headers com token se disponível
        headers = {
            'Accept': 'application/vnd.github.v3.raw',
            'User-Agent': 'Python/requests'
        }
        
        if GITHUB_TOKEN:
            headers['Authorization'] = f'Bearer {GITHUB_TOKEN}'
        
        dados = {}
        arquivos = {
            'base': 'dados/base.xlsx',
            'codigo': 'dados/codigo.xlsx', 
            'medias': 'dados/medias_atend.xlsx'
        }
        
        # Primeira tentativa - verificar se o token é válido
        url = f"https://raw.githubusercontent.com/{GITHUB_CONFIG['owner']}/{GITHUB_CONFIG['repo']}/{GITHUB_CONFIG['branch']}/{list(arquivos.values())[0]}"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 401:  # Token inválido
                st.error("❌ Token GitHub inválido")
                return None
            elif response.status_code == 403:  # Rate limit
                st.error("❌ Limite de requisições atingido")
                return None
        except:
            return None

        # Se chegou aqui, o token é válido - carregar todos os arquivos
        for key, path in arquivos.items():
            try:
                url = f"https://raw.githubusercontent.com/{GITHUB_CONFIG['owner']}/{GITHUB_CONFIG['repo']}/{GITHUB_CONFIG['branch']}/{path}"
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    dados[key] = pd.read_excel(BytesIO(response.content))
                else:
                    st.warning(f"⚠️ Erro ao carregar {key}: Status {response.status_code}")
                    return None
            except Exception as e:
                st.warning(f"⚠️ Erro ao carregar {key}: {str(e)}")
                return None

        return dados if len(dados) == 3 else None

    @staticmethod
    def load_drive():
        """Carrega dados do Google Drive"""
        dados = {}
        try:
            for key, file_id in DRIVE_CONFIG['files'].items():
                url = f"https://drive.google.com/uc?export=download&id={file_id}"
                try:
                    if key == 'medias':
                        dados[key] = pd.read_excel(url, sheet_name="DADOS")
                    else:
                        dados[key] = pd.read_excel(url)
                except Exception as e:
                    st.warning(f"⚠️ Erro ao carregar {key}.xlsx do Drive: {str(e)}")
                    return None
                    
            return dados if len(dados) == 3 else None
            
        except Exception as e:
            st.warning(f"⚠️ Erro ao carregar dados do Drive: {str(e)}")
            return None

    @staticmethod
    def load_files(files):
        """Processa arquivos enviados via upload"""
        if not all(files.values()):
            return None
            
        try:
            return {
                'base': pd.read_excel(files['base']),
                'codigo': pd.read_excel(files['codigo']),
                'medias': pd.read_excel(files['medias'], sheet_name="DADOS")
            }
        except Exception as e:
            st.error(f"Erro no processamento: {str(e)}")
            return None

    @staticmethod
    def process_data(dados):
        """Processa os dados carregados"""
        try:
            # Validar dados
            if not isinstance(dados, dict) or not all(k in dados for k in ['base', 'codigo', 'medias']):
                st.error("❌ Formato de dados inválido")
                return None
            
            # Processar base
            df_base = dados['base'].copy()
            
            # Debug info
            if st.session_state.debug:
                st.write("Colunas disponíveis:", df_base.columns.tolist())
            
            # Mapeamento de colunas atual para padronizado
            column_mapping = {
                'status_descricao': 'status',
                'guiche': 'guichê',
                'usuario': 'usuário'
            }
            
            # Renomear colunas
            df_base = df_base.rename(columns=column_mapping)
            
            # Converter datas
            date_columns = ['retirada', 'inicio', 'fim']
            for col in date_columns:
                if col in df_base.columns:
                    df_base[col] = pd.to_datetime(df_base[col], format='mixed', dayfirst=True)
            
            # Aplicar filtros com verificação
            mask = pd.Series(True, index=df_base.index)
            
            if 'tpatend' in df_base.columns:
                mask &= df_base['tpatend'].between(60, 1800)
            
            if 'tpesper' in df_base.columns:
                mask &= df_base['tpesper'] <= 14400
            
            # Aplicar filtro de status usando o nome original da coluna
            if 'status' in df_base.columns:
                status_values = ['ATENDIDO', 'TRANSFERIDA']
                df_base['status'] = df_base['status'].str.upper()
                mask &= df_base['status'].isin(status_values)
            
            df_base = df_base[mask]
            
            # Merge com códigos e limpeza de dados
            if 'prefixo' in df_base.columns:
                df_final = pd.merge(
                    df_base,
                    dados['codigo'][['prefixo', 'CLIENTE', 'OPERAÇÃO']],
                    on='prefixo',
                    how='left'
                )
                
                # Limpar valores nulos e converter para string
                df_final['CLIENTE'] = df_final['CLIENTE'].fillna('NÃO INFORMADO').astype(str)
                df_final['OPERAÇÃO'] = df_final['OPERAÇÃO'].fillna('NÃO INFORMADA').astype(str)
                
                df_final['tempo_permanencia'] = df_final['tpatend'] + df_final['tpesper']
                
                if st.session_state.debug:
                    st.write("Dados processados:", len(df_final), "registros")
                
                return {
                    'base': df_final,
                    'medias': dados['medias'],
                    'codigo': dados['codigo']
                }
            else:
                st.error("❌ Coluna 'prefixo' não encontrada para merge")
                return None
            
        except Exception as e:
            st.error(f"❌ Erro no processamento: {str(e)}")
            if st.session_state.debug:
                st.exception(e)
            return None
