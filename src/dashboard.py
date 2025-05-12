import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import joblib
import pandas as pd
from dash.exceptions import PreventUpdate
from flask_caching import Cache
import plotly.graph_objs as go
import plotly.express as px

# Initialize Dash app with Bootstrap theme
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}]
)

# Initialize cache
cache = Cache(app.server, config={'CACHE_TYPE': 'filesystem', 'CACHE_DIR': 'cache'})

# Load model and data
try:
    model = joblib.load('../models/outbreak_model.pkl')
    data = pd.read_csv('../data/processed/merged_data.csv')
except FileNotFoundError as e:
    print(f"Error loading files: {e}")
    raise PreventUpdate

# Custom CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Disease Outbreak Prediction</title>
        {%favicon%}
        {%css%}
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');
            
            body {
                font-family: 'Poppins', sans-serif;
                background-color: #f8f9fa;
            }
            
            .input-card {
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                transition: transform 0.2s;
            }
            
            .input-card:hover {
                transform: translateY(-5px);
            }
            
            .prediction-card {
                background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
                border-radius: 15px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            
            .custom-input {
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 8px;
                transition: all 0.3s;
            }
            
            .custom-input:focus {
                border-color: #2c3e50;
                box-shadow: 0 0 0 0.2rem rgba(44, 62, 80, 0.25);
            }
            
            .predict-button {
                background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
                border: none;
                border-radius: 8px;
                padding: 12px;
                color: white;
                font-weight: 600;
                transition: all 0.3s;
            }
            
            .predict-button:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# App layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1(
                "Disease Outbreak Prediction Dashboard",
                className="text-center mb-4 mt-4",
                style={'color': '#2c3e50', 'font-weight': '600'}
            )
        ])
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Input Parameters", className="card-title mb-4"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("New Cases", html_for="new-cases"),
                            dbc.Input(
                                id="new-cases",
                                type="number",
                                value=120,
                                className="custom-input mb-3"
                            )
                        ], md=6),
                        dbc.Col([
                            dbc.Label("Humidity (%)", html_for="humidity"),
                            dbc.Input(
                                id="humidity",
                                type="number",
                                value=85,
                                className="custom-input mb-3"
                            )
                        ], md=6)
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Temperature (°C)", html_for="temperature"),
                            dbc.Input(
                                id="temperature",
                                type="number",
                                value=28,
                                className="custom-input mb-3"
                            )
                        ], md=6),
                        dbc.Col([
                            dbc.Label("Rainfall (mm)", html_for="rainfall"),
                            dbc.Input(
                                id="rainfall",
                                type="number",
                                value=12.5,
                                className="custom-input mb-3"
                            )
                        ], md=6)
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Population Density", html_for="population-density"),
                            dbc.Input(
                                id="population-density",
                                type="number",
                                value=20000,
                                className="custom-input mb-4"
                            )
                        ])
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Button(
                                "Predict Outbreak Risk",
                                id="predict-button",
                                className="predict-button w-100"
                            )
                        ])
                    ])
                ])
            ], className="input-card mb-4")
        ], md=6),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Prediction Results", className="card-title mb-4"),
                    html.Div([
                        html.H3(
                            id="prediction-output",
                            className="text-center mb-4"
                        ),
                        dcc.Graph(
                            id="prediction-graph",
                            config={'displayModeBar': False}
                        )
                    ], className="prediction-results")
                ])
            ], className="prediction-card")
        ], md=6)
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Historical Data Trends", className="card-title mb-4"),
                    dcc.Graph(
                        id="historical-trend",
                        figure=px.line(
                            data.tail(30),
                            x=data.index[-30:],
                            y='NewCases',
                            title='Recent Disease Cases Trend'
                        ).update_layout(
                            plot_bgcolor='white',
                            paper_bgcolor='white'
                        )
                    )
                ])
            ], className="mb-4")
        ])
    ])
], fluid=True, className="px-4")

@app.callback(
    [Output('prediction-output', 'children'),
     Output('prediction-graph', 'figure'),
     Output('prediction-output', 'style')],
    Input('predict-button', 'n_clicks'),
    [State('new-cases', 'value'),
     State('humidity', 'value'),
     State('population-density', 'value'),
     State('temperature', 'value'),
     State('rainfall', 'value')],
    prevent_initial_call=True
)
@cache.memoize(timeout=300)
def predict_outbreak(n_clicks, new_cases, humidity, population_density, temperature, rainfall):
    if None in [new_cases, humidity, population_density, temperature, rainfall]:
        raise PreventUpdate
    
    input_data = {
        'NewCases': new_cases,
        'Humidity_x': humidity,
        'PopulationDensity': population_density,
        'Temperature': temperature,
        'Rainfall': rainfall
    }
    input_df = pd.DataFrame([input_data])
    
    try:
        prediction = model.predict(input_df)[0]
        prediction_proba = model.predict_proba(input_df)[0]
        
        # Create gauge chart for risk probability
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=prediction_proba[1] * 100,
            title={'text': "Risk Probability"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 30], 'color': "lightgreen"},
                    {'range': [30, 70], 'color': "yellow"},
                    {'range': [70, 100], 'color': "salmon"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 70
                }
            }
        ))
        
        fig.update_layout(
            paper_bgcolor="white",
            font={'color': "#2c3e50", 'family': "Poppins"}
        )
        
        # Style based on prediction
        style = {
            'color': '#d35400' if prediction == 1 else '#27ae60',
            'font-weight': '600'
        }
        
        result_text = "High Risk" if prediction == 1 else "Low Risk"
        return f"Prediction: {result_text}", fig, style
        
    except Exception as e:
        return f"Error: {str(e)}", {}, {'color': 'red'}

if __name__ == "__main__":
    app.run_server(debug=False, host="0.0.0.0", port=8000)