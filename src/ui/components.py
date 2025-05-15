import streamlit as st

def upload_widget():
    """Widget de upload de arquivos"""
    files = {}
    with st.sidebar.expander("📁 Upload Manual de Arquivos", expanded=True):
        files['base'] = st.file_uploader(
            "Base de Dados (base.xlsx)", 
            type="xlsx",
            key="upload_base"
        )
        files['codigo'] = st.file_uploader(
            "Códigos (codigo.xlsx)", 
            type="xlsx",
            key="upload_codigo"
        )
        files['medias'] = st.file_uploader(
            "Médias (medias_atend.xlsx)", 
            type="xlsx",
            key="upload_medias"
        )
    return files
