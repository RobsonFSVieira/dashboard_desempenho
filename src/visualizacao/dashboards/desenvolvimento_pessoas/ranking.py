import pandas as pd
import plotly.graph_objects as go
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

def create_ranking_layout(app):
    # Dados simulados para os filtros
    departamentos = ['Vendas', 'Marketing', 'TI', 'RH']
    cargos = ['Analista', 'Gerente', 'Coordenador', 'Assistente']

    layout = dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H3("Ranking de Desempenho", className="text-center mb-4"),
                # Filtros
                dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("Departamento:"),
                                dcc.Dropdown(
                                    id='dept-filter',
                                    options=[{'label': d, 'value': d} for d in departamentos],
                                    value=departamentos[0],  # valor inicial
                                    multi=True
                                )
                            ], width=4),
                            dbc.Col([
                                html.Label("Cargo:"),
                                dcc.Dropdown(
                                    id='cargo-filter',
                                    options=[{'label': c, 'value': c} for c in cargos],
                                    value=cargos[0],  # valor inicial
                                    multi=True
                                )
                            ], width=4),
                            dbc.Col([
                                html.Label("Indicador:"),
                                dcc.Dropdown(
                                    id='indicador-filter',
                                    options=[
                                        {'label': 'Produtividade', 'value': 'prod'},
                                        {'label': 'Qualidade', 'value': 'qual'},
                                        {'label': 'Geral', 'value': 'geral'}
                                    ],
                                    value='geral'  # valor inicial
                                )
                            ], width=4)
                        ])
                    ])
                ], className="mb-4"),
                
                # Gráfico de Comparação
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(id='ranking-chart')
                    ])
                ], className="mb-4"),
                
                # Seção de Insights
                dbc.Card([
                    dbc.CardHeader(html.H5("Análise Detalhada", className="mb-0")),
                    dbc.CardBody([
                        html.Div(id='insights-content')
                    ])
                ])
            ], width=12)
        ])
    ], fluid=True)
    
    @app.callback(
        [Output('ranking-chart', 'figure'),
         Output('insights-content', 'children')],
        [Input('dept-filter', 'value'),
         Input('cargo-filter', 'value'),
         Input('indicador-filter', 'value')]
    )
    def update_ranking(dept, cargo, indicador):
        # Simular dados baseados nos filtros selecionados
        df = pd.DataFrame({
            'usuario': ['Ana Silva', 'Carlos Santos', 'Maria Oliveira', 'João Pedro', 'Paula Costa'],
            'departamento': ['Vendas', 'Marketing', 'Vendas', 'TI', 'RH'],
            'cargo': ['Analista', 'Gerente', 'Coordenador', 'Analista', 'Gerente'],
            'periodo_1': [80, 65, 90, 70, 85],
            'periodo_2': [95, 85, 85, 75, 92]
        })
        
        # Aplicar filtros se selecionados
        if dept:
            df = df[df['departamento'].isin([dept] if isinstance(dept, str) else dept)]
        if cargo:
            df = df[df['cargo'].isin([cargo] if isinstance(cargo, str) else cargo)]
            
        # Criar gráfico
        fig = go.Figure()
        df = df.sort_values('periodo_2', ascending=False)
        
        # Adicionar barras
        fig.add_trace(go.Bar(
            name='Período 1',
            x=df['usuario'],
            y=df['periodo_1'],
            marker_color='lightgray'
        ))
        
        fig.add_trace(go.Bar(
            name='Período 2',
            x=df['usuario'],
            y=df['periodo_2'],
            marker_color='royalblue'
        ))
        
        # Adicionar diferenças percentuais
        for i, row in df.iterrows():
            diff_pct = ((row['periodo_2'] - row['periodo_1']) / row['periodo_1'] * 100)
            color = 'green' if diff_pct >= 0 else 'red'
            fig.add_annotation(
                x=row['usuario'],
                y=max(row['periodo_1'], row['periodo_2']),
                text=f"{diff_pct:.1f}%",
                showarrow=False,
                font=dict(color=color),
                yshift=10
            )
        
        fig.update_layout(
            barmode='group',
            title=f"Comparação de Desempenho entre Períodos - {indicador.upper() if indicador else 'GERAL'}",
            xaxis_title="Colaboradores",
            yaxis_title="Pontuação de Desempenho",
            showlegend=True,
            height=500
        )
        
        # Gerar insights mais detalhados
        insights = [
            html.H5("Principais Observações:", className="mb-3"),
            html.Ul([
                html.Li([
                    html.Strong("Maior crescimento: "), 
                    f"{df['usuario'].iloc[0]} com aumento de {((df['periodo_2'].iloc[0] - df['periodo_1'].iloc[0]) / df['periodo_1'].iloc[0] * 100):.1f}%"
                ]),
                html.Li([
                    html.Strong("Top 3 performers no período atual:")
                ]),
                html.Ul([
                    html.Li(f"{df['usuario'].iloc[i]} - {df['periodo_2'].iloc[i]:.1f} pontos ({df['cargo'].iloc[i]} em {df['departamento'].iloc[i]})")
                    for i in range(min(3, len(df)))
                ]),
                html.Li([
                    html.Strong("Média geral: "), 
                    f"Período 1: {df['periodo_1'].mean():.1f} | Período 2: {df['periodo_2'].mean():.1f}"
                ]),
                html.Li([
                    html.Strong("Variação média: "), 
                    f"{((df['periodo_2'].mean() - df['periodo_1'].mean()) / df['periodo_1'].mean() * 100):.1f}%"
                ])
            ])
        ]
        
        return fig, insights
    
    return layout
