import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
from datetime import datetime, timedelta

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

def formatar_tempo(segundos):
    """Formata o tempo em segundos para o formato HH:MM:SS"""
    horas = int(segundos // 3600)
    minutos = int((segundos % 3600) // 60)
    segs = int(segundos % 60)
    return f"{horas:02d}:{minutos:02d}:{segs:02d} min"

def calcular_ociosidade_por_periodo(dados, filtros, periodo, adicional_filters=None):adicional_filters=None):
    """Calcula o tempo de ociosidade por colaborador no período especificado"""
    df = dados['base'].copy()
    
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
    # Aplicar filtros adicionais
    if filtros['cliente'] != ['Todos']:= "Todos":
        df_filtrado = df_filtrado[df_filtrado['CLIENTE'].isin(filtros['cliente'])]
            df['turno'] = df['retirada'].dt.hour.map(
    if filtros['operacao'] != ['Todas']: <= x < 14 else ('TURNO B' if 14 <= x < 22 else 'TURNO C')
        df_filtrado = df_filtrado[df_filtrado['OPERAÇÃO'].isin(filtros['operacao'])]
            mask &= (df['turno'] == adicional_filters['turno'])
    if filtros['turno'] != ['Todos']:
        def get_turno(hour):['cliente'] != "Todos":
            if 7 <= hour < 15:TE'] == adicional_filters['cliente'])
                return 'TURNO A'
            elif 15 <= hour < 23:a_especifica']:
                return 'TURNO B'a'].dt.date == adicional_filters['data_especifica'])
            else:
                return 'TURNO C'laborador'] != "Todos":
        df_filtrado = df_filtrado[df_filtrado['retirada'].dt.hour.apply(get_turno).isin(filtros['turno'])]
    
    # Aplicar filtros adicionais fornecidos
    if adicional_filters:
        if adicional_filters['colaborador'] != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['usuário'] == adicional_filters['colaborador']] != ['Todos']:
        if adicional_filters['turno'] != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['retirada'].dt.hour.apply(get_turno) == adicional_filters['turno']]
        if adicional_filters['cliente'] != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['CLIENTE'] == adicional_filters['cliente']].isin(filtros['operacao'])]
        if adicional_filters['data_especifica']:
            df_filtrado = df_filtrado[df_filtrado['retirada'].dt.date == adicional_filters['data_especifica']]os['turno'] != ['Todos']:
    
    # Calcular ociosidade por colaborador
    ociosidade = []
    for usuario in df_filtrado['usuário'].unique(): 15 <= hour < 23:
        # Agrupar por dia
        for data in df_filtrado[df_filtrado['usuário'] == usuario]['retirada'].dt.date.unique():
            atend_dia = df_filtrado[return 'TURNO C'
                (df_filtrado['usuário'] == usuario) & 'retirada'].dt.hour.apply(get_turno).isin(filtros['turno'])]
                (df_filtrado['retirada'].dt.date == data)
            ].copy()
            
            if len(atend_dia) > 0:
                # Ordenar por horário
                atend_dia = atend_dia.sort_values('inicio')usuário'] == usuario]['retirada'].dt.date.unique():
                
                # Calcular intervalos entre atendimentos(df_filtrado['usuário'] == usuario) & 
                intervalos = []retirada'].dt.date == data)
                
                # Intervalo entre atendimentos
                for i in range(len(atend_dia)-1):
                    fim_atual = atend_dia['fim'].iloc[i]denar por horário
                    inicio_prox = atend_dia['inicio'].iloc[i+1]'inicio')
                    intervalo = (inicio_prox - fim_atual).total_seconds()
                    # Considerar apenas intervalos menores que 2 horas (7200 segundos)ndimentos
                    if 0 < intervalo <= 7200:
                        intervalos.append(intervalo)
                
                if intervalos:in range(len(atend_dia)-1):
                    # Remover o maior intervalo (presumivelmente almoço)                fim_atual = atend_dia['fim'].iloc[i]
                    if len(intervalos) > 1:icio'].iloc[i+1]
                        intervalos.remove(max(intervalos))  intervalo = (inicio_prox - fim_atual).total_seconds()
                    os menores que 2 horas (7200 segundos)
                    tempo_ocioso = sum(intervalos)
                    ociosidade.append({rvalos.append(intervalo)
                        'colaborador': usuario,            
                        'data': data,alos:
                        'tempo_ocioso': tempo_ocioso,                    # Remover o maior intervalo (presumivelmente almoço)
                        'qtd_intervalos': len(intervalos)
                    })
                
    # Criar DataFrame com média por colaborador_ocioso = sum(intervalos)
    if ociosidade:ade.append({
        df_ociosidade = pd.DataFrame(ociosidade)  'colaborador': usuario,
        df_ociosidade = df_ociosidade.groupby('colaborador')['tempo_ocioso'].mean().reset_index()  'data': data,
        return df_ociosidadeo_ocioso': tempo_ocioso,
    los': len(intervalos)
    return pd.DataFrame()

def criar_grafico_comparativo(dados_p1, dados_p2, filtros):iar DataFrame com média por colaborador
    """Cria gráfico comparativo de ociosidade entre períodos"""
    try:
        # Merge dos dadosdf_ociosidade = df_ociosidade.groupby('colaborador')['tempo_ocioso'].mean().reset_index()
        df_comp = pd.merge(
            dados_p1, 
            dados_p2, 
            on='colaborador',
            suffixes=('_p1', '_p2'), dados_p2, filtros):
            how='outer'ria gráfico comparativo de ociosidade entre períodos"""
        ).fillna(0)
        
        # Ordena por tempo de ociosidade do período 2 (crescente - menores tempos no topo)
        df_comp = df_comp.sort_values('tempo_ocioso_p2', ascending=False)
        
        # Calcula variação percentual    on='colaborador',
        df_comp['variacao'] = ((df_comp['tempo_ocioso_p2'] - df_comp['tempo_ocioso_p1']) / p1', '_p2'),
                              df_comp['tempo_ocioso_p1'] * 100).replace([float('inf')], 100)
        ).fillna(0)
        cores_tema = obter_cores_tema()
         ociosidade do período 2 (crescente - menores tempos no topo)
        # Prepara legendasrt_values('tempo_ocioso_p2', ascending=False)
        legenda_p1 = (f"Período 1 ({filtros['periodo1']['inicio'].strftime('%d/%m/%Y')} "
                      f"a {filtros['periodo1']['fim'].strftime('%d/%m/%Y')})")
        legenda_p2 = (f"Período 2 ({filtros['periodo2']['inicio'].strftime('%d/%m/%Y')} "= ((df_comp['tempo_ocioso_p2'] - df_comp['tempo_ocioso_p1']) / 
                      f"a {filtros['periodo2']['fim'].strftime('%d/%m/%Y')})")float('inf')], 100)
        
        # Cria o gráfico
        fig = go.Figure()
        as
        # Adiciona barras para período 1genda_p1 = (f"Período 1 ({filtros['periodo1']['inicio'].strftime('%d/%m/%Y')} "
        fig.add_trace(go.Bar(              f"a {filtros['periodo1']['fim'].strftime('%d/%m/%Y')})")
            name=legenda_p1,ros['periodo2']['inicio'].strftime('%d/%m/%Y')} "
            y=df_comp['colaborador'],ltros['periodo2']['fim'].strftime('%d/%m/%Y')})")
            x=df_comp['tempo_ocioso_p1'],
            orientation='h',
            text=[formatar_tempo(t) for t in df_comp['tempo_ocioso_p1']],
            textposition='inside',
            marker_color=cores_tema['primaria'],
            textfont={'color': '#ffffff', 'size': 16},
            opacity=0.85
        ))
        empo_ocioso_p1'],
        # Adiciona barras para período 2  orientation='h',
        fig.add_trace(go.Bar(    text=[formatar_tempo(t) for t in df_comp['tempo_ocioso_p1']],
            name=legenda_p2,n='inside',
            y=df_comp['colaborador'],ores_tema['primaria'],
            x=df_comp['tempo_ocioso_p2'],t={'color': '#ffffff', 'size': 16},
            orientation='h',
            text=[formatar_tempo(t) for t in df_comp['tempo_ocioso_p2']],
            textposition='inside',
            marker_color=cores_tema['secundaria'],ra período 2
            textfont={'color': '#000000', 'size': 16},.Bar(
            opacity=0.85
        ))
        
        # Ajusta layout
        fig.update_layout(rmatar_tempo(t) for t in df_comp['tempo_ocioso_p2']],
            title={
                'text': 'Comparativo de Tempo de Ociosidade por Colaborador (Excluindo Horário de Almoço)','secundaria'],
                'font': {'size': 16, 'color': cores_tema['texto']}or': '#000000', 'size': 16},
            },
            barmode='stack',
            bargap=0.15,
            bargroupgap=0.1,ta layout
            height=max(600, len(df_comp) * 45),
            font={'size': 12, 'color': cores_tema['texto']},
            showlegend=True, de Ociosidade por Colaborador (Excluindo Horário de Almoço)',
            legend={       'font': {'size': 16, 'color': cores_tema['texto']}
                'orientation': 'h',    },
                'yanchor': 'bottom',e='stack',
                'y': 1.02,
                'xanchor': 'right',
                'x': 1,max(600, len(df_comp) * 45),
                'traceorder': 'normal'  # Mudado para 'normal' para manter ordem original das legendas            font={'size': 12, 'color': cores_tema['texto']},
            },
            margin=dict(l=20, r=160, t=80, b=40),
            plot_bgcolor='rgba(0,0,0,0)',        'orientation': 'h',
            paper_bgcolor=cores_tema['fundo']: 'bottom',
        )
        hor': 'right',
        return fig1,
    except Exception as e: 'normal'  # Mudado para 'normal' para manter ordem original das legendas
        st.error(f"Erro ao criar gráfico: {str(e)}")
        return None(l=20, r=160, t=80, b=40),
color='rgba(0,0,0,0)',
def gerar_insights_ociosidade(ocio_p1, ocio_p2):    paper_bgcolor=cores_tema['fundo']
    """Gera insights sobre a ociosidade dos colaboradores"""
    try:
        # Merge dos dados
        df_insights = pd.merge(pt Exception as e:
            ocio_p1, fico: {str(e)}")
            ocio_p2, 
            on='colaborador',
            suffixes=('_p1', '_p2'),_p2):
            how='outer'olaboradores"""
        ).fillna(0)
         dados
        # Calcular variação percentual
        df_insights['variacao'] = ((df_insights['tempo_ocioso_p2'] - df_insights['tempo_ocioso_p1']) / 
                                  df_insights['tempo_ocioso_p1'] * 100).replace([float('inf')], 100)
           on='colaborador',
        # Criar 4 colunas principais            suffixes=('_p1', '_p2'),
        col_perf1, col_perf2, col_perf3, col_insights = st.columns([0.25, 0.25, 0.25, 0.25])
        
        # Dividir colaboradores em 3 partes
        tamanho_parte = len(df_insights) // 3
        resto = len(df_insights) % 3s['tempo_ocioso_p2'] - df_insights['tempo_ocioso_p1']) / 
        indices = [f')], 100)
            (0, tamanho_parte + (1 if resto > 0 else 0)),
            (tamanho_parte + (1 if resto > 0 else 0), 2*tamanho_parte + (2 if resto > 1 else 1 if resto > 0 else 0)),
            (2*tamanho_parte + (2 if resto > 1 else 1 if resto > 0 else 0), len(df_insights))5, 0.25, 0.25, 0.25])
        ]

        # Primeira coluna de performancearte = len(df_insights) // 3
        with col_perf1:        resto = len(df_insights) % 3
            st.write("#### Performance (1/3)")
            df_parte = df_insights.iloc[indices[0][0]:indices[0][1]]_parte + (1 if resto > 0 else 0)),
            for _, row in df_parte.iterrows():lse 0), 2*tamanho_parte + (2 if resto > 1 else 1 if resto > 0 else 0)),
                status = "✅" if row['tempo_ocioso_p2'] <= row['tempo_ocioso_p1'] else "⚠️"lse 0), len(df_insights))
                st.write(
                    f"**{row['colaborador']}** {status}\n\n"
                    f"- P1: {formatar_tempo(row['tempo_ocioso_p1'])}\n" de performance
                    f"- P2: {formatar_tempo(row['tempo_ocioso_p2'])}\n"
                    f"- Variação: {row['variacao']:+.1f}%"
                )

        # Segunda coluna de performancetatus = "✅" if row['tempo_ocioso_p2'] <= row['tempo_ocioso_p1'] else "⚠️"
        with col_perf2:                st.write(
            st.write("#### Performance (2/3)")r']}** {status}\n\n"
            df_parte = df_insights.iloc[indices[1][0]:indices[1][1]] P1: {formatar_tempo(row['tempo_ocioso_p1'])}\n"
            for _, row in df_parte.iterrows():w['tempo_ocioso_p2'])}\n"
                status = "✅" if row['tempo_ocioso_p2'] <= row['tempo_ocioso_p1'] else "⚠️"
                st.write(
                    f"**{row['colaborador']}** {status}\n\n"
                    f"- P1: {formatar_tempo(row['tempo_ocioso_p1'])}\n"de performance
                    f"- P2: {formatar_tempo(row['tempo_ocioso_p2'])}\n"
                    f"- Variação: {row['variacao']:+.1f}%"
                )

        # Terceira coluna de performancetatus = "✅" if row['tempo_ocioso_p2'] <= row['tempo_ocioso_p1'] else "⚠️"
        with col_perf3:                st.write(
            st.write("#### Performance (3/3)")['colaborador']}** {status}\n\n"
            df_parte = df_insights.iloc[indices[2][0]:indices[2][1]]: {formatar_tempo(row['tempo_ocioso_p1'])}\n"
            for _, row in df_parte.iterrows():mpo(row['tempo_ocioso_p2'])}\n"
                status = "✅" if row['tempo_ocioso_p2'] <= row['tempo_ocioso_p1'] else "⚠️"        f"- Variação: {row['variacao']:+.1f}%"
                st.write(
                    f"**{row['colaborador']}** {status}\n\n"
                    f"- P1: {formatar_tempo(row['tempo_ocioso_p1'])}\n"a de performance
                    f"- P2: {formatar_tempo(row['tempo_ocioso_p2'])}\n"
                    f"- Variação: {row['variacao']:+.1f}%"
                )s[2][0]:indices[2][1]]

        # Coluna de insights✅" if row['tempo_ocioso_p2'] <= row['tempo_ocioso_p1'] else "⚠️"
        with col_insights:
            st.write("#### 📈 Insights")       f"**{row['colaborador']}** {status}\n\n"
                    f"- P1: {formatar_tempo(row['tempo_ocioso_p1'])}\n"
            # Melhor performance (menor ociosidade)ormatar_tempo(row['tempo_ocioso_p2'])}\n"
            melhor = df_insights.loc[df_insights['tempo_ocioso_p2'].idxmin()]
            st.markdown(
                f"<div class='success-box'>"
                f"<b>🎯 Menor Ociosidade</b><br>"
                f"{melhor['colaborador']}<br>"
                f"Tempo: {formatar_tempo(melhor['tempo_ocioso_p2'])}"
                f"</div>",
                unsafe_allow_html=Truer ociosidade)
            )elhor = df_insights.loc[df_insights['tempo_ocioso_p2'].idxmin()]
                        st.markdown(
            # Maior ociosidadess='success-box'>"
            pior = df_insights.loc[df_insights['tempo_ocioso_p2'].idxmax()]
            st.markdown(                f"{melhor['colaborador']}<br>"
                f"<div class='warning-box'>"ar_tempo(melhor['tempo_ocioso_p2'])}"
                f"<b>⚠️ Maior Ociosidade</b><br>"
                f"{pior['colaborador']}<br>"
                f"Tempo: {formatar_tempo(pior['tempo_ocioso_p2'])}"        )
                f"</div>",    
                unsafe_allow_html=True
            )    pior = df_insights.loc[df_insights['tempo_ocioso_p2'].idxmax()]

    except Exception as e:
        st.error(f"Erro ao gerar insights: {str(e)}")        f"<b>⚠️ Maior Ociosidade</b><br>"
>"
def mostrar_aba(dados, filtros):
    """Mostra a aba de Análise de Ociosidade"""</div>",
    st.header("Análise de Ociosidade")        unsafe_allow_html=True
    
    try:
        st.session_state['tema_atual'] = detectar_tema()
        rro ao gerar insights: {str(e)}")
        # Linha de seletores
        col1, col2, col3, col4 = st.columns(4)
         a aba de Análise de Ociosidade"""
        with col1:eader("Análise de Ociosidade")
            colaboradores = sorted(dados['base']['usuário'].unique())
            colaborador = st.selectbox(
                "Selecione o Colaborador",
                options=['Todos'] + colaboradores,
                help="Escolha um colaborador para análise detalhada"    ocio_p1 = calcular_ociosidade_por_periodo(dados, filtros, 'periodo1')
            )_ociosidade_por_periodo(dados, filtros, 'periodo2')
        
        with col2:y or ocio_p2.empty:
            turnos = ["Todos", "TURNO A", "TURNO B", "TURNO C"]            st.warning("Não há dados suficientes para análise de ociosidade no período selecionado.")




































































        st.exception(e)        st.error(f"Erro ao mostrar aba: {str(e)}")    except Exception as e:                gerar_insights_ociosidade(ocio_p1, ocio_p2)        with st.expander("Ver análise detalhada", expanded=True):        st.subheader("📈 Análise Detalhada")        st.markdown("---")                    )                key=f"grafico_ociosidade_{st.session_state['tema_atual']}"                use_container_width=True,                fig,            st.plotly_chart(        if fig:        fig = criar_grafico_comparativo(ocio_p1, ocio_p2, filtros)                    return            st.warning("Não há dados suficientes para análise de ociosidade no período selecionado.")        if ocio_p1.empty or ocio_p2.empty:                ocio_p2 = calcular_ociosidade_por_periodo(dados, filtros, 'periodo2', adicional_filters)        ocio_p1 = calcular_ociosidade_por_periodo(dados, filtros, 'periodo1', adicional_filters)        # Chamar função com filtros adicionais                }            'data_especifica': data_especifica            'cliente': cliente,            'turno': turno,            'colaborador': colaborador,        adicional_filters = {        # Filtros adicionais (mesmo formato que colaborador.py)                        data_especifica = pd.to_datetime(f"{ano}-{mes}-{dia}").date()            dia, mes, ano = map(int, data_selecionada.split('/'))        if data_selecionada != "Todas":        data_especifica = None        # Conversão da data selecionada                        )                help="Escolha uma data específica ou 'Todas' para ver o período completo"                options=datas_opcoes,                "Selecione a Data",            data_selecionada = st.selectbox(                        datas_opcoes = ["Todas"] + [data.strftime("%d/%m/%Y") for data in datas_disponiveis]            datas_disponiveis = sorted(dados['base'][mask_periodo]['retirada'].dt.date.unique())            )                (dados['base']['retirada'].dt.date <= filtros['periodo2']['fim'])                (dados['base']['retirada'].dt.date >= filtros['periodo2']['inicio']) &            mask_periodo = (            # Obter lista de datas disponíveis no período        with col4:            )                help="Filtre por cliente específico"                options=clientes,                "Selecione o Cliente",            cliente = st.selectbox(            clientes = ["Todos"] + sorted(dados['base']['CLIENTE'].unique().tolist())        with col3:                        )                help="Filtre por turno específico"                options=turnos,                "Selecione o Turno",            turno = st.selectbox(            return
        
        fig = criar_grafico_comparativo(ocio_p1, ocio_p2, filtros)
        if fig:
            st.plotly_chart(
                fig,
                use_container_width=True,
                key=f"grafico_ociosidade_{st.session_state['tema_atual']}"
            )
        
        st.markdown("---")
        st.subheader("📈 Análise Detalhada")
        with st.expander("Ver análise detalhada", expanded=True):
            gerar_insights_ociosidade(ocio_p1, ocio_p2)
    
    except Exception as e:
        st.error(f"Erro ao mostrar aba: {str(e)}")
        st.exception(e)
