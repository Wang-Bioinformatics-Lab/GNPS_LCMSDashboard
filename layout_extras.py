# Dash imports

import dash
from dash import dcc
import dash_bootstrap_components as dbc
from dash import html
import dash_table
from dash.dependencies import Input, Output, State
import dash_daq as daq

# Plotly Imports
import plotly.express as px
import plotly.graph_objects as go

EXTRAS_PANEL = [
    dbc.CardHeader(html.H5("LCMS Extras Options")),
    dbc.CardBody(
        [
            dbc.Row([
                dbc.Col(
                    dbc.InputGroup(
                        [
                            dbc.InputGroupText("Extras - Metadata Text"),
                            dbc.Textarea(id='extras_metadata_text', placeholder=""),
                        ],
                        className="mb-3",
                    ),
                )
            ]),
            dbc.Row([
                dbc.Col(
                    dbc.InputGroup(
                        [
                            dbc.InputGroupText("Metadata Column", style={"margin-right":"20px"}),
                            dcc.Dropdown(
                                id='extras_metadata_column',
                                options=[
                                    {'label': 'None', 'value': ''},
                                ],
                                searchable=False,
                                clearable=False,
                                value="",
                                style={
                                    "width":"60%"
                                }
                            )
                        ],
                        className="mb-3",
                    ),
                ),
                dbc.Col(
                    
                )
            ]),
        ]
    )

]