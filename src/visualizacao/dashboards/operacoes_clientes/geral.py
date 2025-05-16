import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

def formatar_tempo(minutos):
    """Formata o tempo de minutos para o formato hh:mm min ou mm:ss min"""
    if pd.isna(minutos):
        return "00:00 min"
    
    if minutos >= 60:
        horas = int(minutos // 60)
        minutos_restantes = int(minutos % 60)
        return f"{horas:02d}:{minutos_restantes:02d} h"
    else:
        minutos_parte = int(minutos)
        segundos_parte = int((minutos - minutos_parte) * 60)
        return f"{minutos_parte:02d}:{segundos_parte:02d} min"

def formatar_card(titulo, conteudo, estilo="default"):
    """Formata um card com título e conteúdo"""
    cores = {
        "default": "#ddd",
        "warning": "#ff4b4b",
    }
    bg_cores = {
        "default": "rgba(255,255,255,0)",
        "warning": "rgba(255,75,75,0.05)",
    }
    
    return f"""
    <div style='border:1px solid {cores[estilo]}; border-radius:5px; padding:15px; margin-bottom:20px; background-color:{bg_cores[estilo]};'>
        <p style='font-size:1.1em; font-weight:bold; margin:0 0 10px 0;'>{titulo}</p>
        {conteudo}
    </div>
    """

def formatar_lista(items, separador="\n"):
    """Formata uma lista de items com separador personalizado"""
    return separador.join(items)

def calcular_metricas_gerais(dados, filtros):
    """Calcula métricas gerais para o período selecionado"""
    df = dados['base']
    
    # Validação inicial dos dados
    if df.empty:
        st.warning("Base de dados está vazia")
        return {
            'total_atendimentos': 0,
            'media_tempo_atendimento': 0,
            'media_tempo_espera': 0,
            'media_permanencia': 0
        }
    
    # Identificar período disponível nos dados - Corrigido para usar o mesmo método de mov_cliente.py
    data_mais_antiga = df['retirada'].dt.date.min()
    data_mais_recente = df['retirada'].dt.date.max()
    
    # Validar se as datas estão dentro do período disponível
    if (filtros['periodo2']['inicio'] < data_mais_antiga or 
        filtros['periodo2']['fim'] > data_mais_recente):
        st.error(f"""
            ⚠️ Período selecionado fora do intervalo disponível!
            
            Período disponível na base de dados:
            • De: {data_mais_antiga.strftime('%d/%m/%Y')}
            • Até: {data_mais_recente.strftime('%d/%m/%Y')}
            
            Período selecionado:
            • De: {filtros['periodo2']['inicio'].strftime('%d/%m/%Y')}
            • Até: {filtros['periodo2']['fim'].strftime('%d/%m/%Y')}
            
            Por favor, selecione datas dentro do período disponível.
        """)
        return {
            'total_atendimentos': 0,
            'media_tempo_atendimento': 0,
            'media_tempo_espera': 0,
            'media_permanencia': 0
        }
    
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
    
    df = df[mask]
    
    if df.empty:
        return go.Figure().add_annotation(
            text="Sem dados disponíveis para o período selecionado",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
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
    
    df = df[mask]
    
    if df.empty:
        return go.Figure().add_annotation(
            text="Sem dados disponíveis para o período selecionado",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
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
    
    df = df[mask]

    # Verificar se há dados após a aplicação dos filtros
    if df.empty:
        st.warning("Não há dados disponíveis para os filtros selecionados.")
        return
    
    # Análise por períodos do dia
    df['hora'] = df['retirada'].dt.hour
    manha = df[df['hora'].between(6, 11)]['id'].count()
    tarde = df[df['hora'].between(12, 17)]['id'].count()
    noite = df[df['hora'].between(18, 23)]['id'].count()
    total = manha + tarde + noite
    
    # Evitar divisão por zero
    total = max(total, 1)
    
    # Análise de eficiência - Permanência
    tempo_meta_permanencia = filtros.get('meta_permanencia', 15) * 60  # em segundos
    atend_dentro_meta_perm = df[df['tempo_permanencia'] <= tempo_meta_permanencia]['id'].count()
    total_atendimentos = len(df)
    taxa_efic_permanencia = (atend_dentro_meta_perm / total_atendimentos * 100) if total_atendimentos > 0 else 0

    # Análise de eficiência - Atendimento por Cliente
    tempos_medios_cliente = df.groupby('CLIENTE')['tpatend'].mean()  # em segundos
    analise_por_cliente = []

    for cliente in df['CLIENTE'].unique():
        df_cliente = df[df['CLIENTE'] == cliente]
        tempo_medio = tempos_medios_cliente[cliente]
        atend_dentro_media = df_cliente[df_cliente['tpatend'] <= tempo_medio]['id'].count()
        total_cliente = len(df_cliente)
        taxa_efic = (atend_dentro_media / total_cliente * 100) if total_cliente > 0 else 0
        
        analise_por_cliente.append({
            'cliente': cliente,
            'media': tempo_medio,
            'dentro_media': atend_dentro_media,
            'total': total_cliente,
            'taxa_efic': taxa_efic
        })

    # Análise de pontos fora da meta
    tempo_meta_segundos = tempo_meta_permanencia
    df['status_meta'] = df['tempo_permanencia'].apply(lambda x: 'Dentro' if x <= tempo_meta_segundos else 'Fora')
    pontos_fora = df[df['status_meta'] == 'Fora']
    
    # Cálculos seguros para percentuais
    total_registros = len(df) or 1  # Evita divisão por zero
    dentro_meta = len(df[df['status_meta'] == 'Dentro'])
    fora_meta = len(pontos_fora)
    perc_dentro = (dentro_meta / total_registros * 100) if total_registros > 0 else 0
    perc_fora = (fora_meta / total_registros * 100) if total_registros > 0 else 0

    # Análises detalhadas com tratamento para DataFrames vazios
    dias_criticos = df[df['status_meta'] == 'Fora'].groupby(df['retirada'].dt.date).size().sort_values(ascending=False)
    clientes_criticos = df[df['status_meta'] == 'Fora'].groupby('CLIENTE').size().sort_values(ascending=False)
    
    # Layout dos cards com verificação de dados
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("📊 Visão Geral do Período")
        st.markdown(formatar_card(
            "Resumo do Período",
            f"""
            📌 Atendimentos totais: {len(df):,}
            ⏱️ Tempo médio total: {formatar_tempo(df['tempo_permanencia'].mean() / 60)}
            📈 Taxa de eficiência: {taxa_efic_permanencia:.1f}%
            """
        ), unsafe_allow_html=True)
        
        st.markdown(formatar_card(
            "⏰ Indicadores de Tempo",
            f"""
            ⏳ Tempo médio de espera: {formatar_tempo(df['tpesper'].mean() / 60)}
            ⚡ Tempo médio de atendimento: {formatar_tempo(df['tpatend'].mean() / 60)}
            🎯 Meta de permanência: {tempo_meta_permanencia // 60}:00 min
            """
        ), unsafe_allow_html=True)

    with col2:
        st.subheader("🎯 Análise de Metas")

        # Card de Permanência (mantém como está)
        st.markdown(formatar_card(
            "Meta de Permanência (15min)",
            f"""
            ✅ Dentro da meta: {atend_dentro_meta_perm:,} ({taxa_efic_permanencia:.1f}%)
            ❌ Fora da meta: {total_atendimentos - atend_dentro_meta_perm:,} ({100-taxa_efic_permanencia:.1f}%)
            """,
            "default"
        ), unsafe_allow_html=True)

        # Calcular média geral de atendimento
        tempo_medio_geral = df['tpatend'].mean()
        atend_dentro_media_geral = df[df['tpatend'] <= tempo_medio_geral]['id'].count()
        taxa_efic_geral = (atend_dentro_media_geral / total_atendimentos * 100) if total_atendimentos > 0 else 0

        # Ordenar clientes por eficiência
        analise_por_cliente.sort(key=lambda x: x['taxa_efic'], reverse=True)

        # Substituir a seção do card de Meta de Atendimento por:
        container_metas = st.container()
        with container_metas:
            # Preparar conteúdo detalhado dos clientes
            detalhes_clientes = []
            for analise in analise_por_cliente:
                detalhes_clientes.append(f"""
                **{analise['cliente']}**:
                • Tempo Médio: {formatar_tempo(analise['media']/60)}
                • Dentro da Média: {analise['dentro_media']:,} ({analise['taxa_efic']:.1f}%)
                • Fora da Média: {analise['total'] - analise['dentro_media']:,} ({100-analise['taxa_efic']:.1f}%)
                • Total: {analise['total']:,} atendimentos
                """)

            # Card consolidado com análise geral e por cliente
            conteudo_card = f"""
            💠 **Análise Geral** (média: {formatar_tempo(tempo_medio_geral/60)})
            ✅ Dentro da média: {atend_dentro_media_geral:,} ({taxa_efic_geral:.1f}%)
            ❌ Fora da média: {total_atendimentos - atend_dentro_media_geral:,} ({100-taxa_efic_geral:.1f}%)
            
            📊 **Análise por Cliente**:
            {"\n".join(detalhes_clientes)}
            """
            
            st.markdown(formatar_card(
                "Meta de Atendimento",
                conteudo_card,
                "default"
            ), unsafe_allow_html=True)

        if not dias_criticos.empty and len(dias_criticos) >= 3:
            st.markdown(formatar_card(
                "Pontos Críticos",
                f"""
                📅 Top 3 Dias:
                • {dias_criticos.head(3).index[0].strftime('%d/%m/%Y')}: {dias_criticos.head(3).values[0]:,} atendimentos
                • {dias_criticos.head(3).index[1].strftime('%d/%m/%Y')}: {dias_criticos.head(3).values[1]:,} atendimentos
                • {dias_criticos.head(3).index[2].strftime('%d/%m/%Y')}: {dias_criticos.head(3).values[2]:,} atendimentos
                """
            ), unsafe_allow_html=True)
        else:
            st.markdown(formatar_card(
                "Pontos Críticos",
                "Não há dados suficientes para análise de dias críticos."
            ), unsafe_allow_html=True)

        # Verificar se há clientes críticos antes de mostrar
        if not clientes_criticos.empty and len(clientes_criticos) >= 3:
            st.markdown(formatar_card(
                "Principais Impactos",
                f"""
                👥 Top 3 Clientes:
                • {clientes_criticos.head(3).index[0]}: {clientes_criticos.head(3).values[0]:,} atendimentos
                • {clientes_criticos.head(3).index[1]}: {clientes_criticos.head(3).values[1]:,} atendimentos
                • {clientes_criticos.head(3).index[2]}: {clientes_criticos.head(3).values[2]:,} atendimentos
                """
            ), unsafe_allow_html=True)
        else:
            st.markdown(formatar_card(
                "Principais Impactos",
                "Não há dados suficientes para análise de clientes críticos."
            ), unsafe_allow_html=True)

    with col3:
        st.subheader("⚠️ Análise de Picos")
        # Análise de picos com verificação de dados
        pico_espera = df.nlargest(3, 'tpesper')[['retirada', 'CLIENTE', 'OPERAÇÃO', 'tpesper']]
        pico_permanencia = df.nlargest(3, 'tempo_permanencia')[['retirada', 'CLIENTE', 'OPERAÇÃO', 'tempo_permanencia']]

        if not pico_espera.empty:
            st.markdown(formatar_card(
                "Maiores Tempos de Espera",
                formatar_lista([
                    f"""
                    📍 {formatar_tempo(row['tpesper']/60)}
                    📅 {row['retirada'].strftime('%d/%m/%Y %H:%M')}
                    👥 {row['CLIENTE']}
                    🔧 {row['OPERAÇÃO']}
                    """
                    for _, row in pico_espera.iterrows()
                ], "\n\n"),
                estilo="warning"
            ), unsafe_allow_html=True)
        else:
            st.markdown(formatar_card(
                "Maiores Tempos de Espera",
                "Não há dados suficientes para análise de tempos de espera.",
                estilo="warning"
            ), unsafe_allow_html=True)

        if not pico_permanencia.empty:
            st.markdown(formatar_card(
                "Maiores Tempos de Permanência",
                formatar_lista([
                    f"""
                    📍 {formatar_tempo(row['tempo_permanencia']/60)}
                    📅 {row['retirada'].strftime('%d/%m/%Y %H:%M')}
                    👥 {row['CLIENTE']}
                    🔧 {row['OPERAÇÃO']}
                    """
                    for _, row in pico_permanencia.iterrows()
                ], "\n\n"),
                estilo="warning"
            ), unsafe_allow_html=True)
        else:
            st.markdown(formatar_card(
                "Maiores Tempos de Permanência",
                "Não há dados suficientes para análise de tempos de permanência.",
                estilo="warning"
            ), unsafe_allow_html=True)

def mostrar_aba(dados, filtros):
    """Mostra a aba Geral com visão consolidada e principais insights"""
    # Formatar período para exibição
    periodo = (f"{filtros['periodo2']['inicio'].strftime('%d/%m/%Y')} a "
              f"{filtros['periodo2']['fim'].strftime('%d/%m/%Y')}")
    
    st.header(f"Visão Geral das Operações ({periodo})")
    
    with st.expander("ℹ️ Como funciona?"):
        st.markdown("""
        ### Como analisamos a operação geral?

        1. **Métricas Principais**:
        - **Total de Atendimentos**: Quantidade de senhas atendidas
        - **Tempo Atendimento**: Duração média do atendimento
        - **Tempo Espera**: Duração média em fila
        - **Tempo Permanência**: Duração total no estabelecimento

        2. **Análise por Período**:
        - 📊 Distribuição diária de atendimentos
        - 📈 Evolução do volume de senhas
        - 📉 Identificação de picos e vales

        3. **Análise por Cliente**:
        - 🔝 Top 10 clientes por volume
        - 📊 Participação percentual
        - 📈 Volume de atendimentos

        4. **Indicadores de Eficiência**:
        - ✅ Atendimentos dentro da meta
        - ⚠️ Pontos críticos
        - 📊 Taxa de eficiência

        5. **Insights Gerados**:
        - 🎯 Horários de pico
        - ⚠️ Pontos de atenção
        - 💡 Recomendações operacionais
        """)
    
    try:
        # Validação inicial dos dados
        if not dados or 'base' not in dados or dados['base'].empty:
            st.warning("Dados não disponíveis ou vazios.")
            return
        
        # Criar cópia dos dados para evitar modificações indesejadas
        df = dados['base'].copy()
        
        # Inicializar máscara como True para todos os registros
        mask = pd.Series(True, index=df.index)
        
        # Aplicar filtros individualmente
        if 'periodo2' in filtros and filtros['periodo2']:
            date_mask = (
                (df['retirada'].dt.date >= filtros['periodo2']['inicio']) &
                (df['retirada'].dt.date <= filtros['periodo2']['fim'])
            )
            mask &= date_mask
        
        if filtros.get('cliente') and filtros['cliente'] != ['Todos']:
            client_mask = df['CLIENTE'].isin(filtros['cliente'])
            mask &= client_mask
        
        if filtros.get('operacao') and filtros['operacao'] != ['Todas']:
            op_mask = df['OPERAÇÃO'].isin(filtros['operacao'])
            mask &= op_mask
        
        if filtros.get('turno') and filtros['turno'] != ['Todos']:
            turno_mask = df['retirada'].dt.hour.apply(
                lambda x: 'A' if 7 <= x < 15 else ('B' if 15 <= x < 23 else 'C')
            ).isin(filtros['turno'])
            mask &= turno_mask
        
        # Aplicar máscara final
        df_filtrado = df[mask].copy()
        
        # Continuar apenas se houver dados
        if df_filtrado.empty:
            st.warning("Não há dados disponíveis para os filtros selecionados.")
            return
            
        # Criar dados filtrados e continuar com o processamento
        dados_filtrados = {'base': df_filtrado}
        
        # Calcular métricas
        metricas = calcular_metricas_gerais(dados_filtrados, filtros)
        
        # Layout das métricas em colunas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total de Atendimentos",
                f"{metricas['total_atendimentos']:,}".replace(',', '.'),
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
            fig_diario = criar_grafico_atendimentos_diarios(dados_filtrados, filtros)
            st.plotly_chart(fig_diario, use_container_width=True)
        
        with col_right:
            fig_clientes = criar_grafico_top_clientes(dados_filtrados, filtros)
            st.plotly_chart(fig_clientes, use_container_width=True)
        
        # Insights
        st.markdown("---")
        st.subheader("📈 Análise Detalhada")
        with st.expander("Ver análise completa", expanded=True):
            gerar_insights_gerais(dados_filtrados, filtros, metricas)
    
    except Exception as e:
        st.error("Erro ao gerar a aba Geral")
        st.exception(e)