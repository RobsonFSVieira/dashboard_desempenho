import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

def formatar_tempo(minutos):
    """Formata o tempo de minutos para o formato mm:ss"""
    minutos_parte = int(minutos)
    segundos_parte = int((minutos - minutos_parte) * 60)
    return f"{minutos_parte:02d}:{segundos_parte:02d} min"

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
    
    # Análise de chegadas em comboio (melhorada)
    TEMPO_COMBOIO = 600  # 10 minutos entre chegadas
    MIN_VEICULOS_COMBOIO = 5  # mínimo de 5 veículos para considerar um comboio
    MAX_TEMPO_JANELA = 1800  # tempo máximo total da janela do comboio (30 minutos)
    MAX_VEICULOS_COMBOIO = 30  # limite máximo de veículos em um comboio
    
    # Adicionar período do dia para análise mais granular
    df_sorted = df.sort_values(['CLIENTE', 'retirada'])
    df_sorted['periodo'] = pd.cut(
        df_sorted['retirada'].dt.hour,
        bins=[-1, 5, 11, 17, 23],
        labels=['madrugada', 'manha', 'tarde', 'noite']
    )
    
    # Preparar grupos por cliente e período
    comboios = []
    for (cliente, periodo), grupo in df_sorted.groupby(['CLIENTE', 'periodo']):
        grupo = grupo.sort_values('retirada')
        current_group = []
        current_start_time = None
        
        for _, row in grupo.iterrows():
            if current_start_time is None:
                current_start_time = row['retirada']
                current_group = [row]
            else:
                time_from_start = (row['retirada'] - current_start_time).total_seconds()
                time_from_last = (row['retirada'] - current_group[-1]['retirada']).total_seconds()
                
                # Condições mais estritas para considerar parte do comboio
                if (time_from_start <= MAX_TEMPO_JANELA and 
                    time_from_last <= TEMPO_COMBOIO and 
                    len(current_group) < MAX_VEICULOS_COMBOIO):
                    current_group.append(row)
                else:
                    # Verificar se o grupo atual é válido antes de adicionar
                    if (len(current_group) >= MIN_VEICULOS_COMBOIO and 
                        (current_group[-1]['retirada'] - current_group[0]['retirada']).total_seconds() <= MAX_TEMPO_JANELA):
                        comboios.append(current_group)
                    current_group = [row]
                    current_start_time = row['retirada']
        
        # Verificar último grupo do período
        if (len(current_group) >= MIN_VEICULOS_COMBOIO and 
            (current_group[-1]['retirada'] - current_group[0]['retirada']).total_seconds() <= MAX_TEMPO_JANELA):
            comboios.append(current_group)
    
    # Análise por cliente e operação para chegadas em comboio
    if comboios:
        # Criar DataFrame com todos os veículos em comboio
        chegadas_comboio = pd.concat([pd.DataFrame(grupo) for grupo in comboios])
        
        # Análise por cliente
        comboio_por_cliente = chegadas_comboio.groupby('CLIENTE').size().sort_values(ascending=False).head(5)
        comboio_por_operacao = chegadas_comboio.groupby('OPERAÇÃO').size().sort_values(ascending=False).head(5)
        
        # Estatísticas dos comboios
        total_veiculos_comboio = len(chegadas_comboio)
        media_veiculos_comboio = sum(len(grupo) for grupo in comboios) / len(comboios)
        max_veiculos_comboio = max(len(grupo) for grupo in comboios)
        total_comboios = len(comboios)
        
        # Análise adicional de distribuição de tamanhos
        tamanhos_comboio = pd.Series([len(grupo) for grupo in comboios])
        mediana_veiculos = tamanhos_comboio.median()
        percentil_75 = tamanhos_comboio.quantile(0.75)
        
        # Análise por período do dia
        chegadas_comboio['periodo'] = pd.cut(
            chegadas_comboio['retirada'].dt.hour,
            bins=[-1, 5, 11, 17, 23],
            labels=['madrugada', 'manha', 'tarde', 'noite']
        )
        distribuicao_periodo = chegadas_comboio['periodo'].value_counts()
    else:
        total_veiculos_comboio = 0
        media_veiculos_comboio = 0
        max_veiculos_comboio = 0
        total_comboios = 0
        mediana_veiculos = 0
        percentil_75 = 0
        comboio_por_cliente = pd.Series()
        comboio_por_operacao = pd.Series()
        distribuicao_periodo = pd.Series()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Visão Geral")
        st.markdown(f"""
        <div style='border:1px solid #ddd; border-radius:5px; padding:15px; margin-bottom:20px;'>
            📌 Total de atendimentos: {metricas['total_atendimentos']:,} atendimentos
            <br>⏱️ Tempo médio total: {formatar_tempo(metricas['media_permanencia'])}
            <br>📈 Taxa de eficiência: {taxa_eficiencia:.1f}%
        </div>
        """, unsafe_allow_html=True)
        
        st.subheader("📈 Indicadores de Tempo")
        st.markdown(f"""
        <div style='border:1px solid #ddd; border-radius:5px; padding:15px; margin-bottom:20px;'>
            ⏳ Tempo médio de espera: {formatar_tempo(metricas['media_tempo_espera'])}
            <br>⚡ Tempo médio de atendimento: {formatar_tempo(metricas['media_tempo_atendimento'])}
            <br>🎯 Meta de permanência: {tempo_meta}:00 min
        </div>
        """, unsafe_allow_html=True)
        
        st.subheader("⏱️ Distribuição Horária")
        st.markdown(f"""
        <div style='border:1px solid #ddd; border-radius:5px; padding:15px; margin-bottom:20px;'>
            🌅 Manhã (6h-11h): {manha:,} atendimentos ({manha/total*100:.1f}%)
            <br>☀️ Tarde (12h-17h): {tarde:,} atendimentos ({tarde/total*100:.1f}%)
            <br>🌙 Noite (18h-23h): {noite:,} atendimentos ({noite/total*100:.1f}%)
        </div>
        """, unsafe_allow_html=True)

        st.subheader("💡 Recomendações")
        
        recommendations = []
        if metricas['media_permanencia'] > tempo_meta:
            recommendations.extend([
                "- ⚠️ Atenção: Tempo médio acima da meta",
                "- 📊 Avaliar gargalos no processo",
                "- 👥 Considerar reforço na equipe"
            ])
        if taxa_eficiencia < 80:
            recommendations.extend([
                "- ⚡ Otimizar fluxo de atendimento",
                "- 📈 Implementar melhorias no processo",
                "- 👥 Revisar distribuição da equipe"
            ])
            
        st.markdown(f"""
        <div style='border:1px solid #2196f3; border-radius:5px; padding:15px; background-color:rgba(33,150,243,0.05);'>
            {('<br>'.join(recommendations) if recommendations else 'Nenhuma recomendação necessária no momento.')}
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.subheader("⚠️ Pontos de Atenção")
        
        meta_insight = f"""
        <div style='border:1px solid #ff4b4b; border-radius:5px; padding:15px; margin-bottom:20px; background-color:rgba(255,75,75,0.05);'>
            <h4 style='color:#ff4b4b; margin:0 0 10px 0;'>🎯 Análise de Meta</h4>
            ❌ Atendimentos fora da meta: {len(pontos_fora):,} atendimentos ({len(pontos_fora)/len(df)*100:.1f}%)
            <br>⏰ Tempo médio dos pontos fora: {formatar_tempo(pontos_fora['tempo_permanencia'].mean()/60)}
        </div>
        """
        st.markdown(meta_insight, unsafe_allow_html=True)

        # Prepare os itens das listas uma única vez
        clientes_html = "".join([f"<li>{cliente} ({qtd:,} atendimentos)</li>" 
                               for cliente, qtd in comboio_por_cliente.items()])
        operacoes_html = "".join([f"<li>{op} ({qtd:,} atendimentos)</li>" 
                                for op, qtd in comboio_por_operacao.items()])
        periodos_html = "".join([
            f"<li>{periodo.title()}: {qtd:,} veículos ({qtd/total_veiculos_comboio*100:.1f}%)</li>"
            for periodo, qtd in distribuicao_periodo.items()
            if qtd > 0
        ]) if not distribuicao_periodo.empty else ""

        comboio_insight = f"""
        <div>
            <h4>Chegadas em Comboio</h4>
            <p>
                Total de comboios detectados: {total_comboios:,}<br>
                Veículos em comboio: {total_veiculos_comboio:,} ({total_veiculos_comboio/len(df)*100:.1f}%)<br>
                Média de veículos por comboio: {media_veiculos_comboio:.1f}<br>
                Mediana de veículos: {mediana_veiculos:.1f}<br>
                75% dos comboios têm até: {percentil_75:.1f} veículos<br>
                Maior comboio detectado: {max_veiculos_comboio:,} veículos
            </p>
            
            <h5>Distribuição por período:</h5>
            <ul>
                {periodos_html}
            </ul>
            
            <h5>Principais clientes afetados:</h5>
            <ul>
                {clientes_html}
            </ul>

            <h5>Operações mais impactadas:</h5>
            <ul>
                {operacoes_html}
            </ul>
        </div>
        """
        st.markdown(comboio_insight, unsafe_allow_html=True)

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
                f"{metricas['total_atendimentos']:,} atendimentos",
                help="Número total de atendimentos no período"
            )
        
        with col2:
            st.metric(
                "Tempo Médio de Atendimento",
                formatar_tempo(metricas['media_tempo_atendimento']),
                help="Tempo médio de atendimento no período"
            )
        
        with col3:
            st.metric(
                "Tempo Médio de Espera",
                formatar_tempo(metricas['media_tempo_espera']),
                help="Tempo médio de espera em fila no período"
            )
        
        with col4:
            st.metric(
                "Tempo Médio de Permanência",
                formatar_tempo(metricas['media_permanencia']),
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