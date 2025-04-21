import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import json

def criar_mapa_calor(dados, filtros, cliente=None):
    """Cria mapa de calor de retirada de senhas"""
    df = dados['base']
    cores_tema = obter_cores_tema()
    
    # Aplicar filtros de data para período 2
    mask = (
        (df['retirada'].dt.date >= filtros['periodo2']['inicio']) &
        (df['retirada'].dt.date <= filtros['periodo2']['fim'])
    )
    df_filtrado = df[mask]
    
    # Filtrar por cliente se especificado
    if cliente:
        df_filtrado = df_filtrado[df_filtrado['CLIENTE'] == cliente]
    
    # Criar matriz de dados para o mapa de calor
    pivot = pd.pivot_table(
        df_filtrado,
        values='id',
        index=df_filtrado['retirada'].dt.strftime('%d/%m/%Y'),
        columns=df_filtrado['retirada'].dt.hour,
        aggfunc='count',
        fill_value=0
    )
    
    # Ordenar o índice (datas) em ordem decrescente
    pivot = pivot.reindex(index=sorted(pivot.index, key=lambda x: pd.to_datetime(x, format='%d/%m/%Y'), reverse=True))
    
    # Garantir todas as horas do dia (0-23)
    todas_horas = range(24)
    for hora in todas_horas:
        if hora not in pivot.columns:
            pivot[hora] = 0
    pivot = pivot.reindex(columns=sorted(pivot.columns))
    
    # Criar mapa de calor com configurações atualizadas
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=[f"{h:02d}h" for h in pivot.columns],
        y=pivot.index,
        text=pivot.values,
        texttemplate="%{text}" if "%{text} != 0" else "",  # Mostrar apenas valores não-zero
        textfont={
            "size": 16,
            "family": "Arial Black",
            "color": "#E6E6E6"
        },
        customdata=pivot.values,
        hovertemplate="Data: %{y}<br>Hora: %{x}<br>Quantidade: %{customdata}<extra></extra>",
        colorscale=[
            [0.0, 'rgba(0,0,0,0)'],      # Transparente para zeros
            [0.001, 'rgba(0,0,0,0.1)'],  # Quase transparente para valores muito baixos
            [0.3, cores_tema['secundaria']],
            [0.7, cores_tema['primaria']],
            [1.0, cores_tema['erro']]
        ],
        showscale=True,
        hoverongaps=False,  # Desabilita hover em células vazias
        zauto=True,         # Ajusta escala de cores automaticamente
        zmid=0              # Define o ponto médio da escala
    ))
    
    # Atualizar layout com configurações seguras
    fig.update_layout(
        title_text=f"Mapa de Calor - Retirada de Senhas {'- ' + cliente if cliente else ''}",
        title_font_size=16,
        title_font_color="#E6E6E6",
        paper_bgcolor=cores_tema['fundo'],
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#E6E6E6"),  # Cor mais clara para todas as fontes
        xaxis=dict(
            title="Hora do Dia",
            ticktext=[f"{h:02d}h" for h in range(24)],
            tickvals=list(range(24)),
            tickangle=0,  # Horizontal alignment
            gridcolor=cores_tema['grid'],
            title_font=dict(size=16, color="#E6E6E6"),  # Increased title font size
            tickfont=dict(size=14, color="#E6E6E6"),  # Increased tick font size
            dtick=1  # Force display of all hours
        ),
        yaxis=dict(
            title="Data",
            gridcolor=cores_tema['grid'],
            title_font=dict(size=16, color="#E6E6E6"),  # Increased title font size
            tickfont=dict(size=14, color="#E6E6E6")  # Increased tick font size
        ),
        height=max(400, len(pivot.index) * 25),
        margin=dict(l=50, r=50, t=50, b=80)  # Slightly reduced bottom margin
    )
    
    return fig, pivot

def obter_cores_tema():
    """Retorna as cores baseadas no tema atual"""
    is_dark = detectar_tema() == 'dark'
    return {
        'primaria': '#1a5fb4' if is_dark else '#1864ab',
        'secundaria': '#4dabf7' if is_dark else '#83c9ff',
        'texto': '#ffffff' if is_dark else '#2c3e50',
        'fundo': '#0e1117' if is_dark else '#ffffff',
        'grid': '#2c3e50' if is_dark else '#d3d3d3',
        'erro': '#ff0000' if is_dark else '#e63946'  # Adiciona cor para valores altos
    }

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

def mostrar_aba(dados, filtros):
    """Mostra a aba de análise de chegada em comboio"""
    st.header("Análise de Chegada em Comboio I")
    st.write("Mapa de calor mostrando a concentração de retirada de senhas por hora e dia")
    
    with st.expander("ℹ️ Como funciona?"):
        st.markdown("""
        ### Como analisamos o padrão de chegada?

        1. **Mapa de Calor**:
        - **Eixo X**: 24 horas do dia (00h a 23h)
        - **Eixo Y**: Dias do período analisado
        - **Cores**: Intensidade representa volume de senhas
            - 🟦 Azul claro = Baixo volume
            - 🟦 Azul escuro = Médio volume
            - 🟥 Vermelho = Alto volume (comboio)

        2. **Métricas Analisadas**:
        - **Volume**: Quantidade de senhas por hora
        - **Concentração**: Identificação de picos
        - **Padrões**: Repetição de comportamentos

        3. **Definição de Comboio**:
        - Volume > (Média + Desvio Padrão)
        - Concentração em intervalos de 15 minutos
        - Impacto no dimensionamento

        4. **Análise de Padrões**:
        - **Dias da Semana**: Variação por dia
        - **Horários**: Picos recorrentes
        - **Tendências**: Comportamento ao longo do tempo

        5. **Insights Gerados**:
        - 🎯 Horários críticos
        - 📊 Dias mais movimentados
        - 💡 Recomendações operacionais
        """)
    
    try:
        # Seleção de visualização
        tipo_analise = st.radio(
            "Visualizar:",
            ["Geral", "Por Cliente"],
            horizontal=True
        )
        
        if tipo_analise == "Por Cliente":
            # Lista de clientes disponíveis
            clientes = sorted(dados['base']['CLIENTE'].unique())
            cliente_selecionado = st.selectbox(
                "Selecione o Cliente:",
                clientes
            )
            
            # Criar mapa de calor para o cliente selecionado
            fig, pivot = criar_mapa_calor(dados, filtros, cliente_selecionado)
        else:
            # Criar mapa de calor geral
            fig, pivot = criar_mapa_calor(dados, filtros)
        
        # Exibir gráfico
        st.plotly_chart(fig, use_container_width=True)
        
        # Insights
        st.subheader("📊 Análise Detalhada")
        with st.expander("Ver análise detalhada", expanded=True):
            df = dados['base']
            
            # Preparação dos dados
            df['hora'] = df['retirada'].dt.hour
            df['data'] = df['retirada'].dt.date
            dias_semana = {
                'Sunday': 'Domingo',
                'Monday': 'Segunda-feira',
                'Tuesday': 'Terça-feira',
                'Wednesday': 'Quarta-feira',
                'Thursday': 'Quinta-feira',
                'Friday': 'Sexta-feira',
                'Saturday': 'Sábado'
            }
            df['dia_semana'] = df['retirada'].dt.day_name().map(dias_semana)
            df['periodo_15min'] = df['retirada'].dt.floor('15T')
            
            # Cálculos básicos
            picos = df.groupby('hora')['id'].count()
            hora_pico = picos.idxmax()
            dias_mov = df.groupby(['dia_semana', 'data'])['id'].count().groupby('dia_semana').mean()
            dia_mais_mov = dias_mov.idxmax()
            horarios_criticos = picos[picos > picos.mean() + picos.std()]
            
            def identificar_comboios(grupo):
                return (grupo['id'].count() > grupo['id'].count().mean() + grupo['id'].count().std())
            
            comboios = df.groupby(['data', 'periodo_15min']).filter(identificar_comboios)
            comboios_por_data = df.groupby(['data', 'periodo_15min'])['id'].count()
            threshold = int(comboios_por_data.mean() + comboios_por_data.std())

            # 1. Visão Geral em duas colunas
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📈 Visão Geral")
                media_diaria = int(pivot.mean(axis=1).mean())
                total_dias = len(pivot.index)
                st.markdown(f"""
                - Média diária: **{media_diaria:,}** senhas
                - Total de dias: **{total_dias}**
                - Limite de alerta: **{threshold}** senhas/15min
                """)
                
                st.subheader("⏱️ Horários Críticos")
                for hora, qtd in horarios_criticos.items():
                    st.markdown(f"- **{hora:02d}h**: {int(qtd):,} retiradas/dia")

            with col2:
                st.subheader("📅 Padrão Semanal")
                ordem_dias = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 
                            'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']
                dias_mov_ordenado = dias_mov.reindex(ordem_dias).dropna()
                
                # Encontrar o dia mais movimentado
                max_mov = dias_mov_ordenado.max()
                for dia, media in dias_mov_ordenado.items():
                    destaque = "**🔥**" if media == max_mov else ""
                    st.markdown(f"- {destaque}{dia}: **{int(media):,}** retiradas")
            
            # 2. Análise de Comboios em duas colunas
            st.markdown("---")
            st.subheader("🚦 Análise de Comboios")
            col3, col4 = st.columns(2)
            
            with col3:
                st.subheader("📊 Maiores Concentrações")
                top_concentracoes = comboios_por_data.nlargest(5)
                for (data, periodo), qtd in top_concentracoes.items():
                    st.markdown(f"""
                    - **{data.strftime('%d/%m/%Y')} {periodo.strftime('%H:%M')}**
                      - Senhas: **{int(qtd):,}**
                      - {f"⚠️ Acima do limite" if qtd > threshold else ""}
                    """)

            with col4:
                st.subheader("💡 Recomendações")
                st.markdown("""
                #### Ações Imediatas
                - Reforço em horários críticos
                - Monitoramento dos picos
                - Ajuste de equipe nos dias mais movimentados
                
                #### Ações Preventivas
                - Distribuição de senhas por horário
                - Sistema de agendamento
                - Comunicação de horários alternativos
                """)
            
    except Exception as e:
        st.error("Erro ao gerar a aba de Análise de Chegada em Comboio")
        st.exception(e)