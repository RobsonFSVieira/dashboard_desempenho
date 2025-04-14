import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

def calcular_metricas_gerais(dados, filtros):
    """Calcula métricas gerais para o período selecionado"""
    df = dados['base']
    
    # Aplicar filtros de data
    mask = (
        (df['retirada'].dt.date >= filtros['periodo2']['inicio']) &
        (df['retirada'].dt.date <= filtros['periodo2']['fim'])
    )
    
    # Aplicar filtros adicionais
    if filtros['cliente'] != ['Todos']:
        mask &= df['CLIENTE'].isin(filtros['cliente'])
    if filtros['operacao'] != ['Todas']:
        mask &= df['OPERAÇÃO'].isin(filtros['operacao'])
    if filtros['turno'] != ['Todos']:
        mask &= df['retirada'].dt.hour.apply(lambda x: 'A' if 7 <= x < 15 else ('B' if 15 <= x < 23 else 'C')).isin(filtros['turno'])
    
    df_filtrado = df[mask]
    
    # Cálculo das métricas
    total_atendimentos = len(df_filtrado)
    media_tempo_atendimento = df_filtrado['tpatend'].mean() / 60  # em minutos
    media_tempo_espera = df_filtrado['tpesper'].mean() / 60  # em minutos
    media_permanencia = df_filtrado['tempo_permanencia'].mean() / 60  # em minutos
    
    return {
        'total_atendimentos': total_atendimentos,
        'media_tempo_atendimento': media_tempo_atendimento,
        'media_tempo_espera': media_tempo_espera,
        'media_permanencia': media_permanencia
    }

def criar_grafico_atendimentos_diarios(dados, filtros):
    """Cria gráfico de atendimentos diários"""
    df = dados['base']
    
    # Agrupa dados por data
    df_diario = df.groupby(df['retirada'].dt.date).size().reset_index()
    df_diario.columns = ['data', 'quantidade']
    
    # Cria o gráfico
    fig = px.line(
        df_diario, 
        x='data', 
        y='quantidade',
        title='Atendimentos Diários',
        labels={'data': 'Data', 'quantidade': 'Quantidade de Atendimentos'}
    )
    
    return fig

def criar_grafico_top_clientes(dados, filtros):
    """Cria gráfico dos top 10 clientes"""
    df = dados['base']
    
    # Agrupa dados por cliente
    df_clientes = df.groupby('CLIENTE').size().reset_index()
    df_clientes.columns = ['cliente', 'quantidade']
    df_clientes = df_clientes.sort_values('quantidade', ascending=True).tail(10)
    
    # Cria o gráfico
    fig = px.bar(
        df_clientes,
        x='quantidade',
        y='cliente',
        title='Top 10 Clientes',
        orientation='h',
        labels={
            'quantidade': 'Quantidade de Atendimentos',
            'cliente': 'Cliente'
        },
        text='quantidade'  # Adiciona os valores nas barras
    )
    
    # Atualiza o layout para garantir que os rótulos apareçam
    fig.update_layout(
        xaxis_title="Quantidade de Atendimentos",
        yaxis_title="Cliente",
        title_x=0.5,
        margin=dict(l=10, r=120, t=40, b=10),  # Aumenta margem direita para 120
        height=400,  # Define altura fixa
        uniformtext=dict(minsize=10, mode='show')  # Garante visibilidade uniforme do texto
    )
    
    # Atualiza os eixos e o formato do texto
    fig.update_traces(
        textposition='outside',
        textangle=0,  # Mantém o texto horizontal
        cliponaxis=False  # Impede que o texto seja cortado
    )
    fig.update_xaxes(showgrid=True)
    fig.update_yaxes(showgrid=False)
    
    return fig

def gerar_insights_gerais(dados, filtros, metricas):
    """Gera insights sobre as operações gerais"""
    df = dados['base']
    
    # Análise por períodos do dia
    df['hora'] = df['retirada'].dt.hour
    manha = df[df['hora'].between(6, 11)]['id'].count()
    tarde = df[df['hora'].between(12, 17)]['id'].count()
    noite = df[df['hora'].between(18, 23)]['id'].count()
    total = manha + tarde + noite
    
    # Análise de eficiência
    tempo_meta = filtros.get('meta_permanencia', 30)  # 30 minutos como padrão
    atendimentos_eficientes = df[df['tempo_permanencia'] <= tempo_meta * 60]['id'].count()
    taxa_eficiencia = (atendimentos_eficientes / len(df) * 100) if len(df) > 0 else 0
    
    # Análise de pontos fora da meta
    tempo_meta_segundos = tempo_meta * 60  # convertendo para segundos
    df['status_meta'] = df['tempo_permanencia'].apply(lambda x: 'Dentro' if x <= tempo_meta_segundos else 'Fora')
    pontos_fora = df[df['status_meta'] == 'Fora']
    
    # Análise de chegadas em comboio (veículos chegando com menos de 5 minutos de diferença)
    df_sorted = df.sort_values('retirada')
    df_sorted['tempo_entre_chegadas'] = df_sorted['retirada'].diff().dt.total_seconds()
    chegadas_comboio = df_sorted[df_sorted['tempo_entre_chegadas'] <= 300]  # 5 minutos = 300 segundos
    
    # Análise por cliente e operação para chegadas em comboio
    comboio_por_cliente = chegadas_comboio.groupby('CLIENTE').size().sort_values(ascending=False).head(5)
    comboio_por_operacao = chegadas_comboio.groupby('OPERAÇÃO').size().sort_values(ascending=False).head(5)
    
    col1, col2 = st.columns(2)
    
    # CSS personalizado
    st.markdown("""
        <style>
        .metric-card {
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            padding: 15px;
            margin: 10px 0;
            background-color: white;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
        }
        .alert-card {
            border-left: 4px solid #ff4b4b;
            background-color: rgba(255,75,75,0.1);
            padding: 10px;
            margin: 10px 0;
            border-radius: 0 5px 5px 0;
        }
        .warning-card {
            border-left: 4px solid #ffa726;
            background-color: rgba(255,167,38,0.1);
            padding: 10px;
            margin: 10px 0;
            border-radius: 0 5px 5px 0;
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            text-align: center;
        }
        .metric-label {
            font-size: 14px;
            color: #666;
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)

    with col1:
        st.markdown("### 📊 Performance Geral")
        
        # Card de métricas principais
        st.markdown("""
        <div class="metric-card">
            <h4 style='text-align: center;'>🎯 Métricas Principais</h4>
            <div class="metric-value">{:,}</div>
            <div class="metric-label">Total de Atendimentos</div>
            <hr/>
            <div class="metric-value">{:.1f}%</div>
            <div class="metric-label">Taxa de Eficiência</div>
        </div>
        """.format(metricas['total_atendimentos'], taxa_eficiencia), unsafe_allow_html=True)
        
        # Distribuição por turno
        st.markdown("""
        <div class="metric-card">
            <h4 style='text-align: center;'>⏱️ Distribuição por Turno</h4>
            <div style='display: flex; justify-content: space-between;'>
                <div style='text-align: center; flex: 1;'>
                    <div>🌅</div>
                    <div class="metric-value">{:,}</div>
                    <div class="metric-label">Manhã<br/>{:.1f}%</div>
                </div>
                <div style='text-align: center; flex: 1;'>
                    <div>☀️</div>
                    <div class="metric-value">{:,}</div>
                    <div class="metric-label">Tarde<br/>{:.1f}%</div>
                </div>
                <div style='text-align: center; flex: 1;'>
                    <div>🌙</div>
                    <div class="metric-value">{:,}</div>
                    <div class="metric-label">Noite<br/>{:.1f}%</div>
                </div>
            </div>
        </div>
        """.format(
            manha, (manha/total*100),
            tarde, (tarde/total*100),
            noite, (noite/total*100)
        ), unsafe_allow_html=True)

    with col2:
        st.markdown("### 🚨 Pontos de Atenção")
        
        # Card de pontos fora da meta
        st.markdown("""
        <div class="alert-card">
            <h4>⚠️ Pontos Fora da Meta</h4>
            <ul style='list-style-type: none; padding-left: 0;'>
                <li>📊 Quantidade: <b>{:,}</b> ({:.1f}%)</li>
                <li>⏱️ Tempo médio: <b>{:.1f} min</b></li>
            </ul>
        </div>
        """.format(
            len(pontos_fora), 
            len(pontos_fora)/len(df)*100,
            pontos_fora['tempo_permanencia'].mean()/60
        ), unsafe_allow_html=True)
        
        # Card de chegadas em comboio
        st.markdown("""
        <div class="warning-card">
            <h4>🚛 Chegadas em Comboio</h4>
            <ul style='list-style-type: none; padding-left: 0;'>
                <li>📊 Total: <b>{:,}</b> ({:.1f}%)</li>
                <li>🏢 Top 3 Clientes:</li>
                {}
                <li>🔄 Top 3 Operações:</li>
                {}
            </ul>
        </div>
        """.format(
            len(chegadas_comboio),
            len(chegadas_comboio)/len(df)*100,
            ''.join([f"<li style='margin-left:20px'>• {cliente}: {qtd}</li>" for cliente, qtd in comboio_por_cliente.items()[:3]]),
            ''.join([f"<li style='margin-left:20px'>• {op}: {qtd}</li>" for op, qtd in comboio_por_operacao.items()[:3]])
        ), unsafe_allow_html=True)

def mostrar_aba(dados, filtros):
    """Mostra a aba Geral do dashboard"""
    st.header("Visão Geral das Operações")
    
    try:
        # Cálculo das métricas gerais
        metricas = calcular_metricas_gerais(dados, filtros)
        
        # Layout das métricas em colunas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total de Atendimentos",
                f"{metricas['total_atendimentos']:,}",
                help="Número total de atendimentos no período"
            )
        
        with col2:
            st.metric(
                "Tempo Médio de Atendimento",
                f"{metricas['media_tempo_atendimento']:.1f} min",
                help="Tempo médio de atendimento no período"
            )
        
        with col3:
            st.metric(
                "Tempo Médio de Espera",
                f"{metricas['media_tempo_espera']:.1f} min",
                help="Tempo médio de espera em fila no período"
            )
        
        with col4:
            st.metric(
                "Tempo Médio de Permanência",
                f"{metricas['media_permanencia']:.1f} min",
                help="Tempo médio total (espera + atendimento)"
            )
        
        # Gráficos
        col_left, col_right = st.columns(2)
        
        with col_left:
            fig_diario = criar_grafico_atendimentos_diarios(dados, filtros)
            st.plotly_chart(fig_diario, use_container_width=True)
        
        with col_right:
            fig_clientes = criar_grafico_top_clientes(dados, filtros)
            st.plotly_chart(fig_clientes, use_container_width=True)
        
        # Insights
        st.markdown("---")
        st.subheader("📈 Análise Detalhada")
        with st.expander("Ver análise completa", expanded=True):
            gerar_insights_gerais(dados, filtros, metricas)
    
    except Exception as e:
        st.error("Erro ao gerar a aba Geral")
        st.exception(e)