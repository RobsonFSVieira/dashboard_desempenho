import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
from datetime import datetime

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

def calcular_atendimentos_por_periodo(dados, filtros, periodo):
    """Calcula a quantidade de atendimentos por colaborador no período especificado"""
    df = dados['base']
    
    if df.empty:
        st.warning("Base de dados está vazia")
        return pd.DataFrame()
    
    # Aplicar filtros de data
    mask = (
        (df['retirada'].dt.date >= filtros[periodo]['inicio']) &
        (df['retirada'].dt.date <= filtros[periodo]['fim'])
    )
    df_filtrado = df[mask]
    
    # Aplicar filtros adicionais
    if filtros['cliente'] != ['Todos']:
        df_filtrado = df_filtrado[df_filtrado['CLIENTE'].isin(filtros['cliente'])]
        
    if filtros['operacao'] != ['Todas']:
        df_filtrado = df_filtrado[df_filtrado['OPERAÇÃO'].isin(filtros['operacao'])]
        
    if filtros['turno'] != ['Todos']:
        def get_turno(hour):
            if 7 <= hour < 15:
                return 'TURNO A'
            elif 15 <= hour < 23:
                return 'TURNO B'
            else:
                return 'TURNO C'
        df_filtrado = df_filtrado[df_filtrado['retirada'].dt.hour.apply(get_turno).isin(filtros['turno'])]
    
    # Usar a coluna 'usuário' para identificar o colaborador
    coluna_colaborador = 'usuário'
    
    # Agrupar por colaborador usando a coluna correta
    atendimentos = df_filtrado.groupby(coluna_colaborador)['id'].count().reset_index()
    atendimentos.columns = ['colaborador', 'quantidade']
    
    return atendimentos

def criar_grafico_comparativo(dados_p1, dados_p2, filtros):
    try:
        # Merge dos dados
        df_comp = pd.merge(
            dados_p1, 
            dados_p2, 
            on='colaborador',
            suffixes=('_p1', '_p2'),
            how='outer'
        ).fillna(0)
        
        # Ordena por quantidade do período 2 (decrescente)
        df_comp = df_comp.sort_values('quantidade_p2', ascending=True)
        
        # Calcula variação percentual
        df_comp['variacao'] = ((df_comp['quantidade_p2'] - df_comp['quantidade_p1']) / 
                              df_comp['quantidade_p1'] * 100).replace([float('inf')], 100)
        
        cores_tema = obter_cores_tema()
        
        # Prepara legendas
        legenda_p1 = (f"Período 1 ({filtros['periodo1']['inicio'].strftime('%d/%m/%Y')} "
                      f"a {filtros['periodo1']['fim'].strftime('%d/%m/%Y')})")
        legenda_p2 = (f"Período 2 ({filtros['periodo2']['inicio'].strftime('%d/%m/%Y')} "
                      f"a {filtros['periodo2']['fim'].strftime('%d/%m/%Y')})")
        
        # Cria o gráfico
        fig = go.Figure()
        
        # Adiciona barras para período 1
        fig.add_trace(go.Bar(
            name=legenda_p1,
            y=df_comp['colaborador'],
            x=df_comp['quantidade_p1'],
            orientation='h',
            text=df_comp['quantidade_p1'].astype(int),
            textposition='inside',
            marker_color=cores_tema['primaria'],
            textfont={'color': '#ffffff', 'size': 16},
            opacity=0.85
        ))
        
        # Adiciona barras para período 2
        fig.add_trace(go.Bar(
            name=legenda_p2,
            y=df_comp['colaborador'],
            x=df_comp['quantidade_p2'],
            orientation='h',
            text=df_comp['quantidade_p2'].astype(int),
            textposition='inside',
            marker_color=cores_tema['secundaria'],
            textfont={'color': '#000000', 'size': 16},
            opacity=0.85
        ))
        
        # Adiciona anotações de variação percentual
        df_comp['posicao_total'] = df_comp['quantidade_p1'] + df_comp['quantidade_p2']
        for i, row in df_comp.iterrows():
            cor = cores_tema['sucesso'] if row['variacao'] >= 0 else cores_tema['erro']
            fig.add_annotation(
                y=row['colaborador'],
                x=row['posicao_total'],
                text=f"{row['variacao']:+.1f}%",
                showarrow=False,
                font=dict(color=cor, size=14),
                xanchor='left',
                yanchor='middle',
                xshift=10
            )
        
        # Atualiza layout
        fig.update_layout(
            title={
                'text': 'Comparativo de Quantidade de Atendimentos por Colaborador',
                'font': {'size': 16, 'color': cores_tema['texto']}
            },
            barmode='stack',
            bargap=0.15,
            bargroupgap=0.1,
            height=max(600, len(df_comp) * 45),
            font={'size': 12, 'color': cores_tema['texto']},
            showlegend=True,
            legend={
                'orientation': 'h',
                'yanchor': 'bottom',
                'y': 1.02,
                'xanchor': 'right',
                'x': 1,
                'traceorder': 'normal'  # Define ordem normal para mostrar Período 1 primeiro
            },
            margin=dict(l=20, r=160, t=80, b=40),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor=cores_tema['fundo']
        )
        
        # Atualiza eixos
        fig.update_xaxes(
            title='Quantidade de Atendimentos',
            title_font={'color': cores_tema['texto']},
            tickfont={'color': cores_tema['texto']},
            gridcolor=cores_tema['grid'],
            showline=True,
            linewidth=1,
            linecolor=cores_tema['grid'],
            zeroline=False
        )
        
        fig.update_yaxes(
            title='Colaborador',
            title_font={'color': cores_tema['texto']},
            tickfont={'color': cores_tema['texto']},
            gridcolor=cores_tema['grid'],
            showline=True,
            linewidth=1,
            linecolor=cores_tema['grid'],
            zeroline=False
        )
        
        return fig
    except Exception as e:
        st.error(f"Erro ao criar gráfico: {str(e)}")
        return None

def gerar_insights_atendimentos(atend_p1, atend_p2):
    """Gera insights sobre os atendimentos dos colaboradores"""
    try:
        # Merge dos dados
        df_insights = pd.merge(
            atend_p1, 
            atend_p2, 
            on='colaborador',
            suffixes=('_p1', '_p2'),
            how='outer'
        ).fillna(0)
        
        # Calcula variação percentual
        df_insights['variacao'] = ((df_insights['quantidade_p2'] - df_insights['quantidade_p1']) / 
                                  df_insights['quantidade_p1'] * 100).replace([float('inf')], 100)
        
        # Criar 4 colunas principais
        col_perf1, col_perf2, col_perf3, col_insights = st.columns([0.25, 0.25, 0.25, 0.25])
        
        # Dividir colaboradores em 3 partes
        tamanho_parte = len(df_insights) // 3
        resto = len(df_insights) % 3
        indices = [
            (0, tamanho_parte + (1 if resto > 0 else 0)),
            (tamanho_parte + (1 if resto > 0 else 0), 2*tamanho_parte + (2 if resto > 1 else 1 if resto > 0 else 0)),
            (2*tamanho_parte + (2 if resto > 1 else 1 if resto > 0 else 0), len(df_insights))
        ]

        # Estilo CSS para os boxes
        st.markdown("""
            <style>
                .success-box { 
                    background-color: rgba(0,255,0,0.1);
                    padding: 10px;
                    border-radius: 5px;
                }
                .warning-box { 
                    background-color: rgba(255,0,0,0.1);
                    padding: 10px;
                    border-radius: 5px;
                    margin-top: 10px;
                }
            </style>
        """, unsafe_allow_html=True)

        # Primeira coluna de performance
        with col_perf1:
            st.write("#### Performance (1/3)")
            df_parte = df_insights.iloc[indices[0][0]:indices[0][1]]
            for _, row in df_parte.iterrows():
                status = "✅" if row['variacao'] > 0 else "⚠️"
                st.write(
                    f"**{row['colaborador']}** {status}\n\n"
                    f"- P1: {int(row['quantidade_p1'])}\n"
                    f"- P2: {int(row['quantidade_p2'])}\n"
                    f"- Variação: {row['variacao']:+.1f}%"
                )

        # Segunda coluna de performance
        with col_perf2:
            st.write("#### Performance (2/3)")
            df_parte = df_insights.iloc[indices[1][0]:indices[1][1]]
            for _, row in df_parte.iterrows():
                status = "✅" if row['variacao'] > 0 else "⚠️"
                st.write(
                    f"**{row['colaborador']}** {status}\n\n"
                    f"- P1: {int(row['quantidade_p1'])}\n"
                    f"- P2: {int(row['quantidade_p2'])}\n"
                    f"- Variação: {row['variacao']:+.1f}%"
                )

        # Terceira coluna de performance
        with col_perf3:
            st.write("#### Performance (3/3)")
            df_parte = df_insights.iloc[indices[2][0]:indices[2][1]]
            for _, row in df_parte.iterrows():
                status = "✅" if row['variacao'] > 0 else "⚠️"
                st.write(
                    f"**{row['colaborador']}** {status}\n\n"
                    f"- P1: {int(row['quantidade_p1'])}\n"
                    f"- P2: {int(row['quantidade_p2'])}\n"
                    f"- Variação: {row['variacao']:+.1f}%"
                )

        # Coluna de insights
        with col_insights:
            st.write("#### 📈 Insights")
            
            # Melhor performance
            melhor = df_insights.loc[df_insights['variacao'].idxmax()]
            st.markdown(
                f"<div class='success-box'>"
                f"<b>🎯 Melhor Performance</b><br>"
                f"{melhor['colaborador']}<br>"
                f"Variação: {melhor['variacao']:+.1f}%"
                f"</div>",
                unsafe_allow_html=True
            )
            
            # Oportunidade de melhoria
            pior = df_insights.loc[df_insights['variacao'].idxmin()]
            st.markdown(
                f"<div class='warning-box'>"
                f"<b>⚠️ Oportunidade de Melhoria</b><br>"
                f"{pior['colaborador']}<br>"
                f"Variação: {pior['variacao']:+.1f}%"
                f"</div>",
                unsafe_allow_html=True
            )

    except Exception as e:
        st.error(f"Erro ao gerar insights: {str(e)}")

def mostrar_aba(dados, filtros):
    """Mostra a aba de Quantidade de Atendimento"""
    st.header("Quantidade de Atendimento")
    
    with st.expander("ℹ️ Como funciona?"):
        st.markdown("""
        ### Como analisamos a quantidade de atendimentos?

        1. **Contagem de Atendimentos**:
        - Total de senhas atendidas por colaborador
        - Contabiliza apenas atendimentos finalizados
        - Agrupado por período de análise

        2. **Comparativo entre Períodos**:
        - **Período 1**: Base histórica para comparação
        - **Período 2**: Período atual em análise
        - **Variação**: Diferença percentual entre os períodos
            - 🟢 Variação positiva = Aumento na quantidade (melhor)
            - 🔴 Variação negativa = Redução na quantidade (pior)

        3. **Indicadores de Performance**:
        - ✅ Aumento no número de atendimentos = Maior produtividade
        - ⚠️ Redução no número de atendimentos = Oportunidade de melhoria

        4. **Métricas Importantes**:
        - **Total de Atendimentos**: Quantidade absoluta por colaborador
        - **Variação Percentual**: Evolução em relação ao período anterior
        - **Média por Período**: Base para análise de produtividade

        5. **Insights**:
        - 🎯 Melhor Performance: Maior quantidade ou maior aumento
        - ⚠️ Oportunidade de Melhoria: Menor quantidade ou maior redução
        """)

    try:
        # Adiciona um key único que muda quando o tema muda
        st.session_state['tema_atual'] = detectar_tema()
        
        # Calcula atendimentos para os dois períodos
        atend_p1 = calcular_atendimentos_por_periodo(dados, filtros, 'periodo1')
        atend_p2 = calcular_atendimentos_por_periodo(dados, filtros, 'periodo2')
        
        if atend_p1.empty or atend_p2.empty:
            st.warning("Não há dados para exibir no período selecionado.")
            return
        
        # Cria e exibe o gráfico comparativo
        fig = criar_grafico_comparativo(atend_p1, atend_p2, filtros)
        if fig:
            st.plotly_chart(
                fig, 
                use_container_width=True, 
                key=f"grafico_atendimento_{st.session_state['tema_atual']}"
            )
            
        # Adiciona insights abaixo do gráfico
        st.markdown("---")
        st.subheader("📈 Análise Detalhada")
        with st.expander("Ver análise detalhada", expanded=True):
            gerar_insights_atendimentos(atend_p1, atend_p2)
    
    except Exception as e:
        st.error(f"Erro ao mostrar aba: {str(e)}")
        st.exception(e)
