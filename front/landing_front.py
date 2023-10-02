import dash
from dash import dcc
from dash import html
import plotly.express as px
from plotly import graph_objects as go
from plotly.subplots import make_subplots

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
              html.Div(
                  children=[dcc.Graph(id='sRPE', figure=main_fig),
                            dcc.Graph(id='ratio', figure=fig_ratio),
                            ])
              ])

if __name__ == "__main__":
    app.run_server(debug=True, use_reloader=False)
    