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
        st.subheader("📊 Insights")
        with st.expander("Ver insights"):
            df = dados['base']
            
            # Preparação dos dados
            df['hora'] = df['retirada'].dt.hour
            df['data'] = df['retirada'].dt.date
            # Configurar dias da semana em português (ordem brasileira)
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
            horarios_criticos = picos[picos > picos.mean() + picos.std()]  # Movido para cima
            
            # Análise de comboios
            def identificar_comboios(grupo):
                return (grupo['id'].count() > grupo['id'].count().mean() + grupo['id'].count().std())
            
            comboios = df.groupby(['data', 'periodo_15min']).filter(identificar_comboios)
            comboios_por_data = df.groupby(['data', 'periodo_15min'])['id'].count()
            threshold = int(comboios_por_data.mean() + comboios_por_data.std())
            
            # Layout com colunas
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("### 📈 Métricas Principais")
                # Média diária baseada nas linhas do mapa de calor
                media_diaria = int(pivot.mean(axis=1).mean())  # Média das somas diárias
                total_dias = len(pivot.index)
                st.metric(
                    "Média diária de senhas",
                    f"{media_diaria}",
                    f"Total de {total_dias} dias analisados"
                )
                
                # Encontrar os 3 maiores picos da tabela
                valores_flat = pivot.values.flatten()  # Transformar matriz em array
                top_3_indices = np.argsort(valores_flat)[-3:][::-1]  # Índices dos 3 maiores valores
                
                # Encontrar datas e horas correspondentes aos picos
                picos_info = []
                for idx in top_3_indices:
                    linha = idx // pivot.shape[1]  # Índice da linha (data)
                    coluna = idx % pivot.shape[1]  # Índice da coluna (hora)
                    data = pivot.index[linha]
                    valor = int(valores_flat[idx])
                    picos_info.append(f"{data} {coluna:02d}h: {valor}")
                
                # Exibir o maior pico e seus detalhes
                st.metric(
                    "Maiores picos registrados",
                    f"{int(valores_flat[top_3_indices[0]])} senhas",
                    f"Top 3 momentos críticos"
                )
                for pico in picos_info:
                    st.write(f"- **{pico}** senhas")
                
                st.write("### ⏰ Horários Críticos")
                for hora, qtd in horarios_criticos.items():  # Agora usa a variável definida acima
                    st.write(f"- **{hora:02d}h**: {int(qtd)} retiradas/dia")
            
            with col2:
                st.write("### 📅 Padrão Semanal")
                # Ordenar dias da semana começando pelo domingo
                ordem_dias = ['Domingo', 'Segunda-feira', 'Terça-feira', 'Quarta-feira', 
                            'Quinta-feira', 'Sexta-feira', 'Sábado']
                dias_mov_ordenado = dias_mov.reindex(ordem_dias).dropna()
                for dia, media in dias_mov_ordenado.items():
                    st.write(f"- **{dia}**: {int(media)} retiradas")
                
                st.write("### 🚦 Picos de Comboio")
                if not comboios.empty:
                    top_comboios = comboios_por_data.sort_values(ascending=False).head(3)
                    for (data, periodo), qtd in top_comboios.items():
                        st.write(f"- **{data.strftime('%d/%m/%Y')} {periodo.strftime('%H:%M')}**: {qtd}")
            
            # Recomendações em largura total
            st.write("### 💡 Plano de Ação")
            
            col_rec1, col_rec2 = st.columns(2)
            
            with col_rec1:
                st.write("#### Ações Imediatas")
                st.write(f"""
                - Reforço de equipe: {hora_pico:02d}h - {(hora_pico + 1) % 24:02d}h
                - Prioridade: {dia_mais_mov}s
                - Limite de alerta: {threshold} retiradas/15min
                """)
            
            with col_rec2:
                st.write("#### Ações Preventivas")
                st.write("""
                - Implementar agendamento prévio
                - Distribuir senhas por horário
                - Comunicar horários alternativos
                """)
            
    except Exception as e:
        st.error("Erro ao gerar a aba de Análise de Chegada em Comboio")
        st.exception(e)