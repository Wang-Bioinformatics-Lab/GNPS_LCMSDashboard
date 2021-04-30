# Dash imports

import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output, State
import dash_daq as daq

# Plotly Imports
import plotly.express as px
import plotly.graph_objects as go


FEATUREFINDING_RESULTS_CARD = [
    dbc.CardHeader(html.H5("Feature Finding Results")),
    dbc.CardBody(
        [
            dcc.Loading(
                id="feature-finding-table",
                children=[html.Div([html.Div(id="loading-output-100")])],
                type="default",
            ),
        ]
    )
]