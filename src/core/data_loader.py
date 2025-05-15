import streamlit as st
import pandas as pd
from io import BytesIO
import requests
import time
from src.config import GITHUB_CONFIG, GITHUB_TOKEN

class DataLoader:
    @staticmethod
    @st.cache_data(ttl=3600)
    def load_github():
        """Carrega dados do GitHub"""
        headers = {
            'Accept': 'application/vnd.github.v3.raw',
            'Authorization': f'Bearer {GITHUB_TOKEN}' if GITHUB_TOKEN else None,
            'User-Agent': 'RobsonFSVieira-Dashboard'
        }
        
        dados = {}
        for key, path in {
            'base': 'dados/base.xlsx',
            'codigo': 'dados/codigo.xlsx',
            'medias': 'dados/medias_atend.xlsx'
        }.items():
            for tentativa in range(GITHUB_CONFIG['retry_attempts']):
                try:
                    url = f"https://raw.githubusercontent.com/{GITHUB_CONFIG['owner']}/{GITHUB_CONFIG['repo']}/{GITHUB_CONFIG['branch']}/{path}"
                    
                    if st.session_state.debug:
                        st.write(f"Tentativa {tentativa + 1} de carregar {key}")
                    
                    response = requests.get(
                        url, 
                        headers=headers, 
                        timeout=GITHUB_CONFIG['timeout']
                    )
                    
                    if response.status_code == 200:
                        content = BytesIO(response.content)
                        dados[key] = pd.read_excel(content)
                        break
                    elif response.status_code == 429:  # Rate limit
                        st.warning(f"Limite de requisições atingido. Aguardando {GITHUB_CONFIG['retry_delay']} segundos...")
                        time.sleep(GITHUB_CONFIG['retry_delay'])
                    else:
                        st.error(f"Erro ao carregar {key} (Status: {response.status_code})")
                        if st.session_state.debug:
                            st.write("Headers:", headers)
                            st.write("Response:", response.text)
                        return None
                        
                except Exception as e:
                    st.error(f"Erro ao carregar {key}: {str(e)}")
                    if tentativa == GITHUB_CONFIG['retry_attempts'] - 1:
                        return None
                    time.sleep(GITHUB_CONFIG['retry_delay'])
        
        if len(dados) == 3:
            st.success("✅ Dados carregados com sucesso do GitHub!")
            return dados
        return None

    @staticmethod
    def load_manual(files):
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

    @staticmethod
    def load_data(manual_files=None):
        """Interface principal de carregamento"""
        dados = None
        if manual_files and all(manual_files.values()):
            dados = DataLoader.load_manual(manual_files)
        else:
            dados = DataLoader.load_github()
            
        if dados:
            return DataLoader.process_data(dados)
        return None
