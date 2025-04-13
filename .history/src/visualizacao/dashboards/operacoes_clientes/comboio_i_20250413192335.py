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
        texttemplate="%{text}",
        textfont={
            "size": 16,
            "family": "Arial Black",
            "color": "#E6E6E6"  # Cor mais clara para melhor visibilidade
        },
        customdata=pivot.values,
        hovertemplate="Data: %{y}<br>Hora: %{x}<br>Quantidade: %{customdata}<extra></extra>",
        colorscale=[
            [0.0, 'rgba(0,0,0,0.1)'],     # Transparente para valores baixos
            [0.3, cores_tema['secundaria']],  # Cor secundária para valores médio-baixos
            [0.7, cores_tema['primaria']],    # Cor primária para valores médio-altos
            [1.0, cores_tema['erro']]         # Cor de erro para valores altos
        ],
        showscale=True
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
            tickangle=-45,
            gridcolor=cores_tema['grid'],
            title_font=dict(size=14, color="#E6E6E6"),
            tickfont=dict(size=10, color="#E6E6E6"),  # Fonte menor
            dtick=1  # Força exibição de todas as horas
        ),
        yaxis=dict(
            title="Data",
            gridcolor=cores_tema['grid'],
            title_font=dict(size=14, color="#E6E6E6"),
            tickfont=dict(size=12, color="#E6E6E6")
        ),
        height=max(400, len(pivot.index) * 25),
        margin=dict(l=50, r=50, t=50, b=100)  # Aumentar margem inferior
    )
    
    return fig

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
            fig = criar_mapa_calor(dados, filtros, cliente_selecionado)
        else:
            # Criar mapa de calor geral
            fig = criar_mapa_calor(dados, filtros)
        
        # Exibir gráfico
        st.plotly_chart(fig, use_container_width=True)
        
        # Insights
        st.subheader("📊 Insights")
        with st.expander("Ver insights"):
            df = dados['base']
            
            # Análise de horários de pico
            df['hora'] = df['retirada'].dt.hour
            df['data'] = df['retirada'].dt.date
            picos = df.groupby('hora')['id'].count()
            hora_pico = picos.idxmax()
            
            # Análise por dia da semana
            df['dia_semana'] = df['retirada'].dt.day_name()
            dias_mov = df.groupby(['dia_semana', 'data'])['id'].count().groupby('dia_semana').mean()
            dia_mais_mov = dias_mov.idxmax()
            
            # Análise detalhada de comboios
            def identificar_comboios(grupo):
                return (grupo['id'].count() > grupo['id'].count().mean() + grupo['id'].count().std())
            
            # Análise por períodos de 15 minutos
            df['periodo_15min'] = df['retirada'].dt.floor('15T')
            comboios = df.groupby(['data', 'periodo_15min']).filter(identificar_comboios)
            
            st.write("### 🎯 Análise Detalhada de Comboios")
            
            # 1. Horários Críticos
            st.write("#### ⏰ Horários Críticos:")
            horarios_criticos = picos[picos > picos.mean() + picos.std()]
            for hora, qtd in horarios_criticos.items():
                st.write(f"- **{hora:02d}h**: Média de {int(qtd)} retiradas/dia")
            
            # 2. Dias mais afetados
            st.write("\n#### 📅 Padrão Semanal:")
            for dia, media in dias_mov.sort_values(ascending=False).items():
                st.write(f"- **{dia}**: Média de {int(media)} retiradas")
            
            # 3. Análise de Comboios
            st.write("\n#### 🚦 Detecção de Comboios:")
            if not comboios.empty:
                comboios_por_data = comboios.groupby(['data', 'periodo_15min'])['id'].count()
                top_comboios = comboios_por_data.sort_values(ascending=False).head(5)
                
                st.write("**Top 5 Momentos Críticos:**")
                for (data, periodo), qtd in top_comboios.items():
                    st.write(f"- **{data.strftime('%d/%m/%Y')} às {periodo.strftime('%H:%M')}**: {qtd} retiradas em 15 minutos")
            
            # 4. Recomendações
            st.write("\n### 💡 Recomendações:")
            st.write("""
            1. **Distribuição de Pessoal:**
                - Reforçar equipe nos horários de pico ({:02d}h - {:02d}h)
                - Priorizar cobertura às {dia_mais_mov}s
            
            2. **Gestão de Filas:**
                - Implementar sistema de senhas com horários escalonados
                - Distribuir retiradas ao longo do dia para evitar concentrações
            
            3. **Monitoramento:**
                - Acompanhar em tempo real os períodos de 15 minutos
                - Ação imediata quando detectar mais de {threshold} retiradas em 15 minutos
            
            4. **Comunicação:**
                - Informar clientes sobre horários menos movimentados
                - Estabelecer canais de agendamento prévio
            """.format(
                hora_pico,
                (hora_pico + 1) % 24,
                threshold=int(comboios_por_data.mean() + comboios_por_data.std())
            ))
            
            # 5. KPIs
            st.write("\n### 📈 KPIs de Monitoramento:")
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "Média diária de retiradas",
                    f"{int(df.groupby('data')['id'].count().mean())}"
                )
            with col2:
                st.metric(
                    "Pico de retiradas (15min)",
                    f"{int(df.groupby('periodo_15min')['id'].count().max())}"
                )
    
    except Exception as e:
        st.error("Erro ao gerar a aba de Análise de Chegada em Comboio")
        st.exception(e)