# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_table
import plotly.express as px
from dash.dependencies import Input, Output
import os
from zipfile import ZipFile
import urllib.parse
from flask import Flask, send_from_directory

import pandas as pd
import requests
import uuid

server = Flask(__name__)
app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

NAVBAR = dbc.Navbar(
    children=[
        dbc.NavbarBrand(
            html.Img(src="https://gnps-cytoscape.ucsd.edu/static/img/GNPS_logo.png", width="120px"),
            href="https://gnps.ucsd.edu"
        ),
        dbc.Nav(
            [
                dbc.NavItem(dbc.NavLink("GNPS Classical Networking Group Comparison Dashboard", href="#")),
            ],
        navbar=True)
    ],
    color="light",
    dark=False,
    sticky="top",
)

DASHBOARD = [
    dbc.CardHeader(html.H5("GNPS Classical Networking Group Comparison Dashboard")),
    dbc.CardBody(
        [   
            dcc.Location(id='url', refresh=False),

            html.Div(id='version', children="Version - Release_1"),

            html.Br(),
            html.H3(children='GNPS USI'),
            dbc.Textarea(className="mb-3", id='gnps_file', placeholder="Enter GNPS File USI"),
            html.Br(),
            dcc.Loading(
                id="output",
                children=[html.Div([html.Div(id="loading-output-4")])],
                type="default",
            )

        ]
    )
]

BODY = dbc.Container(
    [
        dbc.Row([dbc.Col(dbc.Card(DASHBOARD)),], style={"marginTop": 30}),
    ],
    className="mt-12",
)

app.layout = html.Div(children=[NAVBAR, BODY])


@app.callback(Output('gnps_file', 'value'),
              [Input('url', 'pathname')])
def determine_task(pathname):
    # Otherwise, lets use the url
    if pathname is not None and len(pathname) > 1:
        return pathname[1:]
    else:
        return dash.no_update


@app.callback(Output('output', 'children'),
              [Input('gnps_file', 'value')])
def draw_file(usi):
    # Test: mzspec:GNPSTASK-ea65c1b165054c3492974b8e4f0bf675:f.mwang87/data/Yao_Streptomyces/roseosporus/0518_s_BuOH.mzXML:scan:171
    filename = usi.split(":")[2]
    task = usi.split(":")[1].split("-")[1]
    return filename




if __name__ == "__main__":
    app.run_server(debug=True, port=5000, host="0.0.0.0")
