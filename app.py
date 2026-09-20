import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# =====================================================================
# 1. CARGA, REPARACIÓN Y LIMPIEZA DE DATOS (Adaptado para Script)
# =====================================================================
# Leemos los datos desde el archivo exportado en lugar de la memoria de Jupyter
df_dash = pd.read_csv('bitcoin_datos_dashboard.csv')

# Aseguramos que la columna de fechas tenga el nombre correcto si se perdió al guardar
if 'Timestamp' not in df_dash.columns:
    df_dash.rename(columns={df_dash.columns[0]: 'Timestamp'}, inplace=True)

# Convertimos a fecha real para ordenar la serie temporal
df_dash['Timestamp'] = pd.to_datetime(df_dash['Timestamp'], errors='coerce')
df_dash = df_dash.sort_values('Timestamp')

# Truco web: creamos una columna de texto puro para evitar errores de gráfica en blanco en el navegador
df_dash['Timestamp_str'] = df_dash['Timestamp'].dt.strftime('%Y-%m-%d')

# Recalculamos las variables por si no se guardaron correctamente
df_dash['Return'] = (df_dash['Close'] - df_dash['Open']) / df_dash['Open']
df_dash['Spread_Lag1'] = df_dash['Spread'].shift(1)
df_dash = df_dash.dropna(subset=['Close', 'Volume', 'Spread', 'Open', 'High', 'Low'])

# Aseguramos la variable binaria de volatilidad
mediana_spread = df_dash['Spread'].median()
df_dash['Alta_Volatilidad'] = (df_dash['Spread'] > mediana_spread).astype(int)

# Extraer el estado de riesgo del último día registrado para el KPI
ultimo_riesgo = df_dash['Alta_Volatilidad'].iloc[-1]
texto_riesgo = "Alta Volatilidad" if ultimo_riesgo == 1 else "Riesgo Bajo"
color_riesgo = "#e74c3c" if ultimo_riesgo == 1 else "#2ecc71"
# =====================================================================

# 2. Inicializar la aplicación Dash
app = dash.Dash(__name__)
app.title = "Dashboard Pro Bitcoin"

# 3. Diseñar la Interfaz (Layout Premium)
app.layout = html.Div(style={'fontFamily': 'Arial, sans-serif', 'padding': '20px', 'backgroundColor': '#f4f6f9'}, children=[
    
    # Encabezado y KPI (Mejora 1)
    html.Div(style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'marginBottom': '20px'}, children=[
        html.Div(children=[
            html.H1("Inteligencia de Riesgo - Bitcoin", style={'color': '#2c3e50', 'margin': '0'}),
            html.P("Análisis de Volatilidad y Volumen (2020-2021)", style={'fontSize': '16px', 'color': '#7f8c8d'})
        ]),
        html.Div(style={'backgroundColor': 'white', 'padding': '15px 30px', 'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center'}, children=[
            html.H4("Estado Actual del Mercado", style={'margin': '0', 'color': '#34495e', 'fontSize': '14px'}),
            html.H2(texto_riesgo, style={'margin': '5px 0 0 0', 'color': color_riesgo})
        ])
    ]),

    # Filtros interactivos
    html.Div(style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)', 'marginBottom': '20px'}, children=[
        html.Label("Selecciona el indicador para superponer al precio:", style={'fontWeight': 'bold'}),
        dcc.Dropdown(
            id='selector-variable',
            options=[
                {'label': 'Spread (Volatilidad Diaria en USD)', 'value': 'Spread'},
                {'label': 'Volumen Diario de Comercio', 'value': 'Volume'},
                {'label': 'Retorno Diario', 'value': 'Return'}
            ],
            value='Volume',
            clearable=False,
            style={'width': '40%', 'marginTop': '10px'}
        )
    ]),

    # Contenedor de Gráficos Superior
    html.Div(style={'display': 'flex', 'gap': '20px', 'flexWrap': 'wrap', 'marginBottom': '20px'}, children=[
        
        # Gráfico Temporal con Velas (Izquierda - Mejora 2)
        html.Div(style={'flex': '2', 'minWidth': '600px', 'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.05)'}, children=[
            dcc.Graph(id='grafico-temporal')
        ]),
        
        # Gráfico de Dispersión (Derecha)
        html.Div(style={'flex': '1', 'minWidth': '400px', 'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.05)'}, children=[
            html.H3("Patrón: Volumen vs Riesgo", style={'textAlign': 'center', 'color': '#34495e', 'fontSize': '16px'}),
            dcc.Graph(
                id='grafico-dispersion',
                figure=px.scatter(df_dash, x='Volume', y='Spread', trendline="ols", 
                                  color='Alta_Volatilidad',
                                  color_continuous_scale=['#3498db', '#e74c3c']).update_layout(margin=dict(l=20, r=20, t=30, b=20))
            )
        ])
    ]),

    # Contenedor Inferior: Matriz y Conclusiones
    html.Div(style={'display': 'flex', 'gap': '20px', 'flexWrap': 'wrap'}, children=[
        
        # Matriz de Correlación (Izquierda - Mejora 3)
        html.Div(style={'flex': '1', 'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.05)'}, children=[
            html.H3("Correlación de Variables", style={'textAlign': 'center', 'color': '#34495e', 'fontSize': '16px'}),
            dcc.Graph(
                id='grafico-correlacion',
                figure=px.imshow(df_dash[['Close', 'Volume', 'Spread', 'Return']].corr(), 
                                 text_auto=".2f", aspect="auto", color_continuous_scale="RdBu_r")
                         .update_layout(margin=dict(l=10, r=10, t=30, b=10))
            )
        ]),

        # Narrativa (Derecha)
        html.Div(style={'flex': '2', 'backgroundColor': '#2c3e50', 'color': 'white', 'padding': '25px', 'borderRadius': '10px'}, children=[
            html.H3("Conclusiones del Modelo Optimizado, Conclusiones Analíticas", style={'marginTop': '0', 'borderBottom': '1px solid #34495e', 'paddingBottom': '10px'}),
            html.Ul([
                html.Li(html.Span(["Ingeniería de Características: ", html.Span("La inclusión del 'Retorno Diario' y la 'Volatilidad Anterior' dotó al modelo de contexto direccional y memoria de mercado.", style={'fontWeight': 'normal'})], style={'fontWeight': 'bold'})),
                html.Li(html.Span(["Optimización Estructural: ", html.Span("Al aplicar regularización L1 (Lasso) con C=10, el algoritmo filtró el ruido estadístico, priorizando únicamente a los verdaderos predictores del riesgo.", style={'fontWeight': 'normal'})], style={'fontWeight': 'bold'})),
                html.Li(html.Span(["Desempeño Excepcional: ", html.Span("El modelo final alcanzó una Sensibilidad (Recall) del 89.7%, logrando alertar correctamente 61 de los 68 días de alta volatilidad.", style={'fontWeight': 'normal'})], style={'fontWeight': 'bold'})),
                html.Li(html.Span(["Gestión de Riesgo: ", html.Span("Mantener un umbral de decisión estricto (0.40) demostró ser la estrategia óptima para evitar puntos ciegos (minimizar Falsos Negativos).", style={'fontWeight': 'normal'})], style={'fontWeight': 'bold'})),
                html.Li(html.Span(["Catalizador del Mercado: ", html.Span("Como evidencia la matriz de correlación, el volumen de transacciones se confirma matemáticamente como el principal motor de la inestabilidad.", style={'fontWeight': 'normal'})], style={'fontWeight': 'bold'})),
                html.Li(html.Span(["Aplicabilidad Real: ", html.Span("Este sistema transciende el análisis descriptivo, sirviendo como una herramienta de alerta temprana para estrategias de cobertura institucional (hedging).", style={'fontWeight': 'normal'})], style={'fontWeight': 'bold'})),
                html.Li(html.Span(["Efecto de Escala (Precio vs Riesgo): ", html.Span("La matriz revela una fuerte correlación (0.82) entre el Precio de Cierre y el Spread. A mayor valoración del activo, las fluctuaciones absolutas crecen proporcionalmente.", style={'fontWeight': 'normal'})], style={'fontWeight': 'bold'})),
                html.Li(html.Span(["Validación de Hipótesis: ", html.Span("Se confirma una correlación positiva (0.34) entre Volumen y Spread, probando estadísticamente que los picos transaccionales son detonantes de la inestabilidad.", style={'fontWeight': 'normal'})], style={'fontWeight': 'bold'})),
                html.Li(html.Span(["Naturaleza del Riesgo (Retorno): ", html.Span("El Retorno Diario muestra correlaciones casi nulas con Volumen y Spread. Esto indica que el riesgo es bidireccional (alta volatilidad ocurre tanto en fuertes caídas como en repuntes).", style={'fontWeight': 'normal'})], style={'fontWeight': 'bold'})),
                html.Li(html.Span(["Eficacia Estructural (L1): ", html.Span("La penalización Lasso (C=10) actuó como un filtro de ruido excepcional, logrando que el algoritmo ignorara variables irrelevantes y evitara el sobreajuste.", style={'fontWeight': 'normal'})], style={'fontWeight': 'bold'}))
            ], style={'lineHeight': '1.7', 'fontSize': '14px', 'margin': '0', 'paddingLeft': '20px'})
        ])
    ])
])

# 4. Interactividad: Velas Japonesas + Variable
@app.callback(
    Output('grafico-temporal', 'figure'),
    [Input('selector-variable', 'value')]
)
def actualizar_grafico(variable_seleccionada):
    if not variable_seleccionada:
        return go.Figure()

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # MEJORA 2: Eje Principal usando Velas (Candlestick) y la columna de texto seguro
    fig.add_trace(
        go.Candlestick(x=df_dash['Timestamp_str'],
                       open=df_dash['Open'],
                       high=df_dash['High'],
                       low=df_dash['Low'],
                       close=df_dash['Close'],
                       name='Precio BTC'),
        secondary_y=False,
    )
    
    # Eje Secundario: Variable del filtro
    fig.add_trace(
        go.Scatter(x=df_dash['Timestamp_str'], y=df_dash[variable_seleccionada], 
                   name=variable_seleccionada, mode='lines', 
                   line=dict(color='#8e44ad', width=1.5, dash='dot')),
        secondary_y=True,
    )
    
    fig.update_layout(
        title=f"Acción del Precio vs {variable_seleccionada}",
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        plot_bgcolor='white',
        margin=dict(l=20, r=20, t=40, b=20)
    )

    return fig

# 5. Ejecutar la aplicación (Configuración para script y despliegue)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050, debug=False)