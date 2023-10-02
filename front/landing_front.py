import dash
from dash.dependencies import Input, Output
from dash import dcc
from dash import html
import plotly.express as px
from plotly import graph_objects as go

import pandas as pd

# Data and plot defintions
wl_processed = pd.read_excel('../data/wl_processed.xlsx', index_col=0, parse_dates=['date'])
wl_processed['Ratio A/C'] = wl_processed['REDI 0.28']/wl_processed['REDI 0.07']
fig_wl = px.bar(wl_processed, x='date', y='sRPE')
fig_redi = px.line(wl_processed, x='date', y=['REDI 0.07', 'REDI 0.28'])
fig_ratio = px.line(wl_processed, x='date', y='Ratio A/C')

# dash app definition
app = dash.Dash(__name__)

app.layout = html.Div(
    children=[html.H1(children=["Trivial Workloads"]),
              dcc.Graph(id='sRPE', figure=fig_wl),
              dcc.Graph(id='ratio', figure=fig_ratio),
              dcc.Graph(id='REDI', figure=fig_redi)])

if __name__ == "__main__":
    app.run_server(debug=True, use_reloader=False)
    