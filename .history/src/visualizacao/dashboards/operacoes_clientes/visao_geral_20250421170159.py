import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

try:
    from visualizacao.tema import Tema
    tema_disponivel = True
except ImportError:
    tema_disponivel = False

def calcular_metricas_gerais(dados, filtros):
    """Calcula métricas gerais para os dois períodos"""
    st.write("Debug: Iniciando cálculo de métricas")
    st.write(f"Debug: Filtros recebidos: {filtros}")
    
    df = dados['base']
    st.write(f"Debug: Tamanho do DataFrame base: {len(df)}")
    
    if df.empty:
        st.warning("Não há dados disponíveis na base.")
        return None
        
    metricas = {}
    
    for periodo in ['periodo1', 'periodo2']:
        st.write(f"\nDebug: Processando {periodo}")
        
        # Validar filtros do período
        if not filtros.get(periodo):
            st.warning(f"Debug: {periodo} não encontrado nos filtros")
            return None
            
        if not filtros[periodo].get('inicio') or not filtros[periodo].get('fim'):
            st.warning(f"Debug: Datas início/fim não encontradas para {periodo}")
            st.write(f"Debug: Conteúdo do filtro {periodo}: {filtros[periodo]}")
            return None
            
        # Filtrar dados por período
        st.write(f"Debug: Filtrando dados para {periodo}")
        st.write(f"Debug: Data início: {filtros[periodo]['inicio']}")
        st.write(f"Debug: Data fim: {filtros[periodo]['fim']}")
        
        mask = (
            (df['retirada'].dt.date >= filtros[periodo]['inicio']) &
            (df['retirada'].dt.date <= filtros[periodo]['fim'])
        )
        df_periodo = df[mask].copy()
        
        st.write(f"Debug: Registros encontrados para {periodo}: {len(df_periodo)}")
        
        if df_periodo.empty:
            st.warning(f"Não há dados disponíveis para o {periodo}")
            return None
        
        # Debug dos dados antes do cálculo
        st.write(f"Debug: Colunas disponíveis: {df_periodo.columns.tolist()}")
        st.write(f"Debug: Amostra de tempos de atendimento: {df_periodo['tpatend'].head()}")
        st.write(f"Debug: Amostra de tempos de espera: {df_periodo['tpesper'].head()}")
        
        # Calcular métricas com validação e debug
        total_atend = len(df_periodo)
        tempo_atend = df_periodo['tpatend'].mean() / 60 if not df_periodo['tpatend'].isna().all() else 0
        tempo_espera = df_periodo['tpesper'].mean() / 60 if not df_periodo['tpesper'].isna().all() else 0
        tempo_perm = df_periodo['tempo_permanencia'].mean() / 60 if not df_periodo['tempo_permanencia'].isna().all() else 0
        
        st.write(f"""
        Debug: Métricas calculadas para {periodo}:
        - Total atendimentos: {total_atend}
        - Tempo médio atendimento: {tempo_atend:.2f} min
        - Tempo médio espera: {tempo_espera:.2f} min
        - Tempo médio permanência: {tempo_perm:.2f} min
        """)
        
        metricas[periodo] = {
            'total_atendimentos': total_atend,
            'tempo_medio_atendimento': tempo_atend,
            'tempo_medio_espera': tempo_espera,
            'tempo_medio_permanencia': tempo_perm,
            'qtd_clientes': df_periodo['CLIENTE'].nunique(),
            'qtd_operacoes': df_periodo['OPERAÇÃO'].nunique()
        }

    # Debug das variações
    st.write("\nDebug: Calculando variações entre períodos")
    
    var_total = ((metricas['periodo2']['total_atendimentos'] - metricas['periodo1']['total_atendimentos']) / 
                metricas['periodo1']['total_atendimentos'] * 100) if metricas['periodo1']['total_atendimentos'] > 0 else 0
                
    var_atendimento = ((metricas['periodo2']['tempo_medio_atendimento'] - metricas['periodo1']['tempo_medio_atendimento']) / 
                       metricas['periodo1']['tempo_medio_atendimento'] * 100) if metricas['periodo1']['tempo_medio_atendimento'] > 0 else 0
                       
    var_espera = ((metricas['periodo2']['tempo_medio_espera'] - metricas['periodo1']['tempo_medio_espera']) / 
                 metricas['periodo1']['tempo_medio_espera'] * 100) if metricas['periodo1']['tempo_medio_espera'] > 0 else 0
                 
    var_permanencia = ((metricas['periodo2']['tempo_medio_permanencia'] - metricas['periodo1']['tempo_medio_permanencia']) / 
                      metricas['periodo1']['tempo_medio_permanencia'] * 100) if metricas['periodo1']['tempo_medio_permanencia'] > 0 else 0
    
    metricas['variacoes'] = {
        'total_atendimentos': var_total,
        'tempo_medio_atendimento': var_atendimento,
        'tempo_medio_espera': var_espera,
        'tempo_medio_permanencia': var_permanencia
    }
    
    return metricas

def criar_graficos_comparativos(dados, filtros, metricas):
    """Cria gráficos comparativos entre os dois períodos"""
    # Definir cores
    if tema_disponivel:
        try:
            cores = Tema.obter_cores_grafico(num_cores=2, modo='categorico')
        except:
            cores = ['rgba(75, 192, 192, 0.8)', 'rgba(153, 102, 255, 0.8)']
    else:
        cores = ['rgba(75, 192, 192, 0.8)', 'rgba(153, 102, 255, 0.8)']
    
    # Criar figura com subplots
    fig = make_subplots(rows=1, cols=2,
                       subplot_titles=('Volume de Atendimentos', 'Tempos Médios (min)'),
                       specs=[[{"type": "bar"}, {"type": "bar"}]])
    
    # Gráfico 1: Volume de Atendimentos
    fig.add_trace(
        go.Bar(
            x=['Período 1', 'Período 2'],
            y=[metricas['periodo1']['total_atendimentos'], metricas['periodo2']['total_atendimentos']],
            marker_color=cores,
            text=[f"{metricas['periodo1']['total_atendimentos']}", f"{metricas['periodo2']['total_atendimentos']}"],
            textposition='auto'
        ),
        row=1, col=1
    )
    
    # Gráfico 2: Tempos Médios
    fig.add_trace(
        go.Bar(
            name='Atendimento',
            x=['Período 1', 'Período 2'],
            y=[metricas['periodo1']['tempo_medio_atendimento'], metricas['periodo2']['tempo_medio_atendimento']],
            marker_color=cores[0]
        ),
        row=1, col=2
    )
    
    fig.add_trace(
        go.Bar(
            name='Espera',
            x=['Período 1', 'Período 2'],
            y=[metricas['periodo1']['tempo_medio_espera'], metricas['periodo2']['tempo_medio_espera']],
            marker_color=cores[1]
        ),
        row=1, col=2
    )
    
    # Atualizar layout
    fig.update_layout(
        height=400,
        barmode='group',
        title_text="Comparativo entre Períodos"
    )
    
    # Aplicar tema se disponível
    if tema_disponivel:
        try:
            fig = Tema.configurar_grafico_padrao(fig)
        except:
            pass
    
    return fig

def mostrar_aba(dados, filtros):
    """Mostra a aba Geral com visão consolidada e principais insights"""
    st.header("Visão Geral do Atendimento")
    
    with st.expander("ℹ️ Como funciona?"):
        st.markdown("""
        ### Como analisamos o desempenho geral?

        1. **Métricas de Volume**:
        - **Total de Atendimentos**: Quantidade de senhas atendidas
        - **Variação**: Comparativo entre períodos (%)
        - **Tendência**: Análise da evolução do volume

        2. **Métricas de Tempo**:
        - **Tempo de Atendimento**: Duração média do atendimento
        - **Tempo de Espera**: Média de espera dos clientes
        - **Tempo de Permanência**: Tempo total no estabelecimento
        - **Variações**: Comparativo entre períodos (%)
            - 🟢 Variação negativa = Redução no tempo (melhor)
            - 🔴 Variação positiva = Aumento no tempo (pior)

        3. **Análise de Performance**:
        - ✅ Melhoria: Redução nos tempos ou aumento controlado de volume
        - ⚠️ Atenção: Aumento nos tempos ou redução de volume

        4. **Indicadores Consolidados**:
        - **Clientes**: Total de clientes atendidos
        - **Operações**: Tipos de serviços realizados
        - **Volume/Tempo**: Relação entre quantidade e duração

        5. **Insights Gerados**:
        - 📈 Análise de tendências
        - 🎯 Pontos de melhoria
        - 💡 Recomendações operacionais
        """)
    
    try:
        # Debug inicial detalhado
        st.write("=== Debug Detalhado ===")
        st.write("1. Verificação de Dados:")
        st.write(f"- Dados recebidos: {type(dados)}")
        st.write(f"- Chaves disponíveis: {dados.keys() if dados else 'Nenhum dado'}")
        
        if dados and 'base' in dados:
            st.write("\n2. Informações do DataFrame:")
            st.write(f"- Tamanho: {len(dados['base'])}")
            st.write(f"- Colunas: {dados['base'].columns.tolist()}")
            st.write(f"- Primeiras linhas:")
            st.write(dados['base'].head())
            st.write("\n3. Informações de Data:")
            st.write(f"- Menor data: {dados['base']['retirada'].min()}")
            st.write(f"- Maior data: {dados['base']['retirada'].max()}")
        
        st.write("\n4. Verificação dos Filtros:")
        st.write(f"- Filtros recebidos: {type(filtros)}")
        for periodo in ['periodo1', 'periodo2']:
            if filtros and periodo in filtros:
                st.write(f"\nFiltro {periodo}:")
                st.write(f"- Início: {filtros[periodo].get('inicio')}")
                st.write(f"- Fim: {filtros[periodo].get('fim')}")
                if 'inicio' in filtros[periodo] and 'fim' in filtros[periodo]:
                    st.write(f"- Tipo data início: {type(filtros[periodo]['inicio'])}")
                    st.write(f"- Tipo data fim: {type(filtros[periodo]['fim'])}")
            else:
                st.write(f"\n{periodo} não encontrado ou inválido")
        
        st.write("\n=== Fim do Debug ===")
        st.markdown("---")

        # Continua com o código original
        st.write("Debug: Iniciando visualização geral")
        st.write(f"Debug: Estrutura dos dados recebidos: {dados.keys() if dados else None}")
        st.write(f"Debug: Estrutura dos filtros: {filtros}")
        
        # Validar dados de entrada
        if not dados or 'base' not in dados:
            st.warning("Debug: Dados não encontrados ou sem chave 'base'")
            return
            
        if dados['base'].empty:
            st.warning("Debug: DataFrame base está vazio")
            return
            
        if not filtros or not all(periodo in filtros for periodo in ['periodo1', 'periodo2']):
            st.warning("Filtros de período não configurados corretamente.")
            return
            
        # Calcular métricas gerais
        metricas = calcular_metricas_gerais(dados, filtros)
        
        if metricas is None:
            return
            
        # Exibir cards com as principais métricas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total de Atendimentos", 
                f"{metricas['periodo2']['total_atendimentos']}",
                f"{metricas['variacoes']['total_atendimentos']:.1f}%"
            )
        
        with col2:
            st.metric(
                "Tempo Médio de Atendimento",
                f"{metricas['periodo2']['tempo_medio_atendimento']:.1f} min",
                f"{metricas['variacoes']['tempo_medio_atendimento']:.1f}%",
                delta_color="inverse"  # Inversão: negativo é bom para redução de tempo
            )
        
        with col3:
            st.metric(
                "Tempo Médio de Espera",
                f"{metricas['periodo2']['tempo_medio_espera']:.1f} min",
                f"{metricas['variacoes']['tempo_medio_espera']:.1f}%",
                delta_color="inverse"  # Inversão: negativo é bom para redução de tempo
            )
        
        with col4:
            st.metric(
                "Tempo Médio de Permanência",
                f"{metricas['periodo2']['tempo_medio_permanencia']:.1f} min",
                f"{metricas['variacoes']['tempo_medio_permanencia']:.1f}%",
                delta_color="inverse"  # Inversão: negativo é bom para redução de tempo
            )
        
        # Exibir gráficos comparativos
        st.subheader("Comparativo entre Períodos")
        fig = criar_graficos_comparativos(dados, filtros, metricas)
        st.plotly_chart(fig, use_container_width=True)
        
        # Visão consolidada e insights
        st.subheader("📊 Principais Insights")
        with st.expander("Ver insights", expanded=True):
            st.write("#### Resumo do Período")
            
            # Total de atendimentos
            var_total = metricas['variacoes']['total_atendimentos']
            if var_total > 0:
                st.write(f"- **Aumento de {var_total:.1f}%** no volume de atendimentos")
            else:
                st.write(f"- **Redução de {abs(var_total):.1f}%** no volume de atendimentos")
            
            # Tempo médio de atendimento
            var_atend = metricas['variacoes']['tempo_medio_atendimento']
            if var_atend < 0:
                st.write(f"- **Melhoria de {abs(var_atend):.1f}%** no tempo médio de atendimento")
            else:
                st.write(f"- **Aumento de {var_atend:.1f}%** no tempo médio de atendimento")
            
            # Tempo médio de espera
            var_espera = metricas['variacoes']['tempo_medio_espera']
            if var_espera < 0:
                st.write(f"- **Redução de {abs(var_espera):.1f}%** no tempo médio de espera")
            else:
                st.write(f"- **Aumento de {var_espera:.1f}%** no tempo médio de espera")
            
            # Tempo médio de permanência
            var_perm = metricas['variacoes']['tempo_medio_permanencia']
            if var_perm < 0:
                st.write(f"- **Redução de {abs(var_perm):.1f}%** no tempo médio de permanência")
            else:
                st.write(f"- **Aumento de {var_perm:.1f}%** no tempo médio de permanência")
            
            # Clientes e operações
            st.write(f"\n**Total de clientes atendidos:** {metricas['periodo2']['qtd_clientes']}")
            st.write(f"**Tipos de operações realizadas:** {metricas['periodo2']['qtd_operacoes']}")
    
    except Exception as e:
        st.error(f"Erro ao gerar a visão geral: {str(e)}")
        st.write("\n=== Debug de Erro ===")
        st.write(f"Tipo do erro: {type(e).__name__}")
        st.write(f"Descrição: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        st.write("=== Fim do Debug de Erro ===")
