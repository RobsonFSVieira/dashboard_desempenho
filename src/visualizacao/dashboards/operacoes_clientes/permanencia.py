import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json

def formatar_tempo(minutos):
    """Formata o tempo em minutos para o formato mm:ss"""
    minutos_int = int(minutos)
    segundos = int((minutos - minutos_int) * 60)
    return f"{minutos_int:02d}:{segundos:02d}"

def detectar_tema():
    """Detecta se o tema atual é claro ou escuro"""
    try:
        theme_param = st.query_params.get('theme', None)
        if theme_param:
            return json.loads(theme_param)['base']
        else:
            return st.config.get_option('theme.base')
    except:
        return 'light'

def obter_cores_tema():
    """Retorna as cores baseadas no tema atual"""
    is_dark = detectar_tema() == 'dark'
    return {
        'primaria': '#1a5fb4' if is_dark else '#1864ab',
        'secundaria': '#4dabf7' if is_dark else '#83c9ff',
        'texto': '#ffffff' if is_dark else '#2c3e50',
        'fundo': '#0e1117' if is_dark else '#ffffff',
        'grid': '#2c3e50' if is_dark else '#e9ecef',
        'sucesso': '#2dd4bf' if is_dark else '#29b09d',
        'erro': '#ff6b6b' if is_dark else '#ff5757'
    }

def calcular_permanencia(dados, filtros, grupo='CLIENTE'):
    """Calcula tempo de permanência por cliente/operação"""
    df = dados['base'].copy()  # Create a copy to avoid SettingWithCopyWarning
    
    # Criar coluna TURNO baseado no horário de retirada
    def determinar_turno(hora):
        if 7 <= hora < 15:
            return 'TURNO A'
        elif 15 <= hora < 23:
            return 'TURNO B'
        else:
            return 'TURNO C'
    
    # Adiciona coluna TURNO
    df['TURNO'] = df['retirada'].dt.hour.map(determinar_turno)
    
    # Aplicar filtros de data para período 2 (mais recente)
    mask = (
        (df['retirada'].dt.date >= filtros['periodo2']['inicio']) &
        (df['retirada'].dt.date <= filtros['periodo2']['fim'])
    )
    df_filtrado = df[mask]
    
    # Aplicar filtros de cliente
    if filtros['cliente'] != ['Todos']:
        df_filtrado = df_filtrado[df_filtrado['CLIENTE'].isin(filtros['cliente'])]
    
    # Aplicar filtros de operação
    if filtros['operacao'] != ['Todas']:
        df_filtrado = df_filtrado[df_filtrado['OPERAÇÃO'].isin(filtros['operacao'])]
    
    # Aplicar filtros de turno
    if filtros['turno'] != ['Todos']:
        df_filtrado = df_filtrado[df_filtrado['TURNO'].isin(filtros['turno'])]
    
    # Calcula médias de tempo
    tempos = df_filtrado.groupby(grupo).agg({
        'tpatend': 'mean',
        'tpesper': 'mean',
        'tempo_permanencia': 'mean',
        'id': 'count'
    }).reset_index()
    
    # Converte para minutos
    tempos['tpatend'] = tempos['tpatend'] / 60
    tempos['tpesper'] = tempos['tpesper'] / 60
    tempos['tempo_permanencia'] = tempos['tempo_permanencia'] / 60
    
    # Retornar tanto os tempos agregados quanto o DataFrame filtrado
    return tempos, df_filtrado

def criar_grafico_permanencia(dados_tempo, meta, grupo='CLIENTE'):
    """Cria gráfico de barras empilhadas com tempo de espera e atendimento"""
    cores_tema = obter_cores_tema()
    
    # Ordena por tempo total de permanência (invertido - menores no topo)
    df = dados_tempo.sort_values('tempo_permanencia', ascending=False)
    
    fig = go.Figure()
    
    # Adiciona barra de tempo de espera
    fig.add_trace(
        go.Bar(
            name='Tempo de Espera',
            y=df[grupo],
            x=df['tpesper'],
            orientation='h',
            text=[f"{formatar_tempo(x)} min" for x in df['tpesper']],
            textposition='inside',
            marker_color=cores_tema['secundaria'],
            textfont={'color': '#000000', 'size': 16, 'family': 'Arial Black'},
            opacity=0.85
        )
    )
    
    # Adiciona barra de tempo de atendimento
    fig.add_trace(
        go.Bar(
            name='Tempo de Atendimento',
            y=df[grupo],
            x=df['tpatend'],
            orientation='h',
            text=[f"{formatar_tempo(x)} min" for x in df['tpatend']],
            textposition='inside',
            marker_color=cores_tema['primaria'],
            textfont={'color': '#ffffff', 'size': 16, 'family': 'Arial Black'},
            opacity=0.85
        )
    )
    
    # Adiciona linha de meta para cobrir toda a área do gráfico
    fig.add_shape(
        type="line",
        x0=meta,
        x1=meta,
        y0=-0.5,  # Estende abaixo da primeira barra
        y1=len(df)-0.5,  # Estende acima da última barra
        line=dict(
            color=cores_tema['erro'],
            dash="dash",
            width=2
        ),
        name=f'Meta: {formatar_tempo(meta)} min'
    )
    
    # Adiciona entrada na legenda para a meta
    fig.add_trace(
        go.Scatter(
            name=f'Meta: {formatar_tempo(meta)} min',
            x=[None],
            y=[None],
            mode='lines',
            line=dict(
                color=cores_tema['erro'],
                dash="dash",
                width=2
            ),
            showlegend=True
        )
    )
    
    # Adiciona anotações com o tempo total e percentual acima da meta
    for i, row in df.iterrows():
        tempo_total = row['tempo_permanencia']
        perc_acima = ((tempo_total - meta) / meta * 100) if tempo_total > meta else 0
        
        cor = cores_tema['erro'] if tempo_total > meta else cores_tema['sucesso']
        texto = (f"{formatar_tempo(tempo_total)} min" if perc_acima <= 0 
                else f"{formatar_tempo(tempo_total)} min (+{perc_acima:.1f}%)")
        
        fig.add_annotation(
            x=tempo_total,
            y=row[grupo],
            text=texto,
            showarrow=False,
            xshift=10,
            font=dict(color=cor, size=14),
            xanchor='left',
            yanchor='middle'
        )
    
    # Atualiza layout
    fig.update_layout(
        title={
            'text': f'Tempo de Permanência por {grupo}',
            'font': {'size': 16, 'color': cores_tema['texto']}
        },
        barmode='stack',
        bargap=0.15,
        bargroupgap=0.1,
        height=max(600, len(df) * 45),
        font={'size': 12, 'color': cores_tema['texto']},
        showlegend=True,
        legend={
            'orientation': 'h',
            'yanchor': 'bottom',
            'y': 1.02,
            'xanchor': 'right',
            'x': 1,
            'font': {'color': cores_tema['texto']},
            'traceorder': 'normal',
            'itemsizing': 'constant'
        },
        margin=dict(l=20, r=160, t=80, b=40),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor=cores_tema['fundo']
    )
    
    # Atualiza eixos
    fig.update_xaxes(
        title='Tempo (minutos)',
        title_font={'color': cores_tema['texto']},
        tickfont={'color': cores_tema['texto']},
        gridcolor=cores_tema['grid'],
        showline=True,
        linewidth=1,
        linecolor=cores_tema['grid'],
        zeroline=False
    )
    
    fig.update_yaxes(
        title=grupo,
        title_font={'color': cores_tema['texto']},
        tickfont={'color': cores_tema['texto']},
        gridcolor=cores_tema['grid'],
        showline=True,
        linewidth=1,
        linecolor=cores_tema['grid'],
        zeroline=False
    )
    
    return fig

def mostrar_aba(dados, filtros):
    """Mostra a aba de Permanência"""
    # Formatar período para exibição
    periodo = (f"{filtros['periodo2']['inicio'].strftime('%d/%m/%Y')} a "
              f"{filtros['periodo2']['fim'].strftime('%d/%m/%Y')}")
    
    st.header(f"Análise de Permanência ({periodo})")
    
    with st.expander("ℹ️ Como funciona?"):
        st.markdown("""
        ### Como analisamos o tempo de permanência?

        1. **Composição do Tempo**:
        - **🔵 Tempo de Espera**: Período entre retirada da senha e início do atendimento
        - **🔵 Tempo de Atendimento**: Duração do atendimento em si
        - **⌛ Tempo Total**: Soma dos dois períodos (permanência total)

        2. **Cálculo da Meta**:
        - ▫️ Meta definida: Tempo máximo desejado para permanência
        - ▫️ Linha pontilhada vermelha indica a meta no gráfico
        - ▫️ Percentual acima/abaixo calculado em relação à meta

        3. **Indicadores**:
        - ✅ Verde: Tempo total abaixo ou igual à meta
        - ⚠️ Vermelho: Tempo total acima da meta
        - 📊 Percentual mostra quanto está acima da meta

        4. **Análises Disponíveis**:
        - **Por Cliente**: Agrupamento por cliente
        - **Por Operação**: Agrupamento por tipo de serviço
        - **Composição**: Proporção entre espera e atendimento

        5. **Insights**:
        - 🎯 Clientes/Operações dentro da meta
        - ⚠️ Pontos de atenção (acima da meta)
        - 📈 Distribuição dos tempos
        """)
    
    try:
        st.session_state['tema_atual'] = detectar_tema()
        
        tipo_analise = st.radio(
            "Analisar por:",
            ["Cliente", "Operação"],
            horizontal=True,
            key="radio_permanencia"
        )
        
        grupo = "CLIENTE" if tipo_analise == "Cliente" else "OPERAÇÃO"
        
        # Receber tanto os tempos quanto o DataFrame filtrado
        tempos, df_filtrado = calcular_permanencia(dados, filtros, grupo)
        meta = filtros['meta_permanencia']
        
        fig = criar_grafico_permanencia(tempos, meta, grupo)
        st.plotly_chart(
            fig, 
            use_container_width=True,
            key=f"grafico_permanencia_{grupo}_{st.session_state['tema_atual']}"
        )
        
        st.markdown("---")
        with st.expander("📊 Ver Insights", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Visão Geral")
                media_permanencia = tempos['tempo_permanencia'].mean()
                media_espera = tempos['tpesper'].mean()
                media_atend = tempos['tpatend'].mean()
                
                st.markdown(f"""
                **Tempo Médio Total**: {formatar_tempo(media_permanencia)} min
                
                **Composição:**
                - Espera: {formatar_tempo(media_espera)} min ({(media_espera/media_permanencia)*100:.1f}%)
                - Atendimento: {formatar_tempo(media_atend)} min ({(media_atend/media_permanencia)*100:.1f}%)
                """)

            with col2:
                st.subheader("⚠️ Análise de Meta")
                acima_meta = tempos[tempos['tempo_permanencia'] > meta]
                dentro_meta = tempos[tempos['tempo_permanencia'] <= meta]
                
                perc_dentro = (len(dentro_meta) / len(tempos) * 100)
                
                st.markdown(f"""
                Meta: {formatar_tempo(meta)} min
                
                - {len(dentro_meta)} ({perc_dentro:.1f}%) dentro da meta
                - {len(acima_meta)} ({100-perc_dentro:.1f}%) acima da meta
                """)
            
            # Mover o detalhamento para fora das colunas para ocupar toda largura
            st.markdown("---")
            st.markdown("### 📋 Detalhamento dos Registros Fora da Meta")
            
            # Filtrar registros acima da meta do DataFrame filtrado
            df_base = df_filtrado.copy()
            df_base['tempo_permanencia'] = df_base['tempo_permanencia'] / 60  # Converter para minutos
            df_fora_meta = df_base[df_base['tempo_permanencia'] > meta].copy()
            
            if not df_fora_meta.empty:
                # Formatar colunas de tempo
                for col in ['retirada', 'inicio', 'fim']:
                    if col in df_fora_meta.columns:
                        df_fora_meta[col] = df_fora_meta[col].dt.strftime('%H:%M:%S')
                
                # Formatar tempos para minutos
                df_fora_meta['tpatend'] = df_fora_meta['tpatend'] / 60
                df_fora_meta['tpesper'] = df_fora_meta['tpesper'] / 60
                
                # Exibir tabela com configuração personalizada
                st.dataframe(
                    df_fora_meta[
                        [
                            'id', 'prefixo', 'numero', 'complemento', 'status',
                            'retirada', 'inicio', 'fim', 'guichê', 'usuário',
                            'tpesper', 'tpatend', 'tempo_permanencia'
                        ]
                    ],
                    column_config={
                        'id': st.column_config.NumberColumn('ID', width=70),
                        'prefixo': st.column_config.TextColumn('Prefixo', width=80),
                        'numero': st.column_config.NumberColumn('Número', width=80),
                        'complemento': st.column_config.TextColumn('Complemento', width=100),
                        'status': st.column_config.TextColumn('Status', width=100),
                        'retirada': st.column_config.TextColumn('Retirada', width=100),
                        'inicio': st.column_config.TextColumn('Início', width=100),
                        'fim': st.column_config.TextColumn('Fim', width=100),
                        'guichê': st.column_config.TextColumn('Guichê', width=80),
                        'usuário': st.column_config.TextColumn('Usuário', width=120),
                        'tpesper': st.column_config.NumberColumn(
                            'T. Espera (min)',
                            width=100,
                            format="%.2f"
                        ),
                        'tpatend': st.column_config.NumberColumn(
                            'T. Atend. (min)',
                            width=100,
                            format="%.2f"
                        ),
                        'tempo_permanencia': st.column_config.NumberColumn(
                            'T. Total (min)',
                            width=100,
                            format="%.2f"
                        )
                    },
                    hide_index=True,
                    use_container_width=True
                )
                
                st.markdown(f"Total de {len(df_fora_meta)} registros encontrados acima da meta.")
            else:
                st.info("Não foram encontrados registros acima da meta no período selecionado.")
            
            # Nova seção de alertas
            st.markdown("---")
            st.subheader("🎯 Destaques")
            col1, col2 = st.columns(2)
            
            with col1:
                melhores = dentro_meta.nsmallest(3, 'tempo_permanencia')
                st.markdown("**Melhores Tempos:**")
                for _, row in melhores.iterrows():
                    diff = meta - row['tempo_permanencia']
                    st.markdown(f"""
                    - {row[grupo]}:
                        - Total: {formatar_tempo(row['tempo_permanencia'])} min
                        - :green[{formatar_tempo(diff)} min abaixo da meta]
                        - Espera: {formatar_tempo(row['tpesper'])} min
                        - Atendimento: {formatar_tempo(row['tpatend'])} min
                    """)
            
            with col2:
                piores = acima_meta.nlargest(3, 'tempo_permanencia')
                st.markdown("**Necessitam Atenção:**")
                for _, row in piores.iterrows():
                    diff = row['tempo_permanencia'] - meta
                    st.markdown(f"""
                    - {row[grupo]}:
                        - Total: {formatar_tempo(row['tempo_permanencia'])} min
                        - :red[{formatar_tempo(diff)} min acima da meta]
                        - Espera: {formatar_tempo(row['tpesper'])} min
                        - Atendimento: {formatar_tempo(row['tpatend'])} min
                    """)
    
    except Exception as e:
        st.error("Erro ao gerar a aba de Permanência")
        st.exception(e)