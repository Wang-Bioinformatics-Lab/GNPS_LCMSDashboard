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


FEATURE_FINDING_PANEL = [
    dbc.CardHeader(html.H5("Feature Finding Options")),
    dbc.CardBody(
        [   
            dbc.Row([
                dbc.Col(
                    dbc.InputGroup(
                        [
                            dbc.InputGroupAddon("Precursor PPM Tolerance", addon_type="prepend"),
                            dbc.Input(id='feature_finding_ppm', placeholder="PPM tolerance for feature finding", value=10),
                        ],
                        className="mb-3",
                    )
                ),
                dbc.Col(
                    dbc.InputGroup(
                        [
                            dbc.InputGroupAddon("MS1 Noise Level", addon_type="prepend"),
                            dbc.Input(id='feature_finding_noise', placeholder="Noise for feature finding", value=10000),
                        ],
                        className="mb-3",
                    )
                ),
            ]),

            dbc.Row([
                dbc.Col(
                    dbc.InputGroup(
                        [
                            dbc.InputGroupAddon("Min Peak Width (Minutes)", addon_type="prepend"),
                            dbc.Input(id='feature_finding_min_peak_rt', placeholder="RT Min for feature finding", value=0.05),
                        ],
                        className="mb-3",
                    )
                ),
                dbc.Col(
                    dbc.InputGroup(
                        [
                            dbc.InputGroupAddon("Max Peak Width (Minutes)", addon_type="prepend"),
                            dbc.Input(id='feature_finding_max_peak_rt', placeholder="RT Max for feature finding", value=1.5),
                        ],
                        className="mb-3",
                    )
                ),
            ]),

            dbc.Row([
                dbc.Col(
                    dbc.InputGroup(
                        [
                            dbc.InputGroupAddon("RT Tolerance (Minutes)", addon_type="prepend"),
                            dbc.Input(id='feature_finding_rt_tolerance', placeholder="RT Tolerance for Isotopic peaks", value=0.3),
                        ],
                        className="mb-3",
                    )
                ),
            ]),

            dbc.Row([
                dbc.Col(
                    dbc.InputGroup(
                        [
                            dbc.Button("Update Feature Finding Interactively", color="primary", className="mr-1", id="run_feature_finding_button", block=True),
                        ],
                        className="mb-3",
                    )
                ),
                dbc.Col(
                    dbc.InputGroup(
                        [
                            dcc.Link(dbc.Button("Run Feature Finding at GNPS with Parameters (Super Beta)", color="primary", className="mr-1"), href="https://proteomics2.ucsd.edu/ProteoSAFe/index.jsp?params={%22workflow%22:%22LC_MZMINE2%22,%22workflow_version%22:%22current%22}", target="_blank", id="run-gnps-mzmine-link")
                        ],
                        className="mb-3",
                    )
                ),
            ]),
        ]
    )
]

FEATUREFINDING_RESULTS_CARD = [
    dbc.CardHeader(html.H5("Feature Finding Results")),
    dbc.CardBody(
        [
            dcc.Loading(
                id="feature-finding-table",
                children=[html.Div([html.Div(id="loading-output-100")])],
                type="default",
            ),
            html.Hr(),
            dbc.Button("Download Exclusion for Orbitrap", block=True, id="orbitrap_exclusion_download_button"),
            dcc.Download(id="orbitrap_exclusion_download")
        ]
    )
]