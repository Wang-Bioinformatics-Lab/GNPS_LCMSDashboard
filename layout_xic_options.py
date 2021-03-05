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

ADVANCED_XIC_MODAL = [
    dbc.Modal(
        [
            dbc.ModalHeader("XIC Options"),
            dbc.ModalBody([
                dbc.Row([
                    dbc.Col([
                        html.H5("mzML Chromatograms"),
                        dcc.Dropdown(
                            id='chromatogram_options',
                            options=[],
                            searchable=False,
                            clearable=True,
                            multi=True,
                            value=[],
                            style={
                                "width":"100%"
                            }
                        ),
                    ]),
                ])
            ]),
            dbc.ModalFooter(
                dbc.Button("Close", id="advanced_xic_modal_close", className="ml-auto")
            ),
        ],
        id="advanced_xic_modal",
        size="xl",
    ),
]