def carregar_base_dados(caminho_arquivo):
    """Carrega os dados da base Excel"""
    try:
        # Carregar dados especificando o formato das datas
        df = pd.read_excel(
            caminho_arquivo,
            parse_dates=['retirada', 'inicio', 'fim'],
            date_parser=lambda x: pd.to_datetime(x, format='%Y-%m-%d %H:%M:%S', errors='coerce')
        )
        
        # Verificar se as datas foram carregadas corretamente
        if df['retirada'].isna().all():
            st.error("Erro: As datas não foram reconhecidas corretamente no arquivo")
            return None
            
        # Debug de datas
        st.sidebar.write("Verificação de datas:")
        st.sidebar.write(f"Primeira data: {df['retirada'].min()}")
        st.sidebar.write(f"Última data: {df['retirada'].max()}")
        
        return df
        
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {str(e)}")
        return None
