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
                    dbc.Col(
                            dbc.InputGroup(
                                [
                                    dbc.InputGroupAddon("XIC Peptide", addon_type="prepend"),
                                    dbc.Input(id='xic_peptide', placeholder="Enter Peptide to XIC", value=""),
                                ],
                                className="mb-3",
                            ),
                        ),
                ]),
                html.Hr(),
                dbc.Row([
                    dbc.Col([
                        html.H5("XIC Presets"),
                        dcc.Dropdown(
                            id='xic_presets',
                            options=[
                                {'label': 'Amino Acids', 'value': 'Ala=90.054946;Arg=175.118946;Asn=133.060766;Asp=134.044776;Cys=122.027026;Glu=148.060426;Gln=147.076416;Gly=76.039296;His=156.076746;Ile=132.101896;Leu=132.101896;Lys=147.112796;Met=150.058326;Phe=166.086246;Pro=116.070596;Ser=106.049866;Thr=120.065516;Trp=205.097146;Tyr=182.081166;Val=118.086246'},
                            ],
                            searchable=True,
                            clearable=True,
                            style={
                                "width":"100%"
                            }
                        ),
                    ]),
                ]),
                html.Hr(),
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