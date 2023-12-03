import json
import os

import dash
from dash import dcc, html, Input, Output, State, callback
import plotly.express as px
from plotly import graph_objects as go
from plotly.subplots import make_subplots
from strava_api.strava_reader import StravaReader
from training_loads.simple_loads import redi_df, rolling_acwr, filter_and_aggregate_wl

import pandas as pd



# Data and plot defintions
wl_processed = pd.read_excel('../data/wl_processed.xlsx', index_col=0, parse_dates=['date'])
wl_processed = wl_processed.sort_values(by='date', ascending=True)

fig_wl = px.bar(wl_processed, x='date', y='sRPE')
fig_redi = px.line(wl_processed, x='date', y=['REDI 0.07', 'REDI 0.28'])
fig_ratio = px.line(wl_processed.dropna(subset=['rolling ACWR']), x='date', y='rolling ACWR')
fig_ratio.add_hrect(y0=1.5, y1=3, line_width=0, fillcolor="red", opacity=0.2)
fig_ratio.add_hrect(y0=-1, y1=0.8, line_width=0, fillcolor="red", opacity=0.2)
fig_ratio.update_yaxes({"range": [0., 2]})

main_fig = make_subplots(specs=[[{"secondary_y": True}]])

main_fig.add_trace(
    go.Bar(x=wl_processed["date"],
           y=wl_processed['sRPE'],
           name='sRPE',
           ),
    secondary_y=False,
)

main_fig.add_trace(
    go.Scatter(x=wl_processed['date'],
               y=wl_processed['REDI 0.07'],
               mode='lines',
               name='REDI 0.07'
               ),
    secondary_y=True,
)
main_fig.add_trace(
    go.Scatter(x=wl_processed['date'],
               y=wl_processed['REDI 0.28'],
               mode='lines',
               name='REDI 0.28'
               ),
    secondary_y=True,
)

main_fig.update_yaxes(title_text="sRPE", secondary_y=False)
main_fig.update_yaxes(title_text="REDI", secondary_y=True)
main_fig.update_xaxes(title_text='date', range=[wl_processed.dropna(subset=['rolling ACWR'])['date'].min(),
                                                wl_processed.dropna(subset=['rolling ACWR'])['date'].max()
                                                ])


# dash app definition
app = dash.Dash(__name__)


app.layout = html.Div(
    children=[html.H1(children=["Trivial Workloads"],
                      style={"textAlign": "center"}
                      ),
              html.Button('Refresh', id='refresh-button', n_clicks=0),
              html.Div(id='is-fresh', children='Not fresh'),
              html.Div(
                  children=[dcc.Graph(id='sRPE', figure=main_fig),
                            dcc.Graph(id='ratio', figure=fig_ratio),
                            ])
              ])
@callback(Output('is-fresh', 'children'),
          Input('refresh-button', 'n_clicks'),
          prevent_initial_call=True
          )
def refresh_fun(n_clicks):
    with open('strava_api/config_strava.json', 'r') as f:
        config_dict = json.load(f)
    strava_reader = StravaReader(config_dict)
    old_raw_data = pd.read_excel('../data/strava.xlsx',
                                 index_col=0,
                                 parse_dates=['date'])
    new_raw_data = strava_reader.update_data(old_raw_data)
    os.rename('../data/strava.xlsx', '../data/strava_old.xlsx')
    new_raw_data.to_excel('../data/strava.xlsx')
    df_wl = filter_and_aggregate_wl(df, sports=['Run', 'Ride'], load_type='sRPE')
    redi_series_007 = redi_df(df_wl, lambda_const=0.07, N=None, col_workload='sRPE')
    redi_series_028 = redi_df(df_wl, lambda_const=0.28, N=None, col_workload='sRPE')
    rolling_acwr_df = rolling_acwr(df_wl, acute_n=7, chronic_n=28, load_type='sRPE')
    df_proc = redi_series_007.merge(redi_series_028, on='date')
    df_proc = df_proc.merge(df_wl, on='date', how='left')
    df_proc = df_proc.merge(rolling_acwr_df, on='date', how='left')
    df_proc.to_excel("../data/wl_processed.xlsx")
    return 'Real fresh'

if __name__ == "__main__":
    app.run_server(debug=True, use_reloader=False)
    