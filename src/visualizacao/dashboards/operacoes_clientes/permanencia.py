import streamlit as st
import pandas as pd
import plotly.express as px
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

def criar_grafico_permanencia(dados_tempo, meta, grupo='CLIENTE', filtros=None):
    """Cria gráfico de barras empilhadas com tempo de espera e atendimento"""
    # Criar DataFrames separados para espera e atendimento
    df_espera = pd.DataFrame({
        grupo: dados_tempo[grupo],
        'Tempo': dados_tempo['tpesper'],
        'Tipo': 'Tempo de Espera'
    })
    
    df_atend = pd.DataFrame({
        grupo: dados_tempo[grupo],
        'Tempo': dados_tempo['tpatend'],
        'Tipo': 'Tempo de Atendimento'
    })
    
    # Invertendo a ordem da concatenação para que Tempo de Espera venha primeiro
    df_long = pd.concat([df_atend, df_espera], ignore_index=True)
    
    # Adicionar coluna de total
    df_long = df_long.merge(
        dados_tempo[[grupo, 'tempo_permanencia']],
        on=grupo,
        how='left'
    )
    
    # Ordenar por tempo total (menor para maior)
    df_long = df_long.sort_values('tempo_permanencia', ascending=False)
    
    # Formatar período para o título
    periodo = (f"{filtros['periodo2']['inicio'].strftime('%d/%m/%Y')} a "
              f"{filtros['periodo2']['fim'].strftime('%d/%m/%Y')}")
    
    # Criar o gráfico com cores personalizadas e ordem invertida
    fig = px.bar(
        df_long,
        x='Tempo',
        y=grupo,
        color='Tipo',
        barmode='stack',
        orientation='h',
        category_orders={"Tipo": ["Tempo de Espera", "Tempo de Atendimento"]},  # Define ordem explícita
        title=f'Tempo de Permanência por {grupo} ({periodo})',
        labels={
            'Tempo': 'Tempo (minutos)',
            'Tipo': ''  # Remove o label 'Tipo'
        },
        height=max(600, len(dados_tempo) * 45),
        text=[f"{formatar_tempo(x)} min" for x in df_long['Tempo']],
        color_discrete_map={
            'Tempo de Espera': '#1a365d',      # Azul escuro profundo
            'Tempo de Atendimento': '#4dabf7'   # Azul claro vibrante
        }
    )
    
    # Adicionar linha de meta com texto vermelho
    fig.add_vline(
        x=meta,
        line_dash="dash",
        line_color="#ff5757",
        annotation_text=f"Meta: {formatar_tempo(meta)} min",
        annotation_position="top right",
        annotation_font=dict(
            color="#ff5757",  # Texto da meta em vermelho
            size=14
        )
    )
    
    # Adiciona anotações de tempo total com cores baseadas na meta
    for idx, row in dados_tempo.iterrows():
        tempo_total = row['tempo_permanencia']
        perc_acima = ((tempo_total - meta) / meta * 100) if tempo_total > meta else 0
        
        # Define cor do texto com base na meta
        cor_texto = "#ff5757" if tempo_total > meta else "#29b09d"  # Vermelho se acima, verde se abaixo
        
        texto = (f"{formatar_tempo(tempo_total)} min" if perc_acima <= 0 
                else f"{formatar_tempo(tempo_total)} min (+{perc_acima:.1f}%)")
        
        fig.add_annotation(
            x=tempo_total,
            y=row[grupo],
            text=texto,
            showarrow=False,
            xshift=10,
            font=dict(
                size=15,                # Aumentado tamanho da fonte
                color=cor_texto,        # Cor dinâmica baseada na meta
                family='Arial Black'    # Fonte mais destacada
            ),
            xanchor='left',
            yanchor='middle'
        )
    
    # Atualizar layout com cores específicas
    fig.update_layout(
        plot_bgcolor='white',          # Fundo do gráfico branco
        paper_bgcolor='white',         # Fundo do papel branco
        title_font_color='#2c3e50',   # Cor do título em cinza escuro
        font=dict(
            family="Inter, -apple-system, BlinkMacSystemFont, sans-serif",
            color='#2c3e50',          # Cor do texto em cinza escuro
            size=12
        ),
        showlegend=True,
        legend={
            'orientation': 'h',
            'yanchor': 'bottom',
            'y': 1.02,
            'xanchor': 'right',
            'x': 1,
            'bgcolor': 'white',        # Fundo da legenda branco
            'bordercolor': '#e9ecef'   # Borda da legenda em cinza claro
        },
        margin=dict(l=20, r=160, t=80, b=40),
        bargap=0.15,
        bargroupgap=0.1
    )
    
    # Atualizar eixos
    fig.update_xaxes(
        title_font_color='#2c3e50',   # Cor do título do eixo
        tickfont_color='#2c3e50',     # Cor dos números do eixo
        gridcolor='#e9ecef',          # Cor da grade em cinza muito claro
        showline=True,
        linewidth=1,
        linecolor='#e9ecef'
    )
    
    fig.update_yaxes(
        title_font_color='#2c3e50',
        tickfont_color='#2c3e50',
        showgrid=False,
        showline=True,
        linewidth=1,
        linecolor='#e9ecef'
    )
    
    # Atualizar textos das barras
    fig.update_traces(
        opacity=0.9,                # Leve transparência
        marker=dict(
            line=dict(width=1, color='rgba(255,255,255,0.2)')  # Borda sutil
        ),
        textfont=dict(
            color='white',             # Cor do texto dentro das barras
            size=16,                   # Aumentado tamanho da fonte
            family='Arial Black'       # Fonte mais pesada para parecer negrito
        ),
        textposition='inside',
        texttemplate='%{text}'        # Garante que o texto personalizado seja usado
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
        
        fig = criar_grafico_permanencia(tempos, meta, grupo, filtros)  # Adicionado filtros como parâmetro
        st.plotly_chart(fig, use_container_width=True)
        
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