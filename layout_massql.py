# Dash imports

import dash
from dash import dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output, State
import dash_daq as daq
import dash_uploader as du

# Plotly Imports
import plotly.express as px
import plotly.graph_objects as go

MASSSPEC_QUERY_PANEL = [
    dbc.CardHeader(html.H5("MassQL Query Options")),
    dbc.CardBody(
        [   
            dbc.Row([
                dbc.Col(
                    html.P(
                        "Welcome to MassQL. Please read the full documentation. Queries here are meant to be simple and fast. If you want to do many files or complex queries, please use the GNPS Workflow!"
                    )
                )
            ]),
            dbc.Row([
                dbc.Col(
                    dbc.InputGroup(
                        [
                            dbc.InputGroupText("MassQL"),
                            dbc.Textarea(id='massql_statement', placeholder="MassQL Query", value="QUERY scaninfo(MS2DATA)", rows=8),
                        ],
                        className="mb-3",
                    )
                ),
            ]),
            dbc.Row([
                dbc.Col(
                    dbc.InputGroup(
                        [
                            dbc.Button("Execute Query", color="primary", className="mr-1", id="run_massql_query_button"),
                        ],
                        className="mb-3",
                    )
                ),
            ]),
        ]
    )
]