import pandas as pd
import plotly.graph_objects as go
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

def create_ranking_layout(app):
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
                                dcc.Dropdown(id='dept-filter', multi=True)
                            ], width=4),
                            dbc.Col([
                                html.Label("Cargo:"),
                                dcc.Dropdown(id='cargo-filter', multi=True)
                            ], width=4),
                            dbc.Col([
                                html.Label("Indicador:"),
                                dcc.Dropdown(id='indicador-filter',
                                           options=[
                                               {'label': 'Produtividade', 'value': 'prod'},
                                               {'label': 'Qualidade', 'value': 'qual'},
                                               {'label': 'Geral', 'value': 'geral'}
                                           ])
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
                    dbc.CardHeader("Análise Detalhada"),
                    dbc.CardBody([
                        html.Div(id='insights-content')
                    ])
                ])
            ])
        ])
    ])
    
    @app.callback(
        [Output('ranking-chart', 'figure'),
         Output('insights-content', 'children')],
        [Input('dept-filter', 'value'),
         Input('cargo-filter', 'value'),
         Input('indicador-filter', 'value')]
    )
    def update_ranking(dept, cargo, indicador):
        # Função para gerar o gráfico de comparação
        def create_comparison_chart(df):
            fig = go.Figure()
            
            # Ordenar por período 2 (decrescente)
            df = df.sort_values('periodo_2', ascending=False)
            
            # Adicionar barras para período 1
            fig.add_trace(go.Bar(
                name='Período 1',
                x=df['usuario'],
                y=df['periodo_1'],
                marker_color='lightgray'
            ))
            
            # Adicionar barras para período 2
            fig.add_trace(go.Bar(
                name='Período 2',
                x=df['usuario'],
                y=df['periodo_2'],
                marker_color='royalblue'
            ))
            
            # Calcular e adicionar as diferenças percentuais
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
                title="Comparação de Desempenho entre Períodos",
                xaxis_title="Usuários",
                yaxis_title="Desempenho",
                showlegend=True
            )
            
            return fig
        
        # Gerar insights baseados nos dados
        def generate_insights(df):
            insights = [
                html.H5("Principais Observações:"),
                html.Ul([
                    html.Li(f"Maior crescimento: {df['usuario'].iloc[0]} (+{((df['periodo_2'].iloc[0] - df['periodo_1'].iloc[0]) / df['periodo_1'].iloc[0] * 100):.1f}%)"),
                    html.Li("Top 3 performers no período atual:"),
                    html.Ul([
                        html.Li(f"{df['usuario'].iloc[i]} - {df['periodo_2'].iloc[i]:.1f}")
                        for i in range(3)
                    ])
                ])
            ]
            return insights
        
        # Aqui você deve implementar a lógica para filtrar os dados
        # baseado nos filtros selecionados (dept, cargo, indicador)
        # Por enquanto, retornamos dados simulados
        df = pd.DataFrame({
            'usuario': ['User A', 'User B', 'User C', 'User D'],
            'periodo_1': [80, 65, 90, 70],
            'periodo_2': [95, 85, 85, 75]
        })
        
        figure = create_comparison_chart(df)
        insights = generate_insights(df)
        
        return figure, insights
    
    return layout
