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
        
        # URLs para download direto usando githubusercontent
        base_url = f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/{branch}/dados"
        files = {
            'base': f"{base_url}/base.xlsx",
            'codigo': f"{base_url}/codigo.xlsx",
            'medias': f"{base_url}/medias_atend.xlsx"
        }
        
        headers = {
            'Accept': 'application/vnd.github.v3.raw',
            'User-Agent': 'Mozilla/5.0',  # Add user agent
            'Authorization': f'token {os.getenv("GITHUB_TOKEN")}' if os.getenv("GITHUB_TOKEN") else None
        }
        # Remove None values from headers
        headers = {k: v for k, v in headers.items() if v is not None}
        
        dados = {}
        
        for key, url in files.items():
            try:
                response = requests.get(url, headers=headers, timeout=30)
                if response.status_code == 200:
                    content = response.content
                    if len(content) < 100:
                        raise ValueError(f"Conteúdo do arquivo {key} muito pequeno")
                    
                    content_io = BytesIO(content)
                    
                    try:
                        # Primeira tentativa: leitura básica
                        excel_options = {
                            'engine': 'openpyxl'
                        }
                        
                        if key == 'medias':
                            dados[key] = pd.read_excel(content_io, sheet_name="DADOS", **excel_options)
                        else:
                            dados[key] = pd.read_excel(content_io, **excel_options)
                            
                    except Exception as first_err:
                        try:
                            # Segunda tentativa: usar xlrd como fallback
                            content_io.seek(0)
                            excel_options = {'engine': 'xlrd'}
                            dados[key] = pd.read_excel(content_io, **excel_options)
                            
                        except Exception as second_err:
                            try:
                                # Terceira tentativa: usar opções mais específicas
                                content_io.seek(0)
                                excel_options = {
                                    'engine': 'openpyxl',
                                    'keep_default_na': False,
                                    'na_values': [''],
                                    'skip_blank_lines': True
                                }
                                dados[key] = pd.read_excel(content_io, **excel_options)
                                
                            except Exception as excel_err:
                                st.error(f"""
                                ❌ Erro ao ler arquivo Excel {key}:
                                • Tentativa 1: {str(first_err)}
                                • Tentativa 2: {str(second_err)}
                                • Tentativa 3: {str(excel_err)}
                                • Tamanho: {len(content)} bytes
                                • Content-Type: {response.headers.get('content-type')}
                                """)
                                
                                try:
                                    # Salvar arquivo para debug
                                    debug_path = f"debug_{key}.xlsx"
                                    with open(debug_path, "wb") as f:
                                        f.write(content)
                                    st.info(f"Arquivo problemático salvo em: {debug_path}")
                                except:
                                    pass
                                
                                raise excel_err
                                
                else:
                    st.error(f"""
                    ❌ Erro ao acessar {key}.xlsx (Status: {response.status_code}):
                    • URL: {url}
                    • Headers: {headers}
                    • Resposta: {response.text[:200]}...
                    """)
                    return None
                    
            except requests.RequestException as req_err:
                st.error(f"""
                ❌ Erro de requisição para {key}.xlsx:
                • Tipo: {type(req_err).__name__}
                • Mensagem: {str(req_err)}
                • URL: {url}
                """)
                return None
                
        if len(dados) == 3:
            st.success("✅ Dados carregados com sucesso do GitHub!")
            return dados
        return None
        
    except Exception as e:
        st.error(f"""
        ❌ Erro ao acessar GitHub:
        • Tipo: {type(e).__name__}
        • Mensagem: {str(e)}
        • Stack trace: {st.exception(e)}
        """)
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
                if response.status_code != 200:
                    st.error(f"""
                    ❌ Erro ao carregar {key} do Drive:
                    • Status code: {response.status_code}
                    • File ID: {file_id}
                    • Resposta: {response.text[:200]}...
                    """)
                    return None
                content = BytesIO(response.content)
                if key == 'medias':
                    dados[key] = pd.read_excel(content, sheet_name="DADOS", engine='openpyxl')
                else:
                    dados[key] = pd.read_excel(content, engine='openpyxl')
            except Exception as e:
                st.error(f"""
                ❌ Erro ao processar {key} do Drive:
                • Tipo do erro: {type(e).__name__}
                • Mensagem: {str(e)}
                • File ID: {file_id}
                """)
                return None
        
        if len(dados) == 3:
            st.success("✅ Dados carregados com sucesso do Drive!")
            return dados
        return None
    except Exception as e:
        st.error(f"""
        ❌ Erro no carregamento do Drive:
        • Tipo do erro: {type(e).__name__}
        • Mensagem: {str(e)}
        • Traceback disponível no log
        """)
        return None

def processar_dados(dados):
    """Processa os dados carregados"""
    try:
        df_base = validar_colunas(dados['base'])
        df_base = validar_dados(df_base)
        
        if df_base is not None:
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
        return None
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