import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

def identificar_ocorrencias(dados, filtros):
    """Identifica ocorrências e desvios dos colaboradores"""
    df = dados['base']
    df_medias = dados['medias']
    
    # Aplicar filtros de data
    mask = (
        (df['retirada'].dt.date >= filtros['periodo2']['inicio']) &
        (df['retirada'].dt.date <= filtros['periodo2']['fim'])
    )
    df_filtrado = df[mask]
    
    # Análise por colaborador e operação
    ocorrencias = []
    
    for usuario in df_filtrado['usuário'].unique():
        dados_usuario = df_filtrado[df_filtrado['usuário'] == usuario]
        
        # 1. Verificar tempos muito acima da média
        for operacao in dados_usuario['OPERAÇÃO'].unique():
            dados_op = dados_usuario[dados_usuario['OPERAÇÃO'] == operacao]
            media_esperada = df_medias[df_medias['OPERAÇÃO'] == operacao]['Total Geral'].values[0]
            
            # Identificar atendimentos muito lentos
            atend_lentos = dados_op[dados_op['tpatend'] > (media_esperada * 2 * 60)]  # Converter para segundos
            
            if len(atend_lentos) > 0:
                ocorrencias.append({
                    'colaborador': usuario,
                    'operacao': operacao,
                    'tipo': 'Atendimento Lento',
                    'quantidade': len(atend_lentos),
                    'media_tempo': atend_lentos['tpatend'].mean() / 60,  # Converter para minutos
                    'data': atend_lentos['inicio'].dt.date.min()
                })
        
        # 2. Verificar intervalos muito longos entre atendimentos
        dados_usuario = dados_usuario.sort_values('inicio')
        dados_usuario['intervalo'] = dados_usuario['inicio'].diff().dt.total_seconds()
        
        intervalos_longos = dados_usuario[dados_usuario['intervalo'] > 3600]  # Mais de 1 hora
        
        if len(intervalos_longos) > 0:
            ocorrencias.append({
                'colaborador': usuario,
                'operacao': 'Todas',
                'tipo': 'Intervalo Longo',
                'quantidade': len(intervalos_longos),
                'media_tempo': intervalos_longos['intervalo'].mean() / 60,
                'data': intervalos_longos['inicio'].dt.date.min()
            })
    
    return pd.DataFrame(ocorrencias)

def criar_grafico_ocorrencias(df_ocorrencias):
    """Cria gráfico de ocorrências por colaborador"""
    # Agrupar ocorrências por colaborador e tipo
    resumo = df_ocorrencias.groupby(['colaborador', 'tipo'])['quantidade'].sum().reset_index()
    
    # Criar gráfico
    fig = px.bar(
        resumo,
        x='colaborador',
        y='quantidade',
        color='tipo',
        title='Ocorrências por Colaborador',
        labels={
            'colaborador': 'Colaborador',
            'quantidade': 'Quantidade de Ocorrências',
            'tipo': 'Tipo de Ocorrência'
        },
        barmode='group'
    )
    
    fig.update_layout(height=500)
    return fig

def mostrar_aba(dados, filtros):
    """Mostra a aba de análise de ocorrências"""
    st.header("Análise de Ocorrências")
    st.write("Identificação de desvios e ocorrências nos atendimentos")
    
    try:
        # Identificar ocorrências
        df_ocorrencias = identificar_ocorrencias(dados, filtros)
        
        if len(df_ocorrencias) > 0:
            # Exibir gráfico
            fig = criar_grafico_ocorrencias(df_ocorrencias)
            st.plotly_chart(fig, use_container_width=True)
            
            # Detalhamento das ocorrências
            st.subheader("📋 Detalhamento das Ocorrências")
            
            # Agrupar por tipo
            for tipo in df_ocorrencias['tipo'].unique():
                with st.expander(f"Ver {tipo}s"):
                    ocorrencias_tipo = df_ocorrencias[df_ocorrencias['tipo'] == tipo]
                    
                    for _, ocorrencia in ocorrencias_tipo.iterrows():
                        st.write(f"**{ocorrencia['colaborador']}** - {ocorrencia['operacao']}")
                        st.write(
                            f"- Quantidade: {int(ocorrencia['quantidade'])} ocorrências\n"
                            f"- Tempo Médio: {ocorrencia['media_tempo']:.1f} min\n"
                            f"- Primeira Ocorrência: {ocorrencia['data'].strftime('%d/%m/%Y')}"
                        )
            
            # Insights
            st.subheader("📊 Insights")
            with st.expander("Ver insights"):
                # Análise por colaborador
                ocorrencias_colab = df_ocorrencias.groupby('colaborador')['quantidade'].sum()
                mais_ocorrencias = ocorrencias_colab.sort_values(ascending=False)
                
                st.write("#### Principais Observações:")
                
                # Top 3 colaboradores com mais ocorrências
                st.write("**Colaboradores com Mais Ocorrências:**")
                for colab, qtd in mais_ocorrencias.head(3).items():
                    st.write(f"- {colab}: {int(qtd)} ocorrências")
                
                # Distribuição por tipo
                dist_tipos = df_ocorrencias.groupby('tipo')['quantidade'].sum()
                st.write("\n**Distribuição por Tipo:**")
                for tipo, qtd in dist_tipos.items():
                    st.write(f"- {tipo}: {int(qtd)} ocorrências")
                
                # Alertas
                if len(df_ocorrencias) > 50:
                    st.warning(
                        "⚠️ Alto número de ocorrências detectado. "
                        "Recomenda-se análise detalhada e ação corretiva."
                    )
        else:
            st.success("✅ Nenhuma ocorrência significativa identificada no período!")
    
    except Exception as e:
        st.error("Erro ao gerar a aba de Análise de Ocorrências")
        st.exception(e)