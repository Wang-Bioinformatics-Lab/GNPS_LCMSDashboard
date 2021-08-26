# -*- coding: utf-8 -*-

# Dash imports

import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output, State
import dash_daq as daq
import dash_uploader as du


# Plotly Imports
import plotly.express as px
import plotly.graph_objects as go 


# Flask
from flask import Flask, send_from_directory, send_file
import werkzeug
from flask_caching import Cache

# Misc Library
import sys
import shutil
import os
import io
from zipfile import ZipFile
import urllib.parse
from scipy import integrate
import pandas as pd
import uuid
import numpy as np
import datashader as ds
import json
from collections import defaultdict
import uuid
import base64
import redis
from time import sleep
import requests
from datetime import datetime

from molmass import Formula
from pyteomics import mass

# Project Imports
from utils import _calculate_file_stats
from utils import _get_scan_polarity
from utils import _resolve_map_plot_selection, _get_param_from_url, _spectrum_generator
from utils import MS_precisions
import utils

from sync import _sychronize_save_state, _sychronize_load_state

import download
import ms2
import lcms_map
import tasks
from formula_utils import get_adduct_mass
import xic
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Importing layout for HTML

from layout_misc import EXAMPLE_DASHBOARD, SYCHRONIZATION_MODAL, SPECTRUM_DETAILS_MODAL, ADVANCED_VISUALIZATION_MODAL, ADVANCED_IMPORT_MODAL, ADVANCED_REPLAY_MODAL, ADVANCED_USI_MODAL
from layout_misc import UPLOAD_MODAL
from layout_xic_options import ADVANCED_XIC_MODAL
from layout_overlay import OVERLAY_PANEL
from layout_fastsearch import ADVANCED_LIBRARYSEARCH_MODAL, ADVANCED_LIBRARYSEARCHMASSIVEKB_MODAL
from layout_massql import MASSSPEC_QUERY_PANEL


server = Flask(__name__)
app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = 'GNPS - LCMS Browser'
TEMPFOLDER = "./temp"
TEMP_UPLOADFOLDER = "./temp/dash-uploader"
du.configure_upload(app, TEMP_UPLOADFOLDER)

server.wsgi_app = ProxyFix(server.wsgi_app, x_for=1, x_host=1)

limiter = Limiter(
    server,
    key_func=get_remote_address,
    default_limits=["10000 per hour"]
)

# Optionally turn on caching
if __name__ == "__main__":
    WORKER_UP = False
    cache = Cache(app.server, config={
        'CACHE_TYPE': "null",
        #'CACHE_TYPE': 'filesystem',
        'CACHE_DIR': 'temp/flask-cache',
        'CACHE_DEFAULT_TIMEOUT': 0,
        'CACHE_THRESHOLD': 1000000
    })

    redis_client = None
else:
    WORKER_UP = True
    cache = Cache(app.server, config={
        #'CACHE_TYPE': "null",
        'CACHE_TYPE': 'filesystem',
        'CACHE_DIR': 'temp/flask-cache',
        'CACHE_DEFAULT_TIMEOUT': 0,
        'CACHE_THRESHOLD': 1000000
    })

    redis_client = redis.Redis(host='redis', port=6379, db=0)

server = app.server

app.index_string = """<!DOCTYPE html>
<html>
    <head>
        <!-- Global site tag (gtag.js) - Google Analytics -->
        <script async src="https://www.googletagmanager.com/gtag/js?id=G-JGX1MKR163"></script>
        <script>
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());

            gtag('config', 'G-JGX1MKR163');
        </script>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>"""

df = pd.DataFrame()
df["rt"] = [1]
df["mz"] = [1]
df["i"] = [1]
cvs = ds.Canvas(plot_width=1, plot_height=1)
agg = cvs.points(df,'rt','mz', agg=ds.sum("i"))
zero_mask = agg.values == 0
agg.values = np.log10(agg.values, where=np.logical_not(zero_mask))
placeholder_map_plot = px.imshow(agg, origin='lower', labels={'color':'Log10(Abundance)'}, title='Heatmap Plot - Please enter a USI or Upload a File', color_continuous_scale="Hot")
placeholder_xic_plot = px.line(df, x="rt", y="mz", title='XIC Plot - Please Enter an m/z value', render_mode="svg")
placeholder_ms2_plot = px.line(df, x="rt", y="mz", title='MS Spectrum Plot - Please select a scan number', render_mode="svg")

MAX_XIC_PLOT_LCMS_FILES = 30
MAX_LCMS_FILES = 500

NAVBAR = dbc.Navbar(
    children=[
        dbc.NavbarBrand(
            html.Img(src="https://gnps-cytoscape.ucsd.edu/static/img/GNPS_logo.png", width="120px"),
            href="https://gnps.ucsd.edu"
        ),
        dbc.Nav(
            [
                dbc.NavItem(dbc.NavLink("GNPS LCMS Dashboard - Version 0.51", href="/")),
                dbc.NavItem(dbc.NavLink("Documentation", href="https://ccms-ucsd.github.io/GNPSDocumentation/lcms-dashboard/")),
                dbc.NavItem(dbc.NavLink("GNPS Datasets", href="https://gnps.ucsd.edu/ProteoSAFe/datasets.jsp#%7B%22query%22%3A%7B%7D%2C%22table_sort_history%22%3A%22createdMillis_dsc%22%2C%22title_input%22%3A%22GNPS%22%7D")),
                dbc.NavItem(id="dataset_files_nav"),
            ],
        navbar=True)
    ],
    color="light",
    dark=False,
    sticky="top",
)

DATASELECTION_CARD = [
    dbc.CardHeader([
        dbc.Row([
            dbc.Col(
                html.H5("Data Selection"),
            ),
            dbc.Col(
                dbc.Button("Show/Hide", 
                    id="data_selection_show_hide_button", 
                    color="primary", size="sm", 
                    className="mr-1", 
                    style={
                        "float" : "right"
                    }
                ),
            )
        ])
    ]),
    dbc.Collapse(
        dbc.CardBody(dbc.Row(
            [   ## Left Panel
                dbc.Col([
                    dbc.Row([
                        dbc.Col(html.H5(children='File Selection')),
                        dbc.Col(
                            dbc.Button("Upload Files", 
                                id="advanced_upload_modal_button", 
                                color="info", size="sm", 
                                className="mr-1", 
                                style={
                                    "float" : "right"
                                }
                            ),
                        ),
                    ]),
                    html.Hr(),
                    dbc.InputGroup(
                        [
                            dbc.InputGroupAddon("GNPS USI", addon_type="prepend"),
                            dbc.Textarea(id='usi', placeholder="Enter GNPS File USI"),
                        ],
                        className="mb-3",
                    ),
                    dbc.InputGroup(
                        [
                            dbc.InputGroupAddon("GNPS USI2", addon_type="prepend"),
                            dbc.Textarea(id='usi2', placeholder="Enter GNPS File USI", value=""),
                        ],
                        className="mb-3",
                    ),
                    # Linkouts
                    dbc.Row([
                        dbc.Col(
                            dbc.Button("Copy URL Link to this Visualization", block=True, color="info", id="copy_link_button", n_clicks=0),
                        ),
                        dbc.Col(
                            dcc.Loading(
                                id="network-link-button",
                                children=[html.Div([html.Div(id="loading-output-232")])],
                                type="default",
                            ),
                        ),
                    ]),
                    html.Br(),
                    dbc.InputGroup(
                        [
                            dbc.InputGroupAddon("Comment", addon_type="prepend"),
                            dbc.Textarea(id='comment', value=""),
                        ],
                        className="mb-3",
                    ),
                    html.H5(children='LCMS Viewer Options'),
                    html.Hr(),
                    dbc.Row([
                        dbc.Col(
                            dbc.FormGroup(
                                [
                                    dbc.Label("Show MS2 Markers", html_for="show_ms2_markers", width=4.8, style={"width":"160px", "margin-left": "25px"}),
                                    dbc.Col(
                                        daq.ToggleSwitch(
                                            id='show_ms2_markers',
                                            value=True,
                                            size=50,
                                            style={
                                                "marginTop": "4px",
                                                "width": "100px"
                                            }
                                        )
                                    ),
                                ],
                                row=True,
                                className="mb-3",
                            )),
                    ]),
                    dbc.Row([
                        dbc.Col(
                            dbc.FormGroup(
                                [
                                    dbc.Label("Show USI LCMS Map", html_for="show_lcms_1st_map", width=5.8, style={"width":"160px", "margin-left": "25px"}),
                                    dbc.Col(
                                        daq.ToggleSwitch(
                                            id='show_lcms_1st_map',
                                            value=True,
                                            size=50,
                                            style={
                                                "marginTop": "4px",
                                                "width": "100px"
                                            }
                                        )
                                    ),
                                ],
                                row=True,
                                className="mb-3",
                            )),
                        dbc.Col(
                            dbc.FormGroup(
                                [
                                    dbc.Label("Show USI2 LCMS Map", html_for="show_lcms_2nd_map", width=5.8, style={"width":"160px"}),
                                    dbc.Col(
                                        daq.ToggleSwitch(
                                            id='show_lcms_2nd_map',
                                            value=False,
                                            size=50,
                                            style={
                                                "marginTop": "4px",
                                                "width": "100px"
                                            }
                                        )
                                    ),
                                ],
                                row=True,
                                className="mb-3",
                            )),
                    ]),
                    dbc.Row([
                        dbc.Col(
                            dbc.FormGroup(
                                [
                                    dbc.Label("Show Filters", html_for="show_filters", width=5.8, style={"width":"160px", "margin-left": "25px"}),
                                    dbc.Col(
                                        daq.ToggleSwitch(
                                            id='show_filters',
                                            value=False,
                                            size=50,
                                            style={
                                                "marginTop": "4px",
                                                "width": "100px"
                                            }
                                        )
                                    ),
                                ],
                                row=True,
                                className="mb-3",
                            )),
                        dbc.Col(
                            dbc.FormGroup(
                                [
                                    dbc.Label("Feature Finding", width=4.8, style={"width":"140px"}),
                                    dcc.Dropdown(
                                        id='feature_finding_type',
                                        options=[
                                            {'label': 'Off', 'value': 'Off'},
                                            {'label': 'Test', 'value': 'Test'},
                                            {'label': 'Trivial', 'value': 'Trivial'},
                                            # {'label': 'TidyMS', 'value': 'TidyMS'},
                                            {'label': 'MZmine2 (Metabolomics)', 'value': 'MZmine2'},
                                            {'label': 'Dinosaur (Proteomics)', 'value': 'Dinosaur'},
                                            {'label': 'MassQL Query', 'value': 'MassQL'},
                                        ],
                                        searchable=False,
                                        clearable=False,
                                        value="Off",
                                        style={
                                            "width":"50%"
                                        }
                                    )
                                ],
                                row=True,
                                className="mb-3",
                                style={"margin-left": "4px"}
                        )),
                    ]),
                    dbc.Row([
                        dbc.Col(
                            dbc.FormGroup(
                                [
                                    dbc.Label("Show Overlay", html_for="show_overlay", width=5.8, style={"width":"160px", "margin-left": "25px"}),
                                    dbc.Col(
                                        daq.ToggleSwitch(
                                            id='show_overlay',
                                            value=False,
                                            size=50,
                                            style={
                                                "marginTop": "4px",
                                                "width": "100px"
                                            }
                                        )
                                    ),
                                ],
                                row=True,
                                className="mb-3",
                            )),
                        dbc.Col(),
                    ]),
                    html.H5(children='Loading Status'),
                    html.Hr(),
                    dbc.Table([
                        html.Tr([html.Td("File Download/Conversion"), 
                                 html.Td(dcc.Loading(
                                        id="loading_file_download",
                                        children="Ready",
                                        type="dot"
                                    )
                                 ),
                                 html.Td("XIC Drawing"), 
                                 html.Td(
                                     dcc.Loading(
                                        id="loading_xic_plot",
                                        children="Ready",
                                        type="dot"
                                    )
                                 )]),
                        html.Tr([html.Td("Heatmap Drawing Left"), 
                                 html.Td(dcc.Loading(
                                        id="loading_map_plot",
                                        children="Ready",
                                        type="dot"
                                    )
                                 ),
                                 html.Td("Heatmap Drawing Right"), 
                                 html.Td(
                                     dcc.Loading(
                                        id="loading_map_plot2",
                                        children="Ready",
                                        type="dot"
                                    )
                                 )]),
                        html.Tr([html.Td("TIC Drawing Left"), 
                                 html.Td(dcc.Loading(
                                        id="loading_tic_plot",
                                        children="Ready",
                                        type="dot"
                                    )
                                 ),
                                 html.Td("TIC Drawing Right"), 
                                 html.Td(
                                     dcc.Loading(
                                        id="loading_tic_plot2",
                                        children="Ready",
                                        type="dot"
                                    )
                                 )])
                    ], bordered=True, size="sm")
                ], className="col-sm"),
                ## Right Panel
                dbc.Col([
                    dbc.Row([
                        dbc.Col(html.H5(children='XIC Options')),
                        dbc.Col(
                            dbc.Button("Advanced XIC Options", 
                                id="advanced_xic_modal_button", 
                                color="info", size="sm", 
                                className="mr-1", 
                                style={
                                    "float" : "right"
                                }
                            ),
                        ),
                    ]),
                    html.Hr(),
                    dbc.Row([
                        dbc.Col(
                            dbc.InputGroup(
                                [
                                    dbc.InputGroupAddon("XIC m/z", addon_type="prepend"),
                                    dbc.Input(id='xic_mz', placeholder="Enter m/z to XIC", value=""),
                                ],
                                className="mb-3",
                            ),
                        ),
                        dbc.Col(
                            dbc.InputGroup(
                                [
                                    dbc.InputGroupAddon("XIC Formula", addon_type="prepend"),
                                    dbc.Input(id='xic_formula', placeholder="Enter Molecular Formula to XIC", value=""),
                                ],
                                className="mb-3",
                            ),
                        )
                    ]),
                    dbc.Row([
                        dbc.Col(
                            dbc.InputGroup(
                                [
                                    dbc.InputGroupAddon("XIC Tolerance (Da)", addon_type="prepend"),
                                    dbc.Input(id='xic_tolerance', placeholder="Enter Da Tolerance", value="0.5"),
                                ],
                                className="mb-3",
                            ),
                        ),
                        dbc.Col(
                            dbc.InputGroup(
                                [
                                    dbc.InputGroupAddon("XIC Tolerance (ppm)", addon_type="prepend"),
                                    dbc.Input(id='xic_ppm_tolerance', placeholder="Enter Da Tolerance", value="10"),
                                ],
                                className="mb-3",
                            ),
                        ),
                        dbc.Col(
                            dbc.FormGroup(
                                [
                                    dbc.Label("XIC Tolerance Unit", width=4.8, style={"width":"150px"}),
                                    dcc.Dropdown(
                                        id='xic_tolerance_unit',
                                        options=[
                                            {'label': 'Da', 'value': 'Da'},
                                            {'label': 'ppm', 'value': 'ppm'}
                                        ],
                                        searchable=False,
                                        clearable=False,
                                        value="Da",
                                        style={
                                            "width":"40%"
                                        }
                                    )  
                                ],
                                row=True,
                                className="mb-3",
                        )),
                    ]),
                    dbc.Row([
                        dbc.Col(
                            dbc.InputGroup(
                                [
                                    dbc.InputGroupAddon("XIC Retention Time View/Integration Limits", addon_type="prepend"),
                                    dbc.Input(id='xic_rt_window', placeholder="Enter RT Window (e.g. 1-2 or 1.5)", value=""),
                                ],
                                className="mb-3",
                            ),
                        ),
                    ]),
                    dbc.Row([
                        dbc.Col(
                            dbc.FormGroup(
                                [
                                    dbc.Label("XIC Integration", width=4.8, style={"width":"120px"}),
                                    dcc.Dropdown(
                                        id='xic_integration_type',
                                        options=[
                                            {'label': 'MS1 Sum', 'value': 'MS1SUM'},
                                            {'label': 'AUC', 'value': 'AUC'},
                                            {'label': 'MAXPEAKHEIGHT', 'value': 'MAXPEAKHEIGHT'},
                                        ],
                                        searchable=False,
                                        clearable=False,
                                        value="AUC",
                                        style={
                                            "width":"50%"
                                        }
                                    )  
                                ],
                                row=True,
                                className="mb-3",
                                style={"margin-left": "4px"}
                        )),
                        dbc.Col(
                            dbc.FormGroup(
                                [
                                    dbc.Label("XIC Normalization", html_for="xic_norm", width=4.8, style={"width":"140px"}),
                                    dbc.Col(
                                        daq.ToggleSwitch(
                                            id='xic_norm',
                                            value=False,
                                            size=50,
                                            style={
                                                "marginTop": "4px",
                                                "width": "100px"
                                            }
                                        )
                                    ),
                                ],
                                row=True,
                                className="mb-3",
                                style={"margin-left": "4px"}
                            )),
                        dbc.Col(
                            dbc.FormGroup(
                                [
                                    dbc.Label("XIC Grouping", width=4.8, style={"width":"120px"}),
                                    dcc.Dropdown(
                                        id='xic_file_grouping',
                                        options=[
                                            {'label': 'By File', 'value': 'FILE'},
                                            {'label': 'By m/z', 'value': 'MZ'},
                                            {'label': 'By Group', 'value': 'GROUP'}
                                        ],
                                        searchable=False,
                                        clearable=False,
                                        value="MZ",
                                        style={
                                            "width":"50%"
                                        }
                                    )  
                                ],
                                row=True,
                                className="mb-3",
                        )),
                    ]),
                    html.H5(children='MS2 Options'),
                    dbc.Row([
                        dbc.Col(
                            dbc.InputGroup(
                                [
                                    dbc.InputGroupAddon("MS2 Identifier", addon_type="prepend"),
                                    dbc.Input(id='ms2_identifier', placeholder="Enter Spectrum Identifier"),
                                ],
                                className="mb-3",
                            ),
                        ),
                    ]),
                    html.H5(children='TIC Options'),
                    dbc.Row([
                        dbc.Col(
                            dbc.FormGroup(
                                [
                                    dbc.Label("TIC option", width=4.8, style={"width":"100px"}),
                                    dcc.Dropdown(
                                        id='tic_option',
                                        options=[
                                            {'label': 'TIC', 'value': 'TIC'},
                                            {'label': 'BPI', 'value': 'BPI'}
                                        ],
                                        searchable=False,
                                        clearable=False,
                                        value="TIC",
                                        style={
                                            "width":"60%"
                                        }
                                    )
                                ],
                                row=True,
                                className="mb-3",
                                style={"margin-left": "4px"}
                            )
                        ),
                        dbc.Col(
                            dbc.FormGroup(
                                [
                                    dbc.Label("Show Multiple TICs", width=4.8, style={"width":"150px"}),
                                    dbc.Col(
                                        daq.ToggleSwitch(
                                            id='show_multiple_tic',
                                            value=False,
                                            size=50,
                                            style={
                                                "marginTop": "4px",
                                                "width": "100px"
                                            }
                                        )
                                    ),
                                ],
                                row=True,
                                className="mb-3",
                                style={"margin-left": "4px"}
                            ),
                        ),
                    ]),

                    dbc.Row([
                        dbc.Col(
                            html.H5(children='Rendering Options '),
                            className="col-3"
                        ),
                        dbc.Col(
                            dbc.Button("Dark Mode", 
                                id="darkmode_button", 
                                color="dark", size="sm",
                                className="mr-1",
                            ),
                            className="col-4"
                        )
                    ]),
                    
                    dbc.Row([
                        dbc.Col(
                            dcc.Dropdown(
                                id='image_export_format',
                                options=[
                                    {'label': 'SVG', 'value': 'svg'},
                                    {'label': 'PNG', 'value': 'png'},
                                ],
                                searchable=False,
                                clearable=False,
                                value="svg",
                                style={
                                    "width":"150px"
                                }
                            )  
                        ),
                        dbc.Col(
                            dbc.FormGroup(
                                [
                                    dbc.Label("Style", width=2, style={"width":"150px"}),
                                    dcc.Dropdown(
                                        id='plot_theme',
                                        options=[
                                            {'label': 'plotly_white', 'value': 'plotly_white'},
                                            {'label': 'ggplot2', 'value': 'ggplot2'},
                                            {'label': 'simple_white', 'value': 'simple_white'},
                                            {'label': 'seaborn', 'value': 'seaborn'},
                                            {'label': 'plotly', 'value': 'plotly'},
                                            {'label': 'plotly_dark', 'value': 'plotly_dark'},
                                            {'label': 'presentation', 'value': 'presentation'},
                                        ],
                                        searchable=False,
                                        clearable=False,
                                        value="plotly_white",
                                        style={
                                            "width":"60%"
                                        }
                                    )  
                                ],
                                row=True,
                                className="mb-3",
                            )),
                    ]),
                    html.H5(children='Advanced Panels'),
                    dbc.Row([
                        dbc.Col(
                            dbc.Button("Visualization Options", block=True, id="advanced_visualization_modal_button"),
                        ),
                        dbc.Col(
                            dbc.Button("Import Options", block=True, id="advanced_import_modal_button"),
                        ),
                        dbc.Col(
                            dbc.Button("Replay Options", block=True, id="advanced_replay_modal_button"),
                        )
                    ]),
                    html.Br(),
                    dbc.Row([
                        dbc.Col(
                            dbc.Button("Sync Options", block=True, color="info", id="sychronization_options_modal_button"),
                        ),
                        dbc.Col([
                            dbc.Button("Sync Initiate (Follower)", block=True, color="success", id="synchronization_begin_button"),
                            html.Div(id="synchronization_status")
                        ]),
                        dbc.Col(
                            dbc.Button("Sync Terminate (Follower)", block=True, color="danger", id="synchronization_stop_button"),
                        ),
                    ]),
                    html.Br(),
                    dbc.Row([
                        dbc.Col(
                            dbc.Button("Replay Advance", block=True, id="replay_forward_button"),
                        ),
                        dbc.Col(
                            dbc.Button("Replay Rewind", block=True, id="replay_backward_button"),
                        ),
                        dbc.Col(),
                    ])
                ], className="col-sm")
            ])
        ),
        id="data_selection_collapse",
        is_open=True
    ),
    
]

DATASLICE_CARD = [
    dbc.CardHeader([
        dbc.Row([
            dbc.Col(
                html.H5("Details Panel"),
            ),
            dbc.Col(
                dbc.Button("Clear XIC", 
                    id="xicmz_clear_button", 
                    color="info", size="sm", 
                    className="mr-1", 
                    style={
                        "float" : "right"
                    }
                ),
            )
        ])
    ]),
    dbc.CardBody(
        [   
            html.Br(),
            dcc.Loading(
                id="loading-20",
                children=[dcc.Graph(
                    id='xic-plot',
                    figure=placeholder_xic_plot,
                    config={
                        'doubleClick': 'reset',
                        "toImageButtonOptions":{
                            "format": "svg",
                        }
                    }
                )],
                type="default",
            ),
            dcc.Loading(
                id="loading-289",
                children=[dcc.Graph(
                    id='ms2-plot',
                    figure=placeholder_ms2_plot,
                    config={
                        'doubleClick': 'reset'
                    }
                )],
                type="default",
            ),

            dbc.ButtonGroup([
                dbc.Button("MS Details", block=False, id="spectrum_details_modal_button"),
                dbc.Button("View Metabolomics USI", block=False, id="advanced_usi_modal_button"),
                dbc.Button("GNPS Library", block=False, id="advanced_librarysearch_modal_button"),
                dbc.Button("MassIVE-KB Library", block=False, id="advanced_librarysearchmassivekb_modal_button"),
            ]),

            html.Br(),
            html.Br(),
            dcc.Loading(
                id="ms2-plot-buttons",
                children=[html.Div([html.Div(id="loading-output-1034")])],
                type="default",
            ),
            html.Br(),
            html.Br(),
            dcc.Loading(
                id="xic-heatmap",
                children=[html.Div([html.Div(id="loading-output-102")])],
                type="default",
            ),
        ]
    )
]

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



USI1_FILTERING_PANEL = [
    dbc.CardHeader(html.H5("USI Scan Filtering Options")),
    dbc.CardBody(
        [   
            dbc.Row([
                dbc.Col(
                    dbc.FormGroup(
                        [
                            dbc.Label("Polarity Filtering", width=4.8, style={"width":"160px", "margin-left": "25px"}),
                            dcc.Dropdown(
                                id='polarity_filtering',
                                options=[
                                    {'label': 'None', 'value': 'None'},
                                    {'label': 'Positive', 'value': 'Positive'},
                                    {'label': 'Negative', 'value': 'Negative'}
                                ],
                                searchable=False,
                                clearable=False,
                                value="None",
                                style={
                                    "width":"60%"
                                }
                            )
                        ],
                        row=True,
                        className="mb-3",
                    )),
                dbc.Col(
                    ),
            ]),
        ]
    )
]

USI2_FILTERING_PANEL = [
    dbc.CardHeader(html.H5("USI2 Scan Filtering Options")),
    dbc.CardBody(
        [   
            dbc.Row([
                dbc.Col(
                    dbc.FormGroup(
                        [
                            dbc.Label("Polarity Filtering", width=4.8, style={"width":"160px", "margin-left": "25px"}),
                            dcc.Dropdown(
                                id='polarity_filtering2',
                                options=[
                                    {'label': 'None', 'value': 'None'},
                                    {'label': 'Positive', 'value': 'Positive'},
                                    {'label': 'Negative', 'value': 'Negative'}
                                ],
                                searchable=False,
                                clearable=False,
                                value="None",
                                style={
                                    "width":"60%"
                                }
                            )
                        ],
                        row=True,
                        className="mb-3",
                    )),
                dbc.Col(
                    ),
            ]),
        ]
    )
]


DEBUG_CARD = [
    dbc.CardHeader(html.H5("DEBUG Panel")),
    dbc.CardBody(
        [
            dcc.Loading(
                id="download-link",
                children=[html.Div([html.Div(id="loading-output-1")])],
                type="default",
            ),
            dcc.Loading(
                id="debug-output",
                children=[html.Div([html.Div(id="loading-output-2")])],
                type="default",
            ),
            dcc.Loading(
                id="debug-output-2",
                children=[html.Div([html.Div(id="loading-output-16")])],
                type="default",
            ),
            dcc.Loading(
                id="debug-output-3",
                children=[html.Div([html.Div(id="loading-output-23123")])],
                type="default",
            ),
            dcc.Loading(
                id="qrcode",
                type="default"
            ),
            html.Hr(),
            html.H5("Privacy Policy"),
            dcc.Markdown('''
In order to be transparent in the usage of this tool, we track the following data

1. IP Addresses
1. Data selected and visualization options
1. Website that directed you to tool (if applicable)

It is our intention with the collected data to keep the specific data private but aggregate for research purposes. These purposes include and be limited to:

1. Understanding user behavior and learning how people explore and interact with mass spectrometry
2. Finding bugs and improving the platform
3. Aggregating user interactions and publish findings regarding which features and analysis workflows are useful to users
4. Usage reporting for grant and manuscript purposes
                ''')
        ]
    )
]

INTEGRATION_CARD = [
    dbc.CardHeader(html.H5("XIC Integration")),
    dbc.CardBody(
        [
            dcc.Loading(
                id="integration-table",
                children="Please enter XIC values to view the XIC integration table",
                type="default",
            ),
            html.Br(),
            html.Br(),
            html.Br(),
            dcc.Loading(
                id="integration-boxplot",
                children=[html.Div([html.Div(id="loading-output-101")])],
                type="default",
            ),
            html.Br(),
            html.Br(),
            dcc.Loading(
                id="integration-scatter",
                children=[html.Div([html.Div(id="loading-output-103")])],
                type="default",
            ),
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
        ]
    )
]


SUMMARY_CARD = [
    dbc.CardHeader(html.H5("File Summaries")),
    dbc.CardBody(
        [
            dcc.Loading(
                id="summary-table",
                children=[html.Div([html.Div(id="loading-output-105")])],
                type="default",
            ),
        ]
    )
]

CONTRIBUTORS_CARD = [
    dbc.CardHeader(html.H5("Contributors")),
    dbc.CardBody(
        [
            html.Div([
                "Mingxun Wang PhD - UC San Diego",
                html.Br(),
                "Daniel Petras PhD - UC San Diego",
                html.Br(),
                "Vanessa Phelan PhD - CU Anschutz",
                html.Hr(),
                html.H5("Beta Testers"),
                html.Hr(),
                "Alan Jarmusch PhD - NIH",
                html.Br(),
                "Allegra Aron PhD - UC San Diego",
                html.Br(),
                "Katherine Maloney PhD - Point Loma",
                html.Br(),
                "Aaron Puri PhD - University of Utah",
                html.Br(),
                "Tristan de Rond PhD - UC San Diego",
                html.Br(),
                "Wout Bittremieux PhD - UC San Diego",
                html.Br(),
                "Laura-Isobel McCall PhD - University of Oklahoma",
                html.Br(),
                "Benjamin Pullman - UC San Diego",
                html.Hr(),
                html.H5("Citation"),
                html.A("Petras, D., Phelan, V. V., Acharya, D. D., Allen, A. E., Aron, A. T., Bandeira, N., ... & Wang, M. (2021). GNPS Dashboard: Collaborative Analysis of Mass Spectrometry Data in the Web Browser. bioRxiv.", href="https://www.biorxiv.org/content/10.1101/2021.04.05.438475v1")
                ]
            )
        ]
    )
]

TOP_DASHBOARD = [
    html.Div(
        [
            html.Div(DATASELECTION_CARD),
        ]
    )
]

LEFT_DASHBOARD = [
    html.Div(
        [
            html.Div(DATASLICE_CARD),
            html.Div(INTEGRATION_CARD),
            html.Div(SUMMARY_CARD),
            html.Div(CONTRIBUTORS_CARD),
            html.Div(DEBUG_CARD),
        ]
    )
]

MIDDLE_DASHBOARD = [
    dbc.CardHeader([
        dbc.Row([
            dbc.Col(
                html.H5("Data Exploration"),
            ),
            dbc.Col(
            )
        ])
    ]),
    dbc.CardBody(
        [
            html.Br(),
            html.Div(id='map_plot_zoom', style={'display': 'none'}),
            html.Div(id='highlight_box', style={'display': 'none'}),
            dcc.Graph(
                id='map-plot',
                figure=placeholder_map_plot,
                config={
                    'doubleClick': 'reset',
                    'modeBarButtonsToRemove': [
                        "toggleSpikelines"
                    ]
                }
            ),
            html.Br(),
            dcc.Graph(
                id='tic-plot',
                config={
                    'doubleClick': 'reset'
                }
            )
        ]
    )
]


SECOND_DATAEXPLORATION_DASHBOARD = [
    dbc.CardHeader(html.H5("Data Exploration 2")),
    dbc.CardBody(
        [
            html.Br(),
            dcc.Graph(
                id='map-plot2',
                figure=placeholder_map_plot,
                config={
                    'doubleClick': 'reset',
                    'modeBarButtonsToRemove': [
                        "toggleSpikelines"
                    ]
                }
            ),
            html.Br(),
            dcc.Graph(
                id='tic-plot2',
                config={
                    'doubleClick': 'reset'
                }
            )
        ]
    )
]




BODY = dbc.Container(
    [
        dcc.Location(id='url', refresh=False),        
        html.Div(
            [
                dcc.Link(id="query_link", href="#", target="_blank"),
            ],
            style={
                "display" : "none"
            }
        ),
        dcc.Interval(
            id='sychronization_interval',
            interval=1000000000*1000, # in milliseconds
            n_intervals=0
        ),
        html.Div("", id="synchronization_type_dependency", style={"display":"none"}), # This is a hack to pass on a retrigger without causing infinite loops in the dependency chain
        html.Div("", id="page_parameters", style={"display":"none"}), # This is an intermediate dependency to hold the parameters so we make it easier to update them
        html.Div("", id="auto_import_parameters", style={"display":"none"}), # This is a hidden area to set parameters to be loaded into the interface

        dbc.Row([
            dbc.Col(
                dbc.Card(TOP_DASHBOARD), 
                className="w-100"
            ),
        ], style={"marginTop": 30}),

        # This is the filtering Panel
        dbc.Row([
            dbc.Collapse(
                [
                    dbc.Col([
                        dbc.Card(USI1_FILTERING_PANEL),
                    ],
                        #className="w-50"
                    ),
                ],
                id='usi1-filtering-collapse',
                is_open=True,
                style={"width": "50%", "marginTop": 30}
            ),
            dbc.Collapse(
                [
                    dbc.Col([
                        dbc.Card(USI2_FILTERING_PANEL),
                    ],
                        #className="w-50"
                    ),
                ],
                id='usi2-filtering-collapse',
                is_open=True,
                style={"width": "50%", "marginTop": 30}
            )
        ]),

        # This is the Feature Finding Panel
        dbc.Row([
            dbc.Collapse(
                [
                    dbc.Col([
                        dbc.Card(FEATURE_FINDING_PANEL),
                    ],
                        #className="w-50"
                    ),
                ],
                id='feature-finding-collapse',
                is_open=False,
                style={"width": "50%", "marginTop": 30}
            )
        ]),

        dbc.Row([
            dbc.Collapse(
                [
                    dbc.Col([
                        dbc.Card(OVERLAY_PANEL),
                    ],
                        #className="w-50"
                    ),
                ],
                id='overlay-collapse',
                is_open=True,
                style={"width": "50%", "marginTop": 30}
            )
        ]),

        # MassQL Query Panel
        dbc.Row([
            dbc.Collapse(
                [
                    dbc.Col([
                        dbc.Card(MASSSPEC_QUERY_PANEL),
                    ],
                        #className="w-50"
                    ),
                ],
                id='massql-collapse',
                is_open=False,
                style={"width": "50%", "marginTop": 30}
            )
        ]),



        # Show Data
        dbc.Row([
            dbc.Collapse(
                [
                    dbc.Col([
                        dbc.Card(MIDDLE_DASHBOARD),
                        html.Br(),
                        dbc.Collapse(
                            [
                                dbc.Card(FEATUREFINDING_RESULTS_CARD),
                            ],
                            id='featurefinding-results-collapse',
                            is_open=False,
                        ),
                        html.Br(),
                        dbc.Card(EXAMPLE_DASHBOARD),
                        html.Br(),
                        dbc.Card(SYCHRONIZATION_MODAL),
                        html.Br(),
                        dbc.Card(UPLOAD_MODAL),
                    ],
                        #className="w-50"
                    ),
                ],
                id='first-data-exploration-dashboard-collapse',
                is_open=True,
                style={"height": "1200px", "width": "50%"}
            ),
            dbc.Col([
                dbc.Collapse(
                    dbc.Card(SECOND_DATAEXPLORATION_DASHBOARD),
                    id='second-data-exploration-dashboard-collapse',
                    is_open=True,
                    style={"height": "1200px"}
                ),
                dbc.Card(LEFT_DASHBOARD),
            ],
                className="w-50"
            ),
        ], style={"marginTop": 30}),
        html.Br(),

        # Adding modals
        dbc.Row(SPECTRUM_DETAILS_MODAL),
        dbc.Row(ADVANCED_IMPORT_MODAL),
        dbc.Row(ADVANCED_REPLAY_MODAL),
        dbc.Row(ADVANCED_VISUALIZATION_MODAL),
        dbc.Row(ADVANCED_XIC_MODAL),
        dbc.Row(ADVANCED_USI_MODAL),
        dbc.Row(ADVANCED_LIBRARYSEARCH_MODAL),
        dbc.Row(ADVANCED_LIBRARYSEARCHMASSIVEKB_MODAL)
    ],
    fluid=True,
    className="",
)

app.layout = html.Div(children=[
    NAVBAR, 
    BODY])



def _resolve_usi(usi, temp_folder="temp"):
    """
    This function interacts with the task queuing system so that it can be abstracted out

    Args:
        usi ([type]): [description]
        tempfolder (str, optional): [description]. Defaults to "temp".

    Raises:
        Exception: [description]

    Returns:
        [type]: [description]
    """

    if download._resolve_exists_local(usi):
        # We can do it in line because we know that it won't actually do the call
        return download._resolve_usi(usi)
    else:
        if _is_worker_up():
            # If we have the celery instance up, we'll push it
            result = tasks._download_convert_file.delay(usi, temp_folder=temp_folder)

            # Waiting
            while(1):
                if result.ready():
                    break
                sleep(1)
            result = result.get()
            return result
        else:
            # If we have the celery instance is not up, we'll do it local
            print("Downloading Local")
            return tasks._download_convert_file(usi, temp_folder=temp_folder)



        
def _synchronize_collab_action(session_id, triggered_fields, full_params, synchronization_token=None):
    if _is_worker_up():
        result = tasks.task_collabsync.delay(session_id, triggered_fields, full_params, synchronization_token=synchronization_token)

# This helps to update the ms2/ms1 plot
@app.callback([
                  Output("ms2_identifier", "value")
              ],
              [
                  Input('url', 'search'),
                  Input('usi', 'value'),
                  Input('map-plot', 'clickData'), 
                  Input('xic-plot', 'clickData'), 
                  Input('tic-plot', 'clickData'),
                  Input('sychronization_load_session_button', 'n_clicks'),
                  Input('sychronization_interval', 'n_intervals'),
                  Input('advanced_import_update_button', "n_clicks"),
              ],
              [
                  State('sychronization_session_id', 'value'),
                  State('setting_json_area', 'value'),
                  State('ms2_identifier', 'value'),
              ])
def click_plot(url_search, usi, mapclickData, xicclickData, ticclickData, sychronization_load_session_button_clicks, sychronization_interval, advanced_import_update_button, 
                sychronization_session_id,
                setting_json_area, 
                existing_ms2_identifier):

    triggered_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    clicked_target = None
    if "map-plot" in triggered_id:
        clicked_target = mapclickData["points"][0]
    elif "xic-plot" in triggered_id:
        clicked_target = xicclickData["points"][0]
    elif "tic-plot" in triggered_id:
        clicked_target = ticclickData["points"][0]

    # nothing was clicked, so read from URL or session
    if clicked_target is None:
        session_dict = {}
        if "sychronization_load_session_button" in triggered_id or "sychronization_interval" in triggered_id:
            try:
                session_dict = _sychronize_load_state(sychronization_session_id, redis_client)
            except:
                pass
        
        # We clicked the button so we are going to load from the text area
        if "advanced_import_update_button" in triggered_id:
            try:
                session_dict = json.loads(setting_json_area)
            except:
                pass

        return [_get_param_from_url(url_search, "", "ms2_identifier", dash.no_update, session_dict=session_dict, old_value=existing_ms2_identifier, no_change_default=dash.no_update)]
    
    # This is an MS2
    if clicked_target["curveNumber"] == 1:
        return ["MS2:" + str(clicked_target["customdata"])]
    
    # This is an MS3
    if clicked_target["curveNumber"] == 2:
        return ["MS3:" + str(clicked_target["customdata"])]
    
    # This is an MS1
    if clicked_target["curveNumber"] == 0:
        rt_target = clicked_target["x"]

        usi_first = usi.split("\n")[0]
        remote_link, local_filename = _resolve_usi(usi_first)

        closest_scan = ms2.determine_scan_by_rt(usi_first, local_filename, rt_target)

        return ["MS1:{}".format(closest_scan)]


# This helps to update the ms2/ms1 plot
@app.callback([
                Output('debug-output', 'children'), 
                Output('ms2-plot', 'figure'), 
                Output('ms2-plot', 'config'), 
                Output('ms2-plot-buttons', 'children'),
                Output('spectrum_details_area', 'children'),
                Output('usi_frame', 'src'),
              ],
              [
                  Input('usi', 'value'), Input('ms2_identifier', 'value'), Input('image_export_format', 'value'), Input("plot_theme", "value")
              ], 
              [
                  State('xic_mz', 'value')
              ])
def draw_spectrum(usi, ms2_identifier, export_format, plot_theme, xic_mz):
    # Checking Values
    if ms2_identifier is None or len(ms2_identifier) < 2:
        return [dash.no_update] * 6

    usi_first = usi.split("\n")[0]

    usi_splits = usi_first.split(":")
    dataset = usi_splits[1]
    filename = usi_splits[2]
    scan_number = str(ms2_identifier.split(":")[-1])
    updated_usi = "mzspec:{}:{}:scan:{}".format(dataset, filename, scan_number)

    # For Drawing and Exporting
    graph_config = {
        "toImageButtonOptions":{
            "format": export_format,
            'filename': werkzeug.utils.secure_filename('ms2_plot_{}_{}'.format(filename, scan_number)),
            'height': None, 
            'width': None,
        }
    }

    # Getting Spectrum Peaks
    remote_link, local_filename = _resolve_usi(usi_first)
    peaks, precursor_mz, spectrum_details_string = ms2._get_ms2_peaks(updated_usi, local_filename, scan_number)
    usi_url = "https://metabolomics-usi.ucsd.edu/dashinterface/?usi={}".format(updated_usi)

    spectrum_type = "MS"
    button_elements = []

    # Drawing the spectrum object
    mzs = [peak[0] for peak in peaks]
    ints = [peak[1] for peak in peaks]
    neg_ints = [intensity * -1 for intensity in ints]

    # Figuring out which labels to show
    mzs_text = ms2._get_ms_peak_labels(mzs, ints)

    interactive_fig = go.Figure(
        data=go.Scatter(x=mzs, y=ints, 
            mode='markers+text',
            marker=dict(size=0.00001),
            error_y=dict(
                symmetric=False,
                arrayminus=[0]*len(neg_ints),
                array=neg_ints,
                width=0
            ),
            hoverinfo="x",
            textposition="top right",
            text=mzs_text
        )
    )

    interactive_fig.update_layout(title='{}'.format(ms2_identifier))
    interactive_fig.update_layout(template=plot_theme)
    interactive_fig.update_xaxes(title_text='m/z')
    interactive_fig.update_yaxes(title_text='intensity')
    interactive_fig.update_xaxes(showline=True, linewidth=1, linecolor='black')
    interactive_fig.update_yaxes(showline=True, linewidth=1, linecolor='black')
    interactive_fig.update_yaxes(range=[0, max(ints) * 1.2])

    if "MS2" in ms2_identifier or "MS3" in ms2_identifier:
        spectrum_type = "MS2"

        masst_dict = {}
        masst_dict["workflow"] = "SEARCH_SINGLE_SPECTRUM"
        masst_dict["precursor_mz"] = str(precursor_mz)
        masst_dict["spectrum_string"] = "\n".join(["{}\t{}".format(peak[0], peak[1]) for peak in peaks])

        masst_url = "https://gnps.ucsd.edu/ProteoSAFe/index.jsp#{}".format(json.dumps(masst_dict))
        masst_button = html.A(dbc.Button("MASST Spectrum in GNPS", color="primary", className="mr-1", block=True), href=masst_url, target="_blank")

        #USI_button = html.A(dbc.Button("View Vector Metabolomics USI", color="primary", className="mr-1", block=True), href=usi_url, target="_blank")

        button_elements = [masst_button]

    if "MS1" in ms2_identifier:
        spectrum_type = "MS1"

        #USI_button = html.A(dbc.Button("View Vector Metabolomics USI", color="primary", className="mr-1", block=True), href=usi_url, target="_blank")

        button_elements = []

    return [spectrum_type, 
            interactive_fig, graph_config, button_elements, html.Pre(spectrum_details_string), usi_url]

@app.callback([
                Output('advanced_librarysearchmassivekb_modal_button', 'children'),
                Output('librarysearchmassivekb_frame', 'src'), 
              ],
              [
                  Input('usi', 'value'), 
                  Input('ms2_identifier', 'value')
              ])
def draw_fastsearch_gnps(usi, ms2_identifier):
    # Checking Values
    if ms2_identifier is None or len(ms2_identifier) < 2:
        return [dash.no_update] * 2

    usi_first = usi.split("\n")[0]

    usi_splits = usi_first.split(":")
    dataset = usi_splits[1]
    filename = usi_splits[2]
    scan_number = str(ms2_identifier.split(":")[-1])
    updated_usi = "mzspec:{}:{}:scan:{}".format(dataset, filename, scan_number)

    massivekb_librarysearch_url = "https://fastlibrarysearch.ucsd.edu/fastsearch/?library_select=massivekb_index&usi1={}".format(updated_usi)

    # Perform API call to get number of matches for MassIVE-KB
    massivekb_search_text = "MassIVE-KB Library"
    try:
        search_api_url = "https://fastlibrarysearch.ucsd.edu/search?usi={}&library=massivekb_index&analog=No".format(updated_usi)
        search_api_response = requests.get(search_api_url, timeout=10)
        search_api_response_json = search_api_response.json()
        num_matches = len(search_api_response_json["results"])

        if num_matches > 0:
            massivekb_search_text = "MassIVE-KB Library ({} Putative Hits)".format(num_matches)
    #except requests.exceptions.Timeout:
    except:
        pass

    return [massivekb_search_text, massivekb_librarysearch_url]

@app.callback([
                Output('advanced_librarysearch_modal_button', 'children'),
                Output('librarysearch_frame', 'src'), 
              ],
              [
                  Input('usi', 'value'), 
                  Input('ms2_identifier', 'value')
              ])
def draw_fastsearch_massivekb(usi, ms2_identifier):
    # Checking Values
    if ms2_identifier is None or len(ms2_identifier) < 2:
        return [dash.no_update] * 2

    usi_first = usi.split("\n")[0]

    usi_splits = usi_first.split(":")
    dataset = usi_splits[1]
    filename = usi_splits[2]
    scan_number = str(ms2_identifier.split(":")[-1])
    updated_usi = "mzspec:{}:{}:scan:{}".format(dataset, filename, scan_number)

    gnps_librarysearch_url = "https://fastlibrarysearch.ucsd.edu/fastsearch/?library_select=gnpslibrary&usi1={}".format(updated_usi)

    # Perform API call to get number of matches for GNPS
    gnps_search_text = "GNPS Library"
    try:
        search_api_url = "https://fastlibrarysearch.ucsd.edu/search?usi={}&library=gnpslibrary&analog=No".format(updated_usi)
        search_api_response = requests.get(search_api_url, timeout=10)
        search_api_response_json = search_api_response.json()
        num_matches = len(search_api_response_json["results"])

        if num_matches > 0:
            gnps_search_text = "GNPS Library ({} Putative Hits)".format(num_matches)
    #except requests.exceptions.Timeout:
    except:
        pass

    return [gnps_search_text, gnps_librarysearch_url]

@app.callback([ 
                Output("xic_formula", "value"),
                Output("xic_peptide", "value"),
                Output("xic_tolerance", "value"), 
                Output("xic_ppm_tolerance", "value"), 
                Output("xic_tolerance_unit", "value"), 
                Output("xic_rt_window", "value"), 
                Output("xic_norm", "value"), 
                Output("xic_file_grouping", "value"),
                Output("xic_integration_type", "value"),
                
                Output("show_ms2_markers", "value"),
                Output("ms2marker_color", "value"),
                Output("ms2marker_size", "value"),

                Output("show_lcms_2nd_map", "value"),
                Output("tic_option", "value"),
                Output("polarity_filtering", "value"),
                Output("polarity_filtering2", "value"),
                Output("overlay_usi", "value"),
                Output("overlay_mz", "value"),
                Output("overlay_rt", "value"),
                Output("overlay_color", "value"),
                Output("overlay_size", "value"),
                Output("overlay_hover", "value"),
                Output('overlay_filter_column', 'value'),
                Output('overlay_filter_value', 'value'),

                Output("feature_finding_type", "value"),
                Output("feature_finding_ppm", "value"),
                Output("feature_finding_noise", "value"),
                Output("feature_finding_min_peak_rt", "value"),
                Output("feature_finding_max_peak_rt", "value"),
                Output("feature_finding_rt_tolerance", "value"),

                Output("massql_statement", "value"),

                Output("sychronization_session_id", "value"),

                Output("chromatogram_options", "value"),

                Output("comment", "value"),

                Output("map_plot_color_scale", "value"),
                Output("map_plot_quantization_level", "value"),

                Output("plot_theme", "value"),
              ],
              [
                  Input('url', 'search'), 
                  Input('sychronization_load_session_button', 'n_clicks'),
                  Input('sychronization_interval', 'n_intervals'),
                  Input('advanced_import_update_button', "n_clicks"),
                  Input('auto_import_parameters', 'children'),

                  Input('darkmode_button', 'n_clicks'),
              ],
              [
                  State('sychronization_session_id', 'value'),
                  State('setting_json_area', 'value'),

                  State('xic_formula', 'value'),
                  State('xic_peptide', 'value'),
                  State('xic_tolerance', 'value'),
                  State('xic_ppm_tolerance', 'value'),
                  State('xic_tolerance_unit', 'value'),
                  State('xic_norm', 'value'),
                  State('xic_integration_type', 'value'),
                  State('xic_file_grouping', 'value'),
                  State('xic_rt_window', 'value'),

                  State('show_ms2_markers', 'value'),
                  State("ms2marker_color", "value"),
                  State("ms2marker_size", "value"),

                  State('show_lcms_2nd_map', 'value'),
                  State('tic_option', 'value'),
                  State('polarity_filtering', 'value'),
                  State('polarity_filtering2', 'value'),

                  State('overlay_usi', 'value'),
                  State('overlay_mz', 'value'),
                  State('overlay_rt', 'value'),
                  State('overlay_color', 'value'),
                  State('overlay_size', 'value'),
                  State('overlay_hover', 'value'),
                  State('overlay_filter_column', 'value'),
                  State('overlay_filter_value', 'value'),

                  State('feature_finding_type', 'value'),
                  State('feature_finding_ppm', 'value'),
                  State('feature_finding_noise', 'value'),
                  State('feature_finding_min_peak_rt', 'value'),
                  State('feature_finding_max_peak_rt', 'value'),
                  State('feature_finding_rt_tolerance', 'value'),

                  State("massql_statement", "value"),
                  
                  State('sychronization_session_id', 'value'),

                  State("chromatogram_options", "value"),

                  State("comment", 'value'),

                  State('map_plot_color_scale', 'value'),
                  State('map_plot_quantization_level', 'value'),

                  State("plot_theme", "value"),
                  
              ]
              )
def determine_url_only_parameters(  search, 
                                    sychronization_load_session_button_click, 
                                    sychronization_interval, 
                                    advanced_import_update_button, 
                                    auto_import_parameters,

                                    darkmode_button_click,

                                    sychronization_session_id,

                                    setting_json_area,

                                    existing_xic_formula,
                                    existing_xic_peptide,
                                    existing_xic_tolerance,
                                    existing_xic_ppm_tolerance,
                                    existing_xic_tolerance_unit,
                                    existing_xic_norm,
                                    existing_xic_integration_type,
                                    existing_xic_file_grouping,
                                    existing_xic_rt_window,

                                    existing_show_ms2_markers,
                                    existing_ms2marker_color,
                                    existing_ms2marker_size,

                                    existing_show_lcms_2nd_map,

                                    existing_tic_option,

                                    existing_polarity_filtering,
                                    existing_polarity_filtering2,

                                    existing_overlay_usi,
                                    existing_overlay_mz,
                                    existing_overlay_rt,
                                    existing_overlay_color,
                                    existing_overlay_size,
                                    existing_overlay_hover,
                                    existing_overlay_filter_column,
                                    existing_overlay_filter_value,

                                    existing_feature_finding_type,
                                    existing_feature_finding_ppm,
                                    existing_feature_finding_noise,
                                    existing_feature_finding_min_peak_rt,
                                    existing_feature_finding_max_peak_rt,
                                    existing_feature_finding_rt_tolerance,

                                    existing_massql_statement,

                                    existing_sychronization_session_id,

                                    existing_chromatogram_options,

                                    existing_comment,
                                    
                                    existing_map_plot_color_scale,
                                    existing_map_plot_quantization_level,
                                    
                                    existing_plot_theme):
    triggered_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    # Here we clicked a button
    if "darkmode_button" in triggered_id:
        output = [dash.no_update] * 36
        output[-1] = "plotly_dark"
        output[-3] = "Turbo"
        return output

    #print("TRIGGERED URL PARSING", triggered_id, file=sys.stderr)

    session_dict = {}
    # We are going to load it from internal redis session server
    if "sychronization_load_session_button" in triggered_id or "sychronization_interval" in triggered_id:
        if len(sychronization_session_id) > 0:
            #print("LOADING", sychronization_session_id, file=sys.stderr)
            try:
                session_dict = _sychronize_load_state(sychronization_session_id, redis_client)
                print(session_dict, file=sys.stderr)
            except:
                pass
    
    # We clicked the button so we are going to load from the text area
    if "advanced_import_update_button" in triggered_id:
        try:
            session_dict = json.loads(setting_json_area)
        except:
            pass

    if "auto_import_parameters" in triggered_id:
        try:
            session_dict = json.loads(auto_import_parameters)
        except:
            pass

    xic_formula = _get_param_from_url(search, "", "xic_formula", dash.no_update, session_dict=session_dict, old_value=existing_xic_formula, no_change_default=dash.no_update)
    xic_peptide = _get_param_from_url(search, "", "xic_peptide", dash.no_update, session_dict=session_dict, old_value=existing_xic_peptide, no_change_default=dash.no_update)
    xic_tolerance = _get_param_from_url(search, "", "xic_tolerance", dash.no_update, session_dict=session_dict, old_value=existing_xic_tolerance, no_change_default=dash.no_update)
    xic_ppm_tolerance = _get_param_from_url(search, "", "xic_ppm_tolerance", dash.no_update, session_dict=session_dict, old_value=existing_xic_ppm_tolerance, no_change_default=dash.no_update)
    xic_tolerance_unit = _get_param_from_url(search, "", "xic_tolerance_unit", dash.no_update, session_dict=session_dict, old_value=existing_xic_tolerance_unit, no_change_default=dash.no_update)
    xic_norm = _get_param_from_url(search, "", "xic_norm", dash.no_update, session_dict=session_dict, old_value=existing_xic_norm, no_change_default=dash.no_update)
    xic_integration_type = _get_param_from_url(search, "", "xic_integration_type", dash.no_update, session_dict=session_dict, old_value=existing_xic_integration_type, no_change_default=dash.no_update)
    xic_file_grouping = _get_param_from_url(search, "", "xic_file_grouping", dash.no_update, session_dict=session_dict, old_value=existing_xic_file_grouping, no_change_default=dash.no_update)
    xic_rt_window = _get_param_from_url(search, "", "xic_rt_window", dash.no_update, session_dict=session_dict, old_value=existing_xic_rt_window, no_change_default=dash.no_update)

    show_ms2_markers = _get_param_from_url(search, "", "show_ms2_markers", dash.no_update, session_dict=session_dict, old_value=existing_show_ms2_markers, no_change_default=dash.no_update)
    ms2marker_color = _get_param_from_url(search, "", "ms2marker_color", dash.no_update, session_dict=session_dict, old_value=existing_ms2marker_color, no_change_default=dash.no_update)
    ms2marker_size = _get_param_from_url(search, "", "ms2marker_size", dash.no_update, session_dict=session_dict, old_value=existing_ms2marker_size, no_change_default=dash.no_update)

    show_lcms_2nd_map = _get_param_from_url(search, "", "show_lcms_2nd_map", dash.no_update, session_dict=session_dict, old_value=existing_show_lcms_2nd_map, no_change_default=dash.no_update)

    tic_option = _get_param_from_url(search, "", "tic_option", dash.no_update, session_dict=session_dict, old_value=existing_tic_option, no_change_default=dash.no_update)

    polarity_filtering = _get_param_from_url(search, "", "polarity_filtering", dash.no_update, session_dict=session_dict, old_value=existing_polarity_filtering, no_change_default=dash.no_update)
    polarity_filtering2 = _get_param_from_url(search, "", "polarity_filtering2", dash.no_update, session_dict=session_dict, old_value=existing_polarity_filtering2, no_change_default=dash.no_update)

    overlay_usi = _get_param_from_url(search, "", "overlay_usi", dash.no_update, session_dict=session_dict, old_value=existing_overlay_usi, no_change_default=dash.no_update)
    overlay_mz = _get_param_from_url(search, "", "overlay_mz", dash.no_update, session_dict=session_dict, old_value=existing_overlay_mz, no_change_default=dash.no_update)
    overlay_rt = _get_param_from_url(search, "", "overlay_rt", dash.no_update, session_dict=session_dict, old_value=existing_overlay_rt, no_change_default=dash.no_update)
    overlay_color = _get_param_from_url(search, "", "overlay_color", dash.no_update, session_dict=session_dict, old_value=existing_overlay_color, no_change_default=dash.no_update)
    overlay_size = _get_param_from_url(search, "", "overlay_size", dash.no_update, session_dict=session_dict, old_value=existing_overlay_size, no_change_default=dash.no_update)
    overlay_hover = _get_param_from_url(search, "", "overlay_hover", dash.no_update, session_dict=session_dict, old_value=existing_overlay_hover, no_change_default=dash.no_update)
    overlay_filter_column = _get_param_from_url(search, "", "overlay_filter_column", dash.no_update, session_dict=session_dict, old_value=existing_overlay_filter_column, no_change_default=dash.no_update)
    overlay_filter_value = _get_param_from_url(search, "", "overlay_filter_value", dash.no_update, session_dict=session_dict, old_value=existing_overlay_filter_value, no_change_default=dash.no_update)

    # Feature Finding
    feature_finding_type = _get_param_from_url(search, "", "feature_finding_type", dash.no_update, session_dict=session_dict, old_value=existing_feature_finding_type, no_change_default=dash.no_update)
    feature_finding_ppm = _get_param_from_url(search, "", "feature_finding_ppm", dash.no_update, session_dict=session_dict, old_value=existing_feature_finding_ppm, no_change_default=dash.no_update)
    feature_finding_noise = _get_param_from_url(search, "", "feature_finding_noise", dash.no_update, session_dict=session_dict, old_value=existing_feature_finding_noise, no_change_default=dash.no_update)
    feature_finding_min_peak_rt = _get_param_from_url(search, "", "feature_finding_min_peak_rt", dash.no_update, session_dict=session_dict, old_value=existing_feature_finding_min_peak_rt, no_change_default=dash.no_update)
    feature_finding_max_peak_rt = _get_param_from_url(search, "", "feature_finding_max_peak_rt", dash.no_update, session_dict=session_dict, old_value=existing_feature_finding_max_peak_rt, no_change_default=dash.no_update)
    feature_finding_rt_tolerance = _get_param_from_url(search, "", "feature_finding_rt_tolerance", dash.no_update, session_dict=session_dict, old_value=existing_feature_finding_rt_tolerance, no_change_default=dash.no_update)

    # MassQL
    massql_statement = _get_param_from_url(search, "", "massql_statement", dash.no_update, session_dict=session_dict, old_value=existing_massql_statement, no_change_default=dash.no_update)

    # Sychronization
    default_session_id = str(uuid.uuid4()).replace("-", "")
    if len(existing_sychronization_session_id) > 0:
        default_session_id = existing_sychronization_session_id
    sychronization_session_id = _get_param_from_url(search, "", "sychronization_session_id", default_session_id, session_dict=session_dict, old_value=existing_sychronization_session_id, no_change_default=dash.no_update)

    # Chromatogram Options
    chromatogram_options = _get_param_from_url(search, "", "chromatogram_options", dash.no_update, session_dict=session_dict, old_value=json.dumps(existing_chromatogram_options), no_change_default=dash.no_update)

    # Comment
    comment = _get_param_from_url(search, "", "comment", dash.no_update, session_dict=session_dict, old_value=existing_comment, no_change_default=dash.no_update)

    # Advanced Visualization Options
    map_plot_color_scale = _get_param_from_url(search, "", "map_plot_color_scale", dash.no_update, session_dict=session_dict, old_value=existing_map_plot_color_scale, no_change_default=dash.no_update)
    map_plot_quantization_level = _get_param_from_url(search, "", "map_plot_quantization_level", dash.no_update, session_dict=session_dict, old_value=existing_map_plot_quantization_level, no_change_default=dash.no_update)

    plot_theme = _get_param_from_url(search, "", "plot_theme", dash.no_update, session_dict=session_dict, old_value=existing_plot_theme, no_change_default=dash.no_update)

    # Formatting the types
    try:
        if xic_norm == "True":
            xic_norm = True
        if xic_norm == "False":
            xic_norm = False
        
        if xic_norm == existing_xic_norm:
            xic_norm = dash.no_update
    except:
        pass

    try:
        if show_ms2_markers == "True":
            show_ms2_markers = True
        if show_ms2_markers == "False":
            show_ms2_markers = True

        if show_ms2_markers == existing_show_ms2_markers:
            show_ms2_markers = dash.no_update
    except:
        pass

    try:
        if show_lcms_2nd_map == "True":
            show_lcms_2nd_map = True
        if show_lcms_2nd_map == "False":
            show_lcms_2nd_map = False

        if show_lcms_2nd_map == existing_show_lcms_2nd_map:
            show_lcms_2nd_map = dash.no_update
    except:
        pass

    try:
        chromatogram_options = json.loads(chromatogram_options)
    except:
        pass    
    
    return [xic_formula, 
            xic_peptide, 
            xic_tolerance, 
            xic_ppm_tolerance, 
            xic_tolerance_unit, 
            xic_rt_window, 
            xic_norm, 
            xic_file_grouping, 
            xic_integration_type, 
            show_ms2_markers, 
            ms2marker_color, 
            ms2marker_size, 
            show_lcms_2nd_map, 
            tic_option, 
            polarity_filtering, 
            polarity_filtering2, 
            overlay_usi, overlay_mz, overlay_rt, overlay_color, overlay_size, overlay_hover, overlay_filter_column, overlay_filter_value,
            feature_finding_type, feature_finding_ppm, feature_finding_noise, feature_finding_min_peak_rt, feature_finding_max_peak_rt, feature_finding_rt_tolerance,
            massql_statement,
            sychronization_session_id,
            chromatogram_options, 
            comment,
            map_plot_color_scale,
            map_plot_quantization_level,
            plot_theme]


@app.callback([ 
                  Output("synchronization_type", "value"),
                  Output("synchronization_type_dependency", "children")
              ],
              [
                  Input('url', 'search'), 
              ],
              [
                  State('synchronization_type', 'value'),
              ]
              )
def determine_url_only_parameters_synchronization(  search, 
                                    existing_synchronization_type):

    triggered_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    #print("TRIGGERED SYNCHRONIZATION URL PARSING", triggered_id, file=sys.stderr)

    synchronization_type  = _get_param_from_url(search, "", "synchronization_type", dash.no_update, old_value=existing_synchronization_type, no_change_default=dash.no_update)

    return [synchronization_type, "DEPENDENCY"]


def _handle_file_upload_small(filename , filecontent):
    # This is the small file upload handler
    upload_message = ""

    if len(filecontent) > 180000000: # Limit of 180MiB
        upload_message = "File Upload too big\n"
        return None, upload_message

    extension = os.path.splitext(filename)[1]
    original_filename = os.path.splitext(filename)[0]
    safe_filename = werkzeug.utils.secure_filename(original_filename) + "_" + str(uuid.uuid4()).replace("-", "")

    usi = None

    acceptable_extensions = [".mzML", ".mzXML", ".cdf", ".mzml", "mzxml", ".CDF", ".raw", ".RAW"]

    if extension in acceptable_extensions:
        temp_filename = os.path.join("temp", "{}{}".format(safe_filename, extension))
        data = filecontent.encode("utf8").split(b";base64,")[1]

        with open(temp_filename, "wb") as temp_file:
            temp_file.write(base64.decodebytes(data))

        usi = "mzspec:LOCAL:{}".format(os.path.basename(temp_filename))


    return usi, upload_message

def _handle_file_upload_big(filename, uploadid):
    uploaded_filename = os.path.join(TEMP_UPLOADFOLDER, uploadid, filename)

    extension = os.path.splitext(filename)[1]
    original_filename = os.path.splitext(filename)[0]
    safe_filename = werkzeug.utils.secure_filename(original_filename) + "_" + str(uuid.uuid4()).replace("-", "")

    acceptable_extensions = [".mzML", ".mzXML", ".cdf", ".mzml", "mzxml", ".CDF", ".raw", ".RAW"]

    if extension in acceptable_extensions:
        temp_filename = os.path.join("temp", "{}{}".format(safe_filename, extension))
        shutil.move(uploaded_filename, temp_filename)

        usi = "mzspec:LOCAL:{}".format(os.path.basename(temp_filename))
    
    return usi, ""


# Handling file upload
@app.callback([
                Output('usi', 'value'), 
                Output('usi2', 'value'), 
                Output('debug-output-2', 'children'),
                Output('upload_status', 'children'),
              ],
              [
                Input('url', 'search'), 
                Input('url', 'hash'), 
                Input('upload-data1', 'contents'),
                Input('upload-data2', 'isCompleted'),
                Input('sychronization_load_session_button', 'n_clicks'),
                Input('sychronization_interval', 'n_intervals'),
                Input('advanced_import_update_button', "n_clicks"),
                Input('auto_import_parameters', 'children')
              ],
              [
                  State('upload-data1', 'filename'),
                  State('upload-data2', 'fileNames'),
                  State('upload-data2', 'upload_id'),
                  State('sychronization_session_id', 'value'),

                  State('setting_json_area', 'value'),

                  State('usi', 'value'),
                  State('usi2', 'value'),
              ])
def update_usi(search, url_hash, 
                uploadfile1_filecontent_list,
                uploadfile2_iscompleted, 
                sychronization_load_session_button_clicks, sychronization_interval, advanced_import_update_button, auto_import_parameters, 
                uploadfile1_filename_list, uploadfile2_filenames, uploadfile2_uploadid, 
                sychronization_session_id,
                setting_json_area, 
                existing_usi,
                existing_usi2):
    usi = "mzspec:MSV000084494:GNPS00002_A3_p"
    usi2 = ""

    triggered_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    if uploadfile1_filename_list is not None or uploadfile2_filenames is not None and "upload-data" in triggered_id:
        total_files_uploaded = 0
        usi = existing_usi
        usi2 = existing_usi2
        upload_message = ""

        # Handling the small many files upload
        if uploadfile1_filename_list is not None and "upload-data1" in triggered_id:
            for i, filename in enumerate(uploadfile1_filename_list):
                filecontent = uploadfile1_filecontent_list[i]
                new_usi, new_upload_message = _handle_file_upload_small(filename , filecontent)
                
                if new_usi is not None:
                    total_files_uploaded += 1
                    usi = new_usi + "\n" + usi

        if uploadfile2_filenames is not None and "upload-data2" in triggered_id:
            print("UPLOADING FILE XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX", uploadfile2_iscompleted, uploadfile2_filenames)

            for i, filename in enumerate(uploadfile2_filenames):
                new_usi, new_upload_message = _handle_file_upload_big(filename, uploadfile2_uploadid)

                if new_usi is not None:
                    total_files_uploaded += 1
                    usi = new_usi + "\n" + usi

        upload_message += "{} Files Uploaded".format(total_files_uploaded)
        return [usi.lstrip(), usi2.lstrip(), dash.no_update, upload_message]

    session_dict = {}
    if "sychronization_load_session_button" in triggered_id or "sychronization_interval" in triggered_id:
        try:
            session_dict = _sychronize_load_state(sychronization_session_id, redis_client)
        except:
            pass

    # We clicked the button so we are going to load from the text area
    if "advanced_import_update_button" in triggered_id:
        try:
            session_dict = json.loads(setting_json_area)
        except:
            pass

    if "auto_import_parameters" in triggered_id:
        try:
            session_dict = json.loads(auto_import_parameters)
        except:
            pass

    # Resolving USI
    usi = _get_param_from_url(search, url_hash, "usi", usi, session_dict=session_dict, old_value=existing_usi, no_change_default=dash.no_update)
    usi2 = _get_param_from_url(search, url_hash, "usi2", usi2, session_dict=session_dict, old_value=existing_usi2, no_change_default=dash.no_update)

    return [usi, usi2, "Using URL USI", dash.no_update]
    
# Calculating which xic value to use
@app.callback(Output('xic_mz', 'value'),
              [
                Input('url', 'search'),
                Input('map-plot', 'clickData'),
                Input('sychronization_load_session_button', 'n_clicks'),
                Input('sychronization_interval', 'n_intervals'),
                Input('advanced_import_update_button', "n_clicks"),
                Input('auto_import_parameters', 'children'),
                Input('xicmz_clear_button', "n_clicks"),
                Input('xic_presets', 'value')
              ], 
              [
                  State('xic_mz', 'value'),
                  State('sychronization_session_id', 'value'),

                  State('setting_json_area', 'value'),
              ])
def determine_xic_target(search, clickData, sychronization_load_session_button_clicks, sychronization_interval, advanced_import_update_button, auto_import_parameters, xicmz_clear_button, xic_presets,
                        existing_xic, sychronization_session_id, setting_json_area):
    triggered_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    print("TRIGGERED XIC MZ", triggered_id, file=sys.stderr)

    # Clearing Button
    if "xicmz_clear_button" in triggered_id:
        return ""
    
    if "xic_presets" in triggered_id:
        return xic_presets

    try:
        if existing_xic is None:
            existing_xic = ""
        else:
            existing_xic = str(existing_xic)
    except:
        existing_xic = ""

    # Clicked points for MS1
    try:
        if "map-plot" in triggered_id:
            clicked_target = clickData["points"][0]

            # This is MS1
            if clicked_target["curveNumber"] == 0:
                mz_target = clicked_target["y"]

                if len(existing_xic) > 0:
                    return existing_xic + ";" + "{:.4f}".format(mz_target)

                return "{:.4f}".format(mz_target)

            # This is MS2
            elif clicked_target["curveNumber"] == 1:
                mz_target = clicked_target["y"]

                if len(existing_xic) > 0:
                    return existing_xic + ";" + "{:.4f}".format(mz_target)

                return "{:.4f}".format(mz_target)
            
            # This is Overlay/Feature Finding
            elif clicked_target["curveNumber"] == 2:
                mz_target = clicked_target["y"]

                if len(existing_xic) > 0:
                    return existing_xic + ";" + "{:.4f}".format(mz_target)

                return "{:.4f}".format(mz_target)
    except:
        pass

    session_dict = {}
    if "sychronization_load_session_button" in triggered_id or "sychronization_interval" in triggered_id:
        try:
            session_dict = _sychronize_load_state(sychronization_session_id, redis_client)
        except:
            pass

    # We clicked the button so we are going to load from the text area
    if "advanced_import_update_button" in triggered_id:
        try:
            session_dict = json.loads(setting_json_area)
        except:
            pass

    if "auto_import_parameters" in triggered_id:
        try:
            session_dict = json.loads(auto_import_parameters)
        except:
            pass

    xic_mz = _get_param_from_url(search, "", "xic_mz", dash.no_update, session_dict=session_dict, old_value=existing_xic, no_change_default=dash.no_update)
    xic_mz = _get_param_from_url(search, "", "xicmz", xic_mz, session_dict=session_dict, old_value=existing_xic, no_change_default=dash.no_update)

    return xic_mz


@cache.memoize()
def _create_map_fig(filename, 
                    map_selection=None, 
                    show_ms2_markers=True, 
                    polarity_filter="None", 
                    highlight_box=None, 
                    map_plot_quantization_level="Medium", 
                    map_plot_color_scale="Hot_r", 
                    template="plotly_light",
                    ms2marker_color="blue",
                    ms2marker_size=5):

    min_rt, max_rt, min_mz, max_mz = utils._determine_rendering_bounds(map_selection)

    import time
    start = time.time()

    if _is_worker_up():
        result = tasks.task_lcms_aggregate.delay(filename, min_rt, max_rt, min_mz, max_mz, polarity_filter=polarity_filter, map_plot_quantization_level=map_plot_quantization_level)

        # Waiting
        while(1):
            if result.ready():
                break
            sleep(0.1)
        agg_dict, msn_results = result.get()
        msn_results = pd.DataFrame(msn_results) # This comes as a list, due to serialization
    else:
        agg_dict, msn_results = tasks.task_lcms_aggregate(filename, min_rt, max_rt, min_mz, max_mz, polarity_filter=polarity_filter, map_plot_quantization_level=map_plot_quantization_level, cache=False)
        msn_results = pd.DataFrame(msn_results) # This comes as a list, due to serialization

    print("GETTING LCMS AGG", time.time() - start, file=sys.stderr, flush=True)

    start = time.time()
    lcms_fig = lcms_map._create_map_fig(agg_dict, msn_results, 
                                            map_selection=map_selection, 
                                            show_ms2_markers=show_ms2_markers, 
                                            polarity_filter=polarity_filter, 
                                            highlight_box=highlight_box,
                                            color_scale=map_plot_color_scale, 
                                            template=template,
                                            ms2marker_color=ms2marker_color,
                                            ms2marker_size=int(ms2marker_size))

    print("DRAWING LCMS MAP", time.time() - start, file=sys.stderr, flush=True)
    return lcms_fig

def _generate_qrcode_img(text_string):
    import base64
    import qrcode
    import io
    qr_image = qrcode.make(text_string, box_size=4)
    qr_bytes = io.BytesIO()
    qr_image.save(qr_bytes, format='png')
    qr_bytes.seek(0)

    encoded_image = base64.b64encode(qr_bytes.getvalue()).decode('ascii')
    qr_html_img = html.Img(src='data:image/png;base64,{}'.format(encoded_image))

    return qr_html_img

# This calls the actual feature finding so it can be cached
@cache.memoize()
def _perform_feature_finding(filename, feature_finding=None):
    import tasks

    # Checking if local or worker
    if _is_worker_up():
        # If we have the celery instance up, we'll push it
        result = tasks.task_featurefinding.delay(filename, json.dumps(feature_finding))

        # Waiting
        while(1):
            if result.ready():
                break
            sleep(3)
        features_list = result.get()
    else:
        features_list = tasks.task_featurefinding(filename, json.dumps(feature_finding))

    features_df = pd.DataFrame(features_list)
    
    # Forcing Types
    features_df["rt"] = features_df["rt"].astype(float)
    features_df["mz"] = features_df["mz"].astype(float)

    return features_df


@cache.memoize()
def _resolve_overlay(overlay_usi, overlay_mz, overlay_rt, overlay_filter_column, overlay_filter_value, overlay_size, overlay_color, overlay_hover, overlay_tabular_data=""):
    """This function handles getting data and formatting for the overlay, functions as caching middle shim

    Args:
        overlay_usi ([type]): [description]
        overlay_mz ([type]): [description]
        overlay_rt ([type]): [description]
        overlay_filter_column ([type]): [description]
        overlay_filter_value ([type]): [description]
        overlay_size ([type]): [description]
        overlay_color ([type]): [description]
        overlay_hover ([type]): [description]
    """

    
    if overlay_tabular_data is None or len(overlay_tabular_data) > 10000000:
        overlay_tabular_data = ""

    overlay_df = utils._resolve_overlay(overlay_usi, overlay_mz, overlay_rt, overlay_filter_column, overlay_filter_value, overlay_size, overlay_color, overlay_hover, overlay_tabular_data=overlay_tabular_data)
    
    return overlay_df

# Integrates the feature finding with the output plotly figure
def _integrate_feature_finding(filename, lcms_fig, map_selection=None, feature_finding=None):
    min_rt, max_rt, min_mz, max_mz = utils._determine_rendering_bounds(map_selection)

    # Checking if we should be detecting features
    features_df = pd.DataFrame()
    if feature_finding is not None:
        try:
            features_df = _perform_feature_finding(filename, feature_finding=feature_finding)

            features_df = features_df[features_df["rt"] > min_rt]
            features_df = features_df[features_df["rt"] < max_rt]
            features_df = features_df[features_df["mz"] > min_mz]
            features_df = features_df[features_df["mz"] < max_mz]

            #feature_overlay_fig = go.Scattergl(x=features_df["rt"], y=features_df["mz"], mode='markers', marker=dict(color='green', size=10, symbol="diamond", opacity=0.7), name="Feature Detection")

            feature_overlay_fig = px.scatter(features_df, x="rt", y="mz", hover_name="i")
            feature_overlay_fig.update_traces(marker=dict(symbol="diamond", color='green', size=10, opacity=0.7))

            _intermediate_fig = feature_overlay_fig.data[0]
            _intermediate_fig.name = "Feature Detection"
            _intermediate_fig.showlegend = True

            lcms_fig.add_trace(_intermediate_fig)
        except:
            #raise #DEBUG
            pass

    return lcms_fig, features_df

def _integrate_overlay(overlay_usi, lcms_fig, overlay_mz, overlay_rt, overlay_filter_column, overlay_filter_value, overlay_size, overlay_color, overlay_hover, map_selection=None, overlay_tabular_data=""):
    """Given data, we try to put it on top of the LCMS View

    Args:
        overlay_usi ([type]): [description]
        lcms_fig ([type]): [description]
        overlay_mz ([type]): [description]
        overlay_rt ([type]): [description]
        overlay_filter_column ([type]): [description]
        overlay_filter_value ([type]): [description]
        overlay_size ([type]): [description]
        overlay_color ([type]): [description]
        overlay_hover ([type]): [description]
        map_selection ([type], optional): [description]. Defaults to None.

    Returns:
        [type]: [description]
    """

    min_rt, max_rt, min_mz, max_mz = utils._determine_rendering_bounds(map_selection)

    # Adding in overlay data
    # Adding a few extra things to the figure
    try:
        overlay_df = _resolve_overlay(overlay_usi, overlay_mz, overlay_rt, overlay_filter_column, overlay_filter_value, overlay_size, overlay_color, overlay_hover, overlay_tabular_data=overlay_tabular_data)

        overlay_df = overlay_df[overlay_df["rt"] > min_rt]
        overlay_df = overlay_df[overlay_df["rt"] < max_rt]
        overlay_df = overlay_df[overlay_df["mz"] > min_mz]
        overlay_df = overlay_df[overlay_df["mz"] < max_mz]

        size_column = None
        color_column = None
        hover_column = None
        
        if "size" in overlay_df:
            size_column = "size"
            overlay_df[size_column] = overlay_df[size_column].clip(lower=1)

            # If we want to do other types of sizing
            #overlay_df[size_column] = np.log(overlay_df[size_column])
            #overlay_df[size_column] = overlay_df[size_column] / max(overlay_df[size_column]) * 10
        
        if "color" in overlay_df:
            color_column = "color"
            overlay_df[color_column] = overlay_df[color_column] / max(overlay_df[color_column]) * 10
        
        if "hover" in overlay_df:
            hover_column = "hover"

        if size_column is None and color_column is None:
            scatter_overlay_fig = px.scatter(overlay_df, x="rt", y="mz", hover_name=hover_column)
            scatter_overlay_fig.update_traces(marker=dict(color="gray", symbol="circle", opacity=0.7, size=10))
        elif size_column is not None and color_column is None:
            scatter_overlay_fig = px.scatter(overlay_df, x="rt", y="mz", size=size_column, hover_name=hover_column)
            scatter_overlay_fig.update_traces(marker=dict(color="gray", symbol="circle", opacity=0.7))
        elif size_column is None and color_column is not None:
            scatter_overlay_fig = px.scatter(overlay_df, x="rt", y="mz", color=color_column, hover_name=hover_column)
            scatter_overlay_fig.update_traces(marker=dict(size=10, symbol="circle", opacity=0.7))
        else:
            scatter_overlay_fig = px.scatter(overlay_df, x="rt", y="mz", color=color_column, size=size_column, hover_name=hover_column)
            scatter_overlay_fig.update_traces(marker=dict(symbol="circle", opacity=0.7))

        # Actually pulling out the figure and adding it
        _intermediate_fig = scatter_overlay_fig.data[0]
        _intermediate_fig.name = "Overlay"
        _intermediate_fig.showlegend = True

        lcms_fig.add_trace(_intermediate_fig)
    except:
        pass

    return lcms_fig

# Creating TIC plot
@app.callback([
                Output('tic-plot', 'figure'), 
                Output('tic-plot', 'config'),
                Output('loading_tic_plot', 'children')
              ],
              [Input('usi', 'value'), 
              Input('image_export_format', 'value'), 
              Input("plot_theme", "value"), 
              Input("tic_option", "value"),
              Input("polarity_filtering", "value"),
              Input("show_multiple_tic", "value")])
def draw_tic(usi, export_format, plot_theme, tic_option, polarity_filter, show_multiple_tic):
    # Calculating all TICs for all USIs
    all_usi = usi.split("\n")

    fig = dash.no_update
    status = "No Data"

    RENDER_MODE = "auto"
    # Making sure the data in the browser is actually svg
    if export_format == "svg":
        RENDER_MODE = "svg"

    if len(all_usi) > 1 and show_multiple_tic is True:
        all_usi_tic_df = []

        for current_usi in all_usi:
            if len(current_usi) < 2:
                continue

            try:
                tic_df = _perform_tic(current_usi, tic_option=tic_option, polarity_filter=polarity_filter)
                tic_df["USI"] = download._get_usi_display_filename(current_usi)
                all_usi_tic_df.append(tic_df)
            except:
                pass

        merged_tic_df = pd.concat(all_usi_tic_df)
        try:
            fig = px.line(merged_tic_df, x="rt", y="tic", title='TIC Plot', template=plot_theme, color="USI", render_mode=RENDER_MODE)
            status = "Ready"
        except:
            fig = dash.no_update
            status = "Draw Error"
    elif len(all_usi) > 0:
        tic_df = _perform_tic(usi.split("\n")[0], tic_option=tic_option, polarity_filter=polarity_filter)
        try:
            fig = px.line(tic_df, x="rt", y="tic", title='TIC Plot', template=plot_theme, render_mode=RENDER_MODE)
            status = "Ready"
        except:
            fig = dash.no_update
            status = "Draw Error"
        


    # For Drawing and Exporting
    graph_config = {
        "toImageButtonOptions":{
            "format": export_format,
            'filename': 'tic_plot',
            'height': None, 
            'width': None,
        }
    }

    return [fig, graph_config, status]

# Creating TIC plot
@app.callback([
                  Output('tic-plot2', 'figure'), 
                  Output('tic-plot2', 'config'),
                  Output('loading_tic_plot2', 'children')
              ],
              [
                  Input('usi2', 'value'), 
                  Input('image_export_format', 'value'), 
                  Input("plot_theme", "value"), 
                  Input("tic_option", "value"),
                  Input("polarity_filtering2", "value"),
                  Input("show_multiple_tic", "value")
              ])
def draw_tic2(usi, export_format, plot_theme, tic_option, polarity_filter, show_multiple_tic):
    # Calculating all TICs for all USIs
    all_usi = usi.split("\n")
    all_usi = [x for x in all_usi if len(x) > 2]

    fig = dash.no_update
    status = "No Data"

    RENDER_MODE = "auto"
    # Making sure the data in the browser is actually svg
    if export_format == "svg":
        RENDER_MODE = "svg"

    if len(all_usi) > 1 and show_multiple_tic is True:
        all_usi_tic_df = []

        for current_usi in all_usi:
            if len(current_usi) < 2:
                continue

            try:
                tic_df = _perform_tic(current_usi, tic_option=tic_option, polarity_filter=polarity_filter)
                tic_df["USI"] = download._get_usi_display_filename(current_usi)
                all_usi_tic_df.append(tic_df)
            except:
                pass

        merged_tic_df = pd.concat(all_usi_tic_df)
        fig = px.line(merged_tic_df, x="rt", y="tic", title='TIC Plot', template=plot_theme, color="USI", render_mode=RENDER_MODE)
        status = "Ready"
    elif len(all_usi) > 0:
        tic_df = _perform_tic(usi.split("\n")[0], tic_option=tic_option, polarity_filter=polarity_filter)
        fig = px.line(tic_df, x="rt", y="tic", title='TIC Plot', template=plot_theme, render_mode=RENDER_MODE)
        status = "Ready"

    # For Drawing and Exporting
    graph_config = {
        "toImageButtonOptions":{
            "format": export_format,
            'filename': 'tic_plot2',
            'height': None, 
            'width': None,
        }
    }

    return [fig, graph_config, status]

@cache.memoize()
def _perform_tic(usi, tic_option="TIC", polarity_filter="None"):
    remote_link, local_filename = _resolve_usi(usi)

    if _is_worker_up():
        result = tasks.task_tic.delay(local_filename, tic_option=tic_option, polarity_filter=polarity_filter)

        # Waiting
        while(1):
            if result.ready():
                break
            sleep(1)
        result = result.get()
        return pd.DataFrame(result)
    else:
        return pd.DataFrame(tasks.task_tic(local_filename, tic_option=tic_option, polarity_filter=polarity_filter))


@cache.memoize()
def _perform_xic(usi, all_xic_values, xic_tolerance, xic_ppm_tolerance, xic_tolerance_unit, rt_min, rt_max, polarity_filter, get_ms2=False):
    # This is the business end of XIC extraction
    remote_link, local_filename = _resolve_usi(usi)

    # If we are able, we will split up the query, one per file
    return xic.xic_file(local_filename, all_xic_values, xic_tolerance, xic_ppm_tolerance, xic_tolerance_unit, rt_min, rt_max, polarity_filter, get_ms2=get_ms2)

@cache.memoize()
def _perform_batch_xic(usi_list, usi1_list, usi2_list, xic_norm, all_xic_values, xic_tolerance, xic_ppm_tolerance, xic_tolerance_unit, rt_min, rt_max, polarity_filter):
    GET_MS2 = False
    ms2_data = {}

    xic_df_list = []
    
    if _is_worker_up():
        result_list = []

        for usi_element in usi_list:
            if len(usi_list) == 1 and len(all_xic_values) == 1:
                GET_MS2 = True

            # Doing it async with tasks
            remote_link, local_filename = _resolve_usi(usi_element)

            for xic_value in all_xic_values:
                result = tasks.task_xic.delay(local_filename, json.dumps([xic_value]), xic_tolerance, xic_ppm_tolerance, xic_tolerance_unit, rt_min, rt_max, polarity_filter, get_ms2=GET_MS2)
                result_dict = {}
                result_dict["result"] = result
                result_dict["usi_element"] = usi_element
                result_list.append(result_dict)

        # Waiting
        for result_dict in result_list:
            result = result_dict["result"]
            usi_element = result_dict["usi_element"]
            while(1):
                if result.ready():
                    break
                sleep(0.5)

            # Waiting on results
            xic_list, ms2_data = result.get()
            xic_df = pd.DataFrame(xic_list)

            xic_dict = {}
            xic_dict["df"] = xic_df
            xic_dict["usi"] = usi_element
            xic_df_list.append(xic_dict)

    else:
        for usi_element in usi_list:
            if len(usi_list) == 1 and len(all_xic_values) == 1:
                GET_MS2 = True
            
            # Doing it all local
            xic_df, ms2_data = _perform_xic(usi_element, all_xic_values, xic_tolerance, xic_ppm_tolerance, xic_tolerance_unit, rt_min, rt_max, polarity_filter, get_ms2=GET_MS2)

            xic_dict = {}
            xic_dict["df"] = xic_df
            xic_dict["usi"] = usi_element
            xic_df_list.append(xic_dict)
    
    # Performing Normalization and formatting
    df_long_list = []
    for xic_dict in xic_df_list:
        try:
            xic_df = xic_dict["df"]
            usi_element = xic_dict["usi"]

            # Performing Normalization only if we have multiple XICs available
            if xic_norm is True:
                try:
                    for key in xic_df.columns:
                        if key == "rt":
                            continue
                        xic_df[key] = xic_df[key] / max(xic_df[key])
                except:
                    pass

            # Formatting for Plotting
            target_names = list(xic_df.columns)
            target_names.remove("rt")
            df_long = pd.melt(xic_df, id_vars="rt", value_vars=target_names)
            df_long["USI"] = usi_element

            if usi_element in usi1_list:
                df_long["GROUP"] = "TOP"
            else:
                df_long["GROUP"] = "BOTTOM"

            df_long_list.append(df_long)
        except:
            pass

    merged_df_long = pd.concat(df_long_list)

    return merged_df_long, ms2_data

def _perform_chromatogram_extraction(usi_list, chromatogram_list, rt_min, rt_max):
    usi = usi_list[0]

    df_list = []
    for usi in usi_list:
        remote_link, local_filename = _resolve_usi(usi)

        for chromatogram_value in chromatogram_list:
            try:
                chromatogram_df = xic.get_chromatogram(local_filename, chromatogram_value)
                chromatogram_df["USI"] = usi
                df_list.append(chromatogram_df)
            except:
                pass

    merged_df = pd.concat(df_list)

    merged_df = merged_df[merged_df["rt"] < rt_max]
    merged_df = merged_df[merged_df["rt"] > rt_min]

    return merged_df

def _is_worker_up():
    """Gives us utility function to tell is celery is up and running

    Returns:
        [type]: [description]
    """

    # Cheap Check
    return WORKER_UP

    # Expensive Check
    try:
        result = tasks.task_computeheartbeat.delay()
        result.task_id

        return True
    except:
        return False


def _integrate_files(long_data_df, xic_integration_type):
    grouped_df = pd.DataFrame()
    # Integrating Data
    if xic_integration_type == "MS1SUM":
        grouped_df = long_data_df.groupby(["variable", "USI", "GROUP"]).sum().reset_index()
        grouped_df = grouped_df.drop("rt", axis=1)
    elif xic_integration_type == "AUC":
        intermediate_grouped_df = long_data_df.groupby(["variable", "USI", "GROUP"])
        grouped_df = long_data_df.groupby(["variable", "USI", "GROUP"]).sum().reset_index()
        grouped_df["value"] = [integrate.trapz(group_df["value"], x=group_df["rt"]) for name, group_df in intermediate_grouped_df]
        grouped_df = grouped_df.drop("rt", axis=1)
    elif xic_integration_type == "MAXPEAKHEIGHT":
        grouped_df = long_data_df.groupby(["variable", "USI", "GROUP"]).max().reset_index()
        grouped_df = grouped_df.drop("rt", axis=1)

    return grouped_df

##################################
# XIC Chromatogram Options
##################################
@app.callback(Output('chromatogram_options', 'options'),
              [
                  Input('usi', 'value'), 
                  Input('usi2', 'value'), 
              ])
def create_chromatogram_options(usi, usi2):
    all_usi = usi.split("\n")
    remote_link, local_filename = _resolve_usi(all_usi[0])

    chromatogram_list = tasks.task_chromatogram_options(local_filename)

    options = []
    for term in chromatogram_list:
        options.append({'label': term, 'value': term})

    return options


# Creating XIC plot
@app.callback([
                Output('xic-plot', 'figure'), 
                Output('xic-plot', 'config'), 
                Output("xic-heatmap", "children"),
                Output("integration-table", "children"), 
                Output("integration-boxplot", "children"),
                Output("integration-scatter", "children"),
                Output('loading_xic_plot', 'children')
              ],
              [
                  Input('usi', 'value'), 
                  Input('usi2', 'value'), 
                  Input('xic_mz', 'value'), 
                  Input('xic_formula', 'value'), 
                  Input('xic_peptide', 'value'), 
                  Input('xic_tolerance', 'value'),
                  Input('xic_ppm_tolerance', 'value'),
                  Input('xic_tolerance_unit', 'value'),
                  Input('xic_rt_window', 'value'),
                  Input('xic_integration_type', 'value'),
                  Input('xic_norm', 'value'),
                  Input('xic_file_grouping', 'value'),
                  Input("chromatogram_options", "value"),
                  Input('polarity_filtering', 'value'),
                  Input('image_export_format', 'value'), 
                  Input("plot_theme", "value"),
                  Input('map_plot_color_scale', 'value'),
              ])
def draw_xic(usi, usi2, xic_mz, xic_formula, xic_peptide, xic_tolerance, xic_ppm_tolerance, xic_tolerance_unit, xic_rt_window, xic_integration_type, xic_norm, xic_file_grouping, chromatogram_list, polarity_filter, export_format, plot_theme, map_plot_color_scale):
    triggered_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    print("TRIGGERED XIC PLOT", dash.callback_context.triggered, file=sys.stderr, flush=True)

    # For Drawing and Exporting
    graph_config = {
        "toImageButtonOptions":{
            "format": export_format,
            'filename': 'xic_plot',
            'height': None, 
            'width': None,
        }
    }

    usi1_list = usi.split("\n")
    usi2_list = usi2.split("\n")

    usi1_list = [usi for usi in usi1_list if len(usi) > 8] # Filtering out empty USIs
    usi2_list = [usi for usi in usi2_list if len(usi) > 8] # Filtering out empty USIs

    usi_list = usi1_list + usi2_list
    usi_list = usi_list[:MAX_LCMS_FILES]

    all_xic_values = []

    # Getting all XIC values from m/z entry
    try:
        for xic_value in xic_mz.split(";"):
            if "=" in xic_value:
                xic_name = xic_value.split("=")[0]
                xic_float = float(xic_value.split("=")[1])
                all_xic_values.append((str(xic_name), float(xic_float)))
            else:
                all_xic_values.append((str(xic_value), float(xic_value)))
    except:
        pass

    # Getting all XIC values from Formula
    try:
        adducts_to_report = ["M+H", "M+Na", "M+K"]
        for adduct in adducts_to_report:
            f = Formula(xic_formula)
            exact_mass = f.isotope.mass
            adduct_mz, charge = get_adduct_mass(exact_mass, adduct)
            all_xic_values.append((str(adduct), float(adduct_mz)))
    except:
        pass

    # Getting all XIC values from Peptide
    try:
        for charge in range(2, 6):
            xic_mz = mass.calculate_mass(sequence=xic_peptide, charge=charge)
            all_xic_values.append(("Charge {} - {:.2f}".format(charge, xic_mz), float(xic_mz)))
    except:
        pass


    # Parsing Tolerances
    parsed_xic_da_tolerance = 0.5
    try:
        parsed_xic_da_tolerance = float(xic_tolerance)
    except:
        pass

    parsed_xic_ppm_tolerance = 50
    try:
        parsed_xic_ppm_tolerance = float(xic_ppm_tolerance)
    except:
        pass

    rt_min = 0
    rt_max = 10000000
    try:
        rt_min = float(xic_rt_window.split("-")[0])
        rt_max = float(xic_rt_window.split("-")[1])
    except:
        try:
            rt_value = float(xic_rt_window)
            rt_min = rt_value - 0.5
            rt_max = rt_value + 0.5
        except:
            pass

    # Exiting if we don't have any valid XIC values
    if len(all_xic_values) == 0 and len(chromatogram_list) == 0:
        return [placeholder_xic_plot, graph_config, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update]

    merged_df_long = pd.DataFrame()
    if len(all_xic_values) > 0:
        # Performing XIC for all USI in the list
        merged_df_long, ms2_data = _perform_batch_xic(usi_list, usi1_list, usi2_list, xic_norm, all_xic_values, parsed_xic_da_tolerance, parsed_xic_ppm_tolerance, xic_tolerance_unit, rt_min, rt_max, polarity_filter)

    # Looking at chromatograms only if a single file exists
    if len(chromatogram_list) > 0:
        chrom_df = _perform_chromatogram_extraction(usi_list, chromatogram_list, rt_min, rt_max)
        chrom_df["GROUP"] = "TOP"
        merged_df_long = pd.concat([merged_df_long, chrom_df])

    # Limit the plotting USIs, but not the integrals below
    plotting_df = merged_df_long
    plot_usi_list = usi_list[:MAX_XIC_PLOT_LCMS_FILES]
    plotting_df = plotting_df[plotting_df["USI"].isin(plot_usi_list)]

    # Cleaning up the USI to show
    plotting_df["USI"] = plotting_df["USI"].apply(lambda x: download._get_usi_display_filename(x))

    RENDER_MODE = "auto"
    # Making sure the data in the browser is actually svg
    if export_format == "svg":
        RENDER_MODE = "svg"

    if len(plot_usi_list) == 1:
        if xic_file_grouping == "FILE":
            height = 400
            fig = px.scatter(plotting_df, x="rt", y="value", color="variable", title='XIC Plot - Single File', height=height, template=plot_theme, render_mode=RENDER_MODE)
        else:
            height = 400 * (len(all_xic_values) + len(chromatogram_list))
            fig = px.scatter(plotting_df, x="rt", y="value", facet_row="variable", title='XIC Plot - Single File', height=height, template=plot_theme, render_mode=RENDER_MODE)
    else:
        if xic_file_grouping == "FILE":
            height = 400 * len(plot_usi_list)
            fig = px.scatter(plotting_df, x="rt", y="value", color="variable", facet_row="USI", title='XIC Plot - Grouped Per File', height=height, template=plot_theme, render_mode=RENDER_MODE)
        elif xic_file_grouping == "MZ":
            height = 400 * (len(all_xic_values) + len(chromatogram_list))
            fig = px.scatter(plotting_df, x="rt", y="value", color="USI", facet_row="variable", title='XIC Plot - Grouped Per M/Z', height=height, template=plot_theme, render_mode=RENDER_MODE)
        elif xic_file_grouping == "GROUP":
            height = 400 * (len(all_xic_values) + len(chromatogram_list))
            fig = px.scatter(plotting_df, x="rt", y="value", color="GROUP", facet_row="variable", title='XIC Plot - By Group', height=height, template=plot_theme, render_mode=RENDER_MODE)

    # Making these scatter plots into lines
    fig.update_traces(mode='lines')

    # Plotting the MS2 on the XIC
    if len(usi_list) == 1 and len(all_xic_values) == 1:
        try:
            all_ms2_ms1_int = ms2_data["all_ms2_ms1_int"]
            all_ms2_rt = ms2_data["all_ms2_rt"]
            all_ms2_scan = ms2_data["all_ms2_scan"]

            if len(all_ms2_scan) > 0:
                scatter_fig = go.Scatter(x=all_ms2_rt, y=all_ms2_ms1_int, mode='markers', customdata=all_ms2_scan, marker=dict(color='red', size=8, symbol="x"), name="MS2 Acquisitions")
                fig.add_trace(scatter_fig)
        except:
            pass

    # Plotting the XIC Heatmap
    xic_heatmap_graph = dash.no_update
    if len(all_xic_values) > 0 or len(chromatogram_list) > 0:
        xic_heatmap_graph_list = []
        all_xic_targets = list(set(merged_df_long["variable"]))
        all_xic_targets.sort()

        for xic_target in all_xic_targets:
            try:
                filtered_df_long = merged_df_long[merged_df_long["variable"] == xic_target]
                all_usi_list = list(set(filtered_df_long["USI"]))
                all_usi_list.sort()
                filtered_df_long["USI"] = filtered_df_long["USI"].apply(lambda x: all_usi_list.index(x))

                cvs = ds.Canvas(plot_width=50, plot_height=len(all_usi_list))
                agg = cvs.points(filtered_df_long, 'rt', 'USI', agg=ds.sum("value"))

                # Shortening the actual name of the file
                all_usi_list = [download._get_usi_display_filename(x) for x in all_usi_list]

                # Clipping
                import numpy as np
                min_value = agg.min().values
                agg.values = np.nan_to_num(agg.values, nan=min_value)
                agg.values = np.clip(agg.values, min_value, 10000000000000000)
                #agg.values = np.log10(agg.values)

                xic_heatmap_fig = px.imshow(agg, origin='lower', y=all_usi_list, labels={'color':'Log10(abundance)'}, height=200 + 25 * len(all_usi_list), template=plot_theme, title='XIC Heatmap - {} m/z'.format(xic_target),
                                            color_continuous_scale=map_plot_color_scale)
                xic_heatmap_graph_list.append(dcc.Graph(figure=xic_heatmap_fig, config=graph_config))
            except:
                pass

        if len(xic_heatmap_graph_list) > 0:
            xic_heatmap_graph = xic_heatmap_graph_list


    ##################################
    # Integration Results Section
    ##################################

    table_graph = dash.no_update
    box_graph = dash.no_update
    integration_scatter_graph = dash.no_update

    try:
        # Doing actual integration
        integral_df = _integrate_files(merged_df_long, xic_integration_type)
        integral_df["USI"] = integral_df["USI"].apply(lambda x: download._get_usi_display_filename(x))

        # Creating a table
        table_graph = dash_table.DataTable(
            id='table',
            columns=[{"name": i, "id": i} for i in integral_df.columns],
            data=integral_df.to_dict('records'),
            sort_action="native",
            page_action="native",
            page_size= 10,
            filter_action="native",
            export_format="csv"
        )

        # Creating a box plot
        box_height = 250 * int(float(len(all_xic_values)) / 3.0 + 0.1)
        box_fig = px.box(integral_df, x="GROUP", y="value", facet_col="variable", facet_col_wrap=3, color="GROUP", points="all", height=box_height, boxmode="overlay", template=plot_theme)
        box_fig.update_traces(pointpos=0)
        box_graph = dcc.Graph(figure=box_fig, config=graph_config)

        # Plotting the Scatter Plot
        # if len(all_xic_values) > 0 or len(chromatogram_list) > 0:
        #     scatter_fig = px.scatter(x=[0, 1, 2, 3, 4], y=[0, 1, 4, 9, 16])
        #     print(integral_df)
        #     integration_scatter_graph = dash.no_update
    except:
        pass


    return [fig, graph_config, xic_heatmap_graph, table_graph, box_graph, integration_scatter_graph, dash.no_update]


@app.callback([
                Output('map_plot_zoom', 'children'),
                Output('highlight_box', 'children'),
                Output("map_plot_rt_min", 'value'),
                Output("map_plot_rt_max", 'value'),
                Output("map_plot_mz_min", 'value'),
                Output("map_plot_mz_max", 'value'),
                ],
              [
                Input('url', 'search'), 
                Input('usi', 'value'), 
                Input('map-plot', 'relayoutData'),
                Input('map_plot_update_range_button', 'n_clicks'),
                Input('sychronization_load_session_button', 'n_clicks'),
                Input('sychronization_interval', 'n_intervals'),
                Input('advanced_import_update_button', "n_clicks"),
                Input('auto_import_parameters', 'children'),
              ],
              [ 
                State("map_plot_rt_min", 'value'),
                State("map_plot_rt_max", 'value'),
                State("map_plot_mz_min", 'value'),
                State("map_plot_mz_max", 'value'),

                State("map_plot_zoom", 'children'),

                State('sychronization_session_id', 'value'),

                State('setting_json_area', 'value'),
              ])
def determine_plot_zoom_bounds(url_search, usi, 
                                map_selection, map_plot_update_range_button, sychronization_load_session_button, sychronization_interval, advanced_import_update_button, auto_import_parameters,
                                map_plot_rt_min, map_plot_rt_max, map_plot_mz_min, map_plot_mz_max, existing_map_plot_zoom, 
                                sychronization_session_id, setting_json_area):

    
    print("ALL TRIGGERS", [p['prop_id'] for p in dash.callback_context.triggered], file=sys.stderr, flush=True)

    triggered_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    usi_list = usi.split("\n")
    remote_link, local_filename = _resolve_usi(usi_list[0])

    session_dict = {}

    if "sychronization_load_session_button" in triggered_id or "sychronization_interval" in triggered_id:
        try:
            session_dict = _sychronize_load_state(sychronization_session_id, redis_client)
        except:
            pass
    
    # We clicked the button so we are going to load from the text area
    if "advanced_import_update_button" in triggered_id:
        try:
            session_dict = json.loads(setting_json_area)
        except:
            pass

    if "auto_import_parameters" in triggered_id:
        try:
            session_dict = json.loads(auto_import_parameters)
        except:
            pass

    priority = "url"

    if "map-plot" in triggered_id:
        priority = "ui"

    if "map_plot_update_range_button" in triggered_id:
        priority = "ui_update_range"
    
    if "sychronization_load_session_button" in triggered_id or "sychronization_interval" in triggered_id or "advanced_import_update_button" in triggered_id or "auto_import_parameters" in triggered_id:
        priority = "session"

    current_map_selection, highlight_box, min_rt, max_rt, min_mz, max_mz = _resolve_map_plot_selection(url_search, 
                                                                                                        usi, 
                                                                                                        local_filename, 
                                                                                                        ui_map_selection=map_selection,
                                                                                                        map_plot_rt_min=map_plot_rt_min,
                                                                                                        map_plot_rt_max=map_plot_rt_max,
                                                                                                        map_plot_mz_min=map_plot_mz_min,
                                                                                                        map_plot_mz_max=map_plot_mz_max, 
                                                                                                        session_dict=session_dict,
                                                                                                        priority=priority)

    current_map_plot_zoom_string = json.dumps(current_map_selection)

    if current_map_plot_zoom_string == existing_map_plot_zoom:
        return  [dash.no_update, dash.no_update, min_rt, max_rt, min_mz, max_mz]

    highlight_box_string = ""
    try:
        highlight_box_string = json.dumps(highlight_box)
    except:
        pass

    print("MAP SELECTION", map_selection, file=sys.stderr, flush=True)
    print("NEW SELECTION", current_map_selection, highlight_box, file=sys.stderr, flush=True)
    print("EXISTING PLOT ZOOM", existing_map_plot_zoom, file=sys.stderr, flush=True)

    return [current_map_plot_zoom_string, highlight_box_string, min_rt, max_rt, min_mz, max_mz]
    
# Downloading the files
@app.callback([Output('loading_file_download', 'children')],
              [Input('usi', 'value'), Input('usi2', 'value')])
def render_initial_file_load(usi, usi2):
    usi1_list = usi.split("\n")
    usi2_list = usi2.split("\n")

    usi1_list = [usi for usi in usi1_list if len(usi) > 8] # Filtering out empty USIs
    usi2_list = [usi for usi in usi2_list if len(usi) > 8] # Filtering out empty USIs
    
    usi_list = usi1_list + usi2_list
    usi_list = usi_list[:MAX_LCMS_FILES]

    status = "Ready"
    if len(usi1_list) > 0:
        try:
            remote_link, local_filename = _resolve_usi(usi1_list[0])

            # Kicking off caching of data, asychronously
            tasks.massql_cache(local_filename)
        except:
            status = "USI1 Loading Error"
            return [status]
            
    if len(usi2_list) > 0:
        try:
            _resolve_usi(usi2_list[0])
        except:
            status = "USI2 Loading Error"
            return [status]
    
    


    return [status]


# Inspiration for structure from
# https://github.com/plotly/dash-datashader
# https://community.plotly.com/t/heatmap-is-slow-for-large-data-arrays/21007/2

@app.callback([
                Output('map-plot', 'figure'), 
                Output('map-plot', 'config'), 
                Output('download-link', 'children'), 
                Output("feature-finding-table", 'children'),
                Output('loading_map_plot', 'children')
                ],
              [
                Input('url', 'search'), 
                Input('usi', 'value'), 
                Input('map_plot_zoom', 'children'), 
                Input('highlight_box', 'children'),
                Input('map_plot_quantization_level', 'value'), 
                Input('map_plot_color_scale', 'value'),
                Input('show_ms2_markers', 'value'),
                Input('ms2marker_color', 'value'),
                Input('ms2marker_size', 'value'),
                Input('polarity_filtering', 'value'),
                Input('overlay_usi', 'value'),
                Input('overlay_mz', 'value'),
                Input('overlay_rt', 'value'),
                Input('overlay_size', 'value'),
                Input('overlay_color', 'value'),
                Input('overlay_hover', 'value'),
                Input('overlay_filter_column', 'value'),
                Input('overlay_filter_value', 'value'),
                Input('overlay_tabular_data', 'value'),

                Input('feature_finding_type', 'value'),
                Input('run_feature_finding_button', 'n_clicks'),
                Input('run_massql_query_button', 'n_clicks'),

                Input('image_export_format', 'value'),
                Input("plot_theme", "value")
              ],
              [
                State('feature_finding_ppm', 'value'),
                State('feature_finding_noise', 'value'),
                State('feature_finding_min_peak_rt', 'value'),
                State('feature_finding_max_peak_rt', 'value'),
                State('feature_finding_rt_tolerance', 'value'),
                State('massql_statement', 'value'),
              ])
def draw_file(url_search, usi, 
                map_plot_zoom, highlight_box_zoom, map_plot_quantization_level, map_plot_color_scale,
                show_ms2_markers, ms2marker_color, ms2marker_size, polarity_filter, 
                overlay_usi, overlay_mz, overlay_rt, overlay_size, overlay_color, overlay_hover, overlay_filter_column, overlay_filter_value, overlay_tabular_data,
                feature_finding_type,
                run_feature_finding_button_click,
                run_massql_query_button_click,
                export_format,
                plot_theme,
                feature_finding_ppm,
                feature_finding_noise,
                feature_finding_min_peak_rt,
                feature_finding_max_peak_rt, 
                feature_finding_rt_tolerance,
                massql_statement):

    triggered_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    print("TRIGGERED MAP PLOT", triggered_id, file=sys.stderr, flush=True)

    usi_list = usi.split("\n")

    remote_link, local_filename = _resolve_usi(usi_list[0])

    if show_ms2_markers == 1:
        show_ms2_markers = True
    else:
        show_ms2_markers = False

    # Feature Finding parameters
    table_graph = dash.no_update
    if feature_finding_type == "Off":
        feature_finding_params = None
    else:
        feature_finding_params = {}
        feature_finding_params["type"] = feature_finding_type
        feature_finding_params["params"] = {}
        feature_finding_params["params"]["feature_finding_ppm"] = feature_finding_ppm
        feature_finding_params["params"]["feature_finding_noise"] = feature_finding_noise
        feature_finding_params["params"]["feature_finding_min_peak_rt"] = feature_finding_min_peak_rt
        feature_finding_params["params"]["feature_finding_max_peak_rt"] = feature_finding_max_peak_rt
        feature_finding_params["params"]["feature_finding_rt_tolerance"] = feature_finding_rt_tolerance

        feature_finding_params["params"]["massql_statement"] = massql_statement

    current_map_selection = json.loads(map_plot_zoom)
    highlight_box = None
    try:
        highlight_box = json.loads(highlight_box_zoom)
    except:
        pass

    # Doing LCMS Map
    map_fig = _create_map_fig(local_filename, 
                                map_selection=current_map_selection, 
                                show_ms2_markers=show_ms2_markers, 
                                polarity_filter=polarity_filter, 
                                highlight_box=highlight_box, 
                                map_plot_quantization_level=map_plot_quantization_level,
                                map_plot_color_scale=map_plot_color_scale,
                                template=plot_theme,
                                ms2marker_color=ms2marker_color,
                                ms2marker_size=ms2marker_size)

    # Adding on Feature Finding data
    map_fig, features_df = _integrate_feature_finding(local_filename, map_fig, map_selection=current_map_selection, feature_finding=feature_finding_params)

    # Adding on Overlay Data
    map_fig = _integrate_overlay(overlay_usi, map_fig, overlay_mz, overlay_rt, overlay_filter_column, overlay_filter_value, overlay_size, overlay_color, overlay_hover, map_selection=current_map_selection, overlay_tabular_data=overlay_tabular_data)

    try:
        # Creating a table
        table_graph = dash_table.DataTable(
            id='table',
            columns=[{"name": i, "id": i} for i in features_df.columns],
            data=features_df.to_dict('records'),
            sort_action="native",
            page_action="native",
            page_size= 10,
            filter_action="native",
            export_format="csv"
        )
    except:
        pass

    # Heatmap Config
    graph_config = {
        "toImageButtonOptions":{
            "format": export_format,
            'filename': werkzeug.utils.secure_filename('map_plot_{}'.format(os.path.basename(local_filename))),
            'height': None, 
            'width': None,
        }
    }

    return [map_fig, graph_config, remote_link, table_graph, "Ready"]


@app.callback([
                Output('map-plot2', 'figure'),
                Output('map-plot2', 'config'), 
                Output('loading_map_plot2', 'children')
              ],
              [
                Input('usi2', 'value'), 
                Input('map_plot_zoom', 'children'),
                Input('map_plot_quantization_level', 'value'), 
                Input('map_plot_color_scale', 'value'),
                Input('show_ms2_markers', 'value'),
                Input("show_lcms_2nd_map", "value"),
                Input('polarity_filtering2', 'value'),
                Input('image_export_format', 'value'),
                Input('plot_theme', 'value')
              ])
def draw_file2( usi, 
                map_plot_zoom, map_plot_quantization_level, map_plot_color_scale,
                show_ms2_markers, show_lcms_2nd_map, polarity_filter, export_format, plot_theme):

    if show_lcms_2nd_map is False:
        return [dash.no_update, dash.no_update, "Not Shown"]

    triggered_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    usi_list = usi.split("\n")

    remote_link, local_filename = _resolve_usi(usi_list[0])

    if show_ms2_markers == 1:
        show_ms2_markers = True
    else:
        show_ms2_markers = False

    current_map_selection = json.loads(map_plot_zoom)

    # Doing LCMS Map
    map_fig = _create_map_fig(local_filename, 
                                map_selection=current_map_selection, 
                                show_ms2_markers=show_ms2_markers, 
                                polarity_filter=polarity_filter, 
                                map_plot_quantization_level=map_plot_quantization_level,
                                map_plot_color_scale=map_plot_color_scale,
                                template=plot_theme)

    # Heatmap Config
    graph_config = {
        "toImageButtonOptions":{
            "format": export_format,
            'filename': werkzeug.utils.secure_filename('map_plot_{}'.format(os.path.basename(local_filename))),
            'height': None, 
            'width': None,
        }
    }

    return [map_fig, graph_config, "Ready"]


@app.callback(Output('run-gnps-mzmine-link', 'href'),
              [
              Input("usi", "value"),
              Input("usi2", "value"),
              Input("feature_finding_type", "value"),
              Input("feature_finding_ppm", "value"),
              Input("feature_finding_noise", "value"),
              Input("feature_finding_min_peak_rt", "value"),
              Input("feature_finding_max_peak_rt", "value"),
              Input("feature_finding_rt_tolerance", "value"),
              ])
def create_gnps_mzmine2_link(usi, usi2, feature_finding_type, feature_finding_ppm, feature_finding_noise, feature_finding_min_peak_rt, feature_finding_max_peak_rt, feature_finding_rt_tolerance):
    import urllib.parse

    g1_list = []
    g2_list = []

    usi_list = usi.split("\n")
    for usi_value in usi_list:
        try:
            ccms_path = download._usi_to_ccms_path(usi_value)
            if ccms_path is not None:
                g1_list.append(ccms_path)
        except:
            pass
    
    usi_list2 = usi2.split("\n")
    for usi_value in usi_list2:
        try:
            ccms_path = download._usi_to_ccms_path(usi_value)
            if ccms_path is not None:
                g2_list.append(ccms_path)
        except:
            pass

    gnps_url = "https://proteomics2.ucsd.edu/ProteoSAFe/index.jsp?params="
    parameters = {}
    parameters["workflow"] = "LC_MZMINE2"
    parameters["desc"] = "MZmine2 Feature Finding - From GNPS LCMS Viewer"
    
    parameters["spec_on_server"] = ";".join(g1_list)
    parameters["spec_on_server_group2"] = ";".join(g2_list)

    parameters["MZMINE_BATCHPRESET"] = "Generic_Batch_Base.xml"
    parameters["feature_finding_ppm"] = feature_finding_ppm
    parameters["feature_finding_noise"] = feature_finding_noise
    parameters["feature_finding_min_peak_rt"] = feature_finding_min_peak_rt
    parameters["feature_finding_max_peak_rt"] = feature_finding_max_peak_rt
    parameters["feature_finding_rt_tolerance"] = feature_finding_rt_tolerance

    gnps_url = gnps_url + urllib.parse.quote(json.dumps(parameters))

    return gnps_url


@app.callback([
                Output('query_link', 'href'),
                Output('page_parameters', 'children'),
                Output('qrcode', 'children'),
              ],  
              [
                Input('usi', 'value'), 
                Input('usi2', 'value'), 
                Input('xic_mz', 'value'), 
                Input('xic_formula', 'value'), 
                Input('xic_peptide', 'value'), 
                Input('xic_tolerance', 'value'),
                Input('xic_ppm_tolerance', 'value'),
                Input('xic_tolerance_unit', 'value'),
                Input('xic_rt_window', 'value'),
                Input("xic_norm", "value"),
                Input('xic_file_grouping', 'value'),
                Input('xic_integration_type', 'value'),
                Input("show_ms2_markers", "value"),
                Input('ms2marker_color', 'value'),
                Input('ms2marker_size', 'value'),
                Input("ms2_identifier", "value"),
                Input("map_plot_zoom", "children"),

                Input('polarity_filtering', 'value'),
                Input('polarity_filtering2', 'value'),

                Input("show_lcms_2nd_map", "value"),
                Input("tic_option", "value"),
                Input("overlay_usi", "value"),
                Input("overlay_mz", "value"),
                Input("overlay_rt", "value"),
                Input("overlay_color", "value"),
                Input("overlay_size", "value"),
                Input("overlay_hover", "value"),
                Input('overlay_filter_column', 'value'),
                Input('overlay_filter_value', 'value'),
                Input("feature_finding_type", "value"),
                Input("feature_finding_ppm", "value"),
                Input("feature_finding_noise", "value"),
                Input("feature_finding_min_peak_rt", "value"),
                Input("feature_finding_max_peak_rt", "value"),
                Input("feature_finding_rt_tolerance", "value"),

                Input("massql_statement", "value"),

                Input("sychronization_save_session_button", "n_clicks"),
                Input("sychronization_set_type_button", "n_clicks"),
                Input("sychronization_session_id", "value"),
                Input("synchronization_leader_token", "value"),

                Input("chromatogram_options", "value"),

                Input("comment", "value"),

                Input("map_plot_color_scale", "value"),
                Input("map_plot_quantization_level", "value"),

                Input("plot_theme", "value"),
              ],
              [
                  State('synchronization_type', 'value')
              ])
def create_link(usi, usi2, xic_mz, xic_formula, xic_peptide, 
                xic_tolerance, xic_ppm_tolerance, xic_tolerance_unit, xic_rt_window, xic_norm, xic_file_grouping, 
                xic_integration_type, show_ms2_markers, ms2marker_color, ms2marker_size,
                ms2_identifier, map_plot_zoom, polarity_filtering, polarity_filtering2, show_lcms_2nd_map, tic_option,
                overlay_usi, overlay_mz, overlay_rt, overlay_color, overlay_size, overlay_hover, overlay_filter_column, overlay_filter_value,
                feature_finding_type, feature_finding_ppm, feature_finding_noise, feature_finding_min_peak_rt, feature_finding_max_peak_rt, feature_finding_rt_tolerance,
                massql_statement,
                sychronization_save_session_button_clicks, sychronization_set_type_button_clicks, sychronization_session_id, synchronization_leader_token, 
                chromatogram_options, 
                comment,
                map_plot_color_scale, map_plot_quantization_level, plot_theme,
                synchronization_type):

    url_params = {}
    url_params["xic_mz"] = xic_mz
    url_params["xic_formula"] = xic_formula
    url_params["xic_peptide"] = xic_peptide
    url_params["xic_tolerance"] = xic_tolerance
    url_params["xic_ppm_tolerance"] = xic_ppm_tolerance
    url_params["xic_tolerance_unit"] = xic_tolerance_unit
    url_params["xic_rt_window"] = xic_rt_window
    url_params["xic_norm"] = xic_norm
    url_params["xic_file_grouping"] = xic_file_grouping
    url_params["xic_integration_type"] = xic_integration_type

    # MS2 in heatmap
    url_params["show_ms2_markers"] = show_ms2_markers
    url_params["ms2marker_color"] = ms2marker_color
    url_params["ms2marker_size"] = ms2marker_size

    url_params["ms2_identifier"] = ms2_identifier
    url_params["show_lcms_2nd_map"] = show_lcms_2nd_map
    url_params["map_plot_zoom"] = map_plot_zoom
    url_params["polarity_filtering"] = polarity_filtering
    url_params["polarity_filtering2"] = polarity_filtering2
    url_params["tic_option"] = tic_option

    # Overlay Options
    url_params["overlay_usi"] = overlay_usi
    url_params["overlay_mz"] = overlay_mz
    url_params["overlay_rt"] = overlay_rt
    url_params["overlay_color"] = overlay_color
    url_params["overlay_size"] = overlay_size
    url_params["overlay_hover"] = overlay_hover
    url_params["overlay_filter_column"] = overlay_filter_column
    url_params["overlay_filter_value"] = overlay_filter_value

    # Feature Finding Options
    url_params["feature_finding_type"] = feature_finding_type
    url_params["feature_finding_ppm"] = feature_finding_ppm
    url_params["feature_finding_noise"] = feature_finding_noise
    url_params["feature_finding_min_peak_rt"] = feature_finding_min_peak_rt
    url_params["feature_finding_max_peak_rt"] = feature_finding_max_peak_rt
    url_params["feature_finding_rt_tolerance"] = feature_finding_rt_tolerance

    # MassQL
    url_params["massql_statement"] = massql_statement

    # Sychronization Options
    url_params["sychronization_session_id"] = sychronization_session_id

    # mzML Chromatogram Options
    url_params["chromatogram_options"] = json.dumps(chromatogram_options)

    # Comment
    url_params["comment"] = comment

    # Advanced Viz options
    url_params["map_plot_color_scale"] = map_plot_color_scale
    url_params["map_plot_quantization_level"] = map_plot_quantization_level

    url_params["plot_theme"] = plot_theme

    hash_params = {}
    hash_params["usi"] = usi
    hash_params["usi2"] = usi2

    full_url = request.host_url + "/?{}#{}".format(urllib.parse.urlencode(url_params), urllib.parse.quote(json.dumps(hash_params)))

    full_json_settings = url_params
    full_json_settings["usi"] = usi
    full_json_settings["usi2"] = usi2

    # Determining Savings
    triggered_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if "sychronization_save_session_button" in triggered_id or synchronization_type == "LEADER" or \
        ("sychronization_set_type_button" in triggered_id and synchronization_type == "COLLAB"):
        if len(sychronization_session_id) > 0:
            # Lets save this to redis
            _sychronize_save_state(sychronization_session_id, full_json_settings, redis_client, synchronization_token=synchronization_leader_token)

    # For Live Synchronization
    if synchronization_type == "COLLAB":
        all_triggered_list = [p['prop_id'] for p in dash.callback_context.triggered]
        if len(sychronization_session_id) > 0:
            _synchronize_collab_action(sychronization_session_id, all_triggered_list, full_json_settings, synchronization_token=synchronization_leader_token)

    qr_html_img = dash.no_update
    try:
        qr_html_img = _generate_qrcode_img(full_url) 
    except:
        pass

    # Saving the data to logs area
    try:
        log_filename = "./logs/params/{}.json".format(str(uuid.uuid4()))
        import copy
        to_save_settings = copy.deepcopy(full_json_settings)
        to_save_settings["ip"] = request.remote_addr

        now = datetime.now()
        date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
        to_save_settings["timestamp"] = date_time

        with open(log_filename, "w") as o:
            o.write(json.dumps(to_save_settings))
    except:
        pass

    # Removing Sync token for json area
    full_json_settings.pop("sychronization_session_id", None)

    return [full_url, json.dumps(full_json_settings, indent=4), qr_html_img]


app.clientside_callback(
    """
    function(n_clicks, text_to_copy) {
        original_text = "Copy URL Link to this Visualization"
        if (n_clicks > 0) {
            const el = document.createElement('textarea');
            el.value = text_to_copy;
            document.body.appendChild(el);
            el.select();
            document.execCommand('copy');
            document.body.removeChild(el);
            setTimeout(function(){ 
                    document.getElementById("copy_link_button").textContent = original_text
                }, 1000);
            document.getElementById("copy_link_button").textContent = "Copied!"
            return 'Copied!';
        } else {
            document.getElementById("copy_link_button").textContent = original_text
            return original_text;
        }
    }
    """,
    Output('copy_link_button', 'children'),
    [
        Input('copy_link_button', 'n_clicks')
    ],
    [
        State('query_link', 'href'),
    ]
)


# This helps write the json string that we can use to load parameters in the whole page
@app.callback([
                  Output('setting_json_area', 'value'),
                  Output('setting_json_area_history', 'value'),
                  Output('advanced_import_history_link', 'href'),
                  Output('advanced_import_download_button', 'href'),
              ],
              [
                  Input("page_parameters", "children"),
                  Input('upload-settings-json', 'contents'),
              ],
              [
                  State('setting_json_area_history', 'value'),
                  State('upload-settings-json', 'filename'),
                  State('upload-settings-json', 'last_modified'),
              ])
def create_param_json(page_parameters, filecontent, existing_setting_json_area_history, filename, filedate):
    triggered_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    new_params = page_parameters
    history_text = dash.no_update
    history_link = dash.no_update

    # Checking if we're doing stuff
    if "upload-settings-json" in triggered_id:
        if len(filecontent) < 100000:
            data = filecontent.encode("utf8").split(b";base64,")[1]
            decoded_data = base64.decodebytes(data).decode("utf8", "ignore")
            file_setting_dict = json.loads(decoded_data)
            
            new_params = json.dumps(file_setting_dict, indent=4)

    if "page_parameters" in triggered_id:
        # Updating the history
        history_list = []
        try:
            history_list = json.loads(existing_setting_json_area_history)
        except:
            pass
        history_list.append(json.loads(page_parameters))
        history_text = json.dumps(history_list, indent=4)

        hash_params = {}
        hash_params["replay_list"] = history_list
        history_link = "/#{}".format(urllib.parse.quote(json.dumps(hash_params)))

    return [
        new_params, 
        history_text,
        history_link,
        "/settingsdownload?settings_json={}".format(urllib.parse.quote(new_params))
    ]


@app.callback([
                Output("auto_import_parameters", "children"),
                Output("replay_json_area", "value"),
                Output("replay_json_area_previous", "value"),
              ],
              [
                  Input('url', 'hash'),
                  Input("replay_forward_button", "n_clicks"),
                  Input("replay_backward_button", "n_clicks"),
              ],
              [
                  State("replay_json_area", "value"),
                  State("replay_json_area_previous", "value")
              ])
def advance_replay(url_hash, replay_forward_button, replay_backward_button, replay_json_area, replay_json_area_previous):
    import_parameters_json = dash.no_update
    next_json_state = []
    previous_json_state = []

    try:
        next_json_state = json.loads(replay_json_area)
    except:
        pass
        
    try:
        previous_json_state = json.loads(replay_json_area_previous)
    except:
        pass
    
    triggered_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    if "url" in triggered_id:
        try:
            hash_dict = json.loads(urllib.parse.unquote(url_hash[1:]))
            next_json_state = hash_dict["replay_list"]
        except:
            pass

    if "replay_forward_button" in triggered_id:
        try:
            if len(next_json_state) > 0:
                import_parameters_json = json.dumps(next_json_state[0], indent=4)
                previous_json_state.append(next_json_state[0])
                next_json_state = next_json_state[1:]
        except:
            pass


    if "replay_backward_button" in triggered_id:
        try:
            if len(previous_json_state) > 0:
                import_parameters_json = json.dumps(previous_json_state[-1], indent=4)
                next_json_state.insert(0, previous_json_state[-1])
                previous_json_state = previous_json_state[:-1]
        except:
            pass

    return [
        import_parameters_json, 
        json.dumps(next_json_state, indent=4),
        json.dumps(previous_json_state, indent=4)
    ]


@app.callback([
                Output("advanced_import_replay_link", "href")
              ],
              [
                  Input('replay_json_area', 'value'),
              ])
def create_replay_link(replay_json_area,):
    
    hash_params = {}
    hash_params["replay_list"] = json.loads(replay_json_area)
    replay_link = "/#{}".format(urllib.parse.quote(json.dumps(hash_params)))

    return [replay_link]


@app.callback([
                Output("replay_summary", "children")
              ],
              [
                  Input('replay_json_area', 'value'),
                  Input('replay_json_area_previous', 'value')
              ])
def create_replay_link(replay_json_area, replay_json_area_previous):
    replay_list = []
    replay_previous_list = []

    try:
        replay_list = json.loads(replay_json_area)
    except:
        pass
    
    try:
        replay_previous_list = json.loads(replay_json_area_previous)
    except:
        pass

    return ["{} total replay steps and {} previous steps".format(len(replay_list), len(replay_previous_list))]




@app.callback(Output('sychronization_teaching_links', 'children'),
              [
                Input("sychronization_session_id", "value"),
                Input("synchronization_leader_token", "value")
              ])
def create_sychronization_link(sychronization_session_id, synchronization_leader_token):
    url_params = {}

    url_params["sychronization_session_id"] = sychronization_session_id
    url_params["synchronization_type"] = "FOLLOWER"

    follower_url = "/?{}".format(urllib.parse.urlencode(url_params))

    url_params["synchronization_leader_token"] = synchronization_leader_token
    url_params["synchronization_type"] = "LEADER"

    leader_url = "/?{}".format(urllib.parse.urlencode(url_params))

    url_params["synchronization_leader_token"] = synchronization_leader_token
    url_params["synchronization_type"] = "COLLAB"

    collab_url = "/?{}".format(urllib.parse.urlencode(url_params))

    follower_full_url = request.url.replace('/_dash-update-component', follower_url)
    follower_img = _generate_qrcode_img(follower_full_url)

    return [
        dbc.Row([
            dbc.Col(
                dcc.Link(dbc.Button("Follower URL", block=True, color="primary", className="mr-1"), href=follower_url, target="_blank")
            ),
            dbc.Col(
                dcc.Link(dbc.Button("Leader URL", block=True, color="primary", className="mr-1"), href=leader_url, target="_blank")
            ),
            dbc.Col(
                dcc.Link(dbc.Button("Collab URL", block=True, color="primary", className="mr-1"), href=collab_url, target="_blank")
            ),
        ]),
        dbc.Row([
            dbc.Col(
                follower_img
            ),
            dbc.Col()
            
        ])
    ]





@app.callback(Output('network-link-button', 'children'),
              [
                  Input('usi', 'value'), 
                  Input('usi2', 'value'), 
              ])
def create_networking_link(usi, usi2):
    full_url = "https://gnps.ucsd.edu/ProteoSAFe/index.jsp?params="

    g1_list = []
    g2_list = []

    usi_list = usi.split("\n")
    for usi_value in usi_list:
        try:
            ccms_path = download._usi_to_ccms_path(usi_value)
            if ccms_path is not None:
                g1_list.append(ccms_path)
        except:
            pass
    
    usi_list2 = usi2.split("\n")
    for usi_value in usi_list2:
        try:
            ccms_path = download._usi_to_ccms_path(usi_value)
            if ccms_path is not None:
                g2_list.append(ccms_path)
        except:
            pass

    if len(g1_list) > 0 or len(g2_list) > 0:
        parameters = {}
        parameters["workflow"] = "METABOLOMICS-SNETS-V2"
        parameters["spec_on_server"] = ";".join(g1_list)
        parameters["spec_on_server_group2"] = ";".join(g2_list)

        gnps_url = "https://gnps.ucsd.edu/ProteoSAFe/index.jsp?params="
        gnps_url = gnps_url + urllib.parse.quote(json.dumps(parameters))

        url_provenance = dbc.Button("Molecular Network {} Files at GNPS".format(len(g1_list) + len(g2_list)), block=True, color="secondary", className="mr-1")
        provenance_link_object = dcc.Link(url_provenance, href=gnps_url, target="_blank")

        return [provenance_link_object, html.Br()]

    return dash.no_update


# Creating File Summary
@app.callback([Output('summary-table', 'children')],
              [Input('usi', 'value'), Input('usi2', 'value')])
@cache.memoize()
def get_file_summary(usi, usi2):
    usi1_list = usi.split("\n")
    usi2_list = usi2.split("\n")

    usi1_list = [usi for usi in usi1_list if len(usi) > 8] # Filtering out empty USIs
    usi2_list = [usi for usi in usi2_list if len(usi) > 8] # Filtering out empty USIs

    
    usi_list = usi1_list + usi2_list
    usi_list = usi_list[:MAX_LCMS_FILES]

    all_file_stats = [_calculate_file_stats(usi, _resolve_usi(usi)[1]) for usi in usi_list]
    stats_df = pd.DataFrame(all_file_stats)     
    stats_df["Download"] = "DOWNLOAD"
    stats_df["Image"] = "Image"

    table = dbc.Table.from_dataframe(stats_df, striped=True, bordered=True, hover=True, size="sm")

    # Adding Download Buttons instead of DOWNLOAD
    for row in table.children:
        for tbody in row.children:
            usi = tbody.children[0].children
            # Skipping header
            if usi == "USI": 
                continue
            download_remote_link = download._resolve_usi_remotelink(usi)

            # Here we're going to convert massive downloads to a proxy
            if "ftp://massive.ucsd.edu" in download_remote_link:
                download_remote_link = "https://gnps-external.ucsd.edu/massiveftpproxy?ftppath={}".format(download_remote_link)

            tbody.children[-2].children = html.A(dbc.Button("Download", color="primary", className="mr-1", size="sm"), href=download_remote_link, target="_blank")

            image_link = "/mspreview?usi={}".format(usi)
            tbody.children[-1].children = html.A(dbc.Button("Image", color="primary", className="mr-1", size="sm"), href=image_link, target="_blank")

            # Replacing USI with just filename
            tbody.children[0].children = download._get_usi_display_filename(usi)

    return [table]


# Creating File Summary
@app.callback([Output('dataset_files_nav', 'children')],
              [Input('usi', 'value'), Input('usi2', 'value')])
@cache.memoize()
def get_dataset_link(usi, usi2):
    usi1_list = usi.split("\n")
    usi2_list = usi2.split("\n")

    usi1_list = [usi for usi in usi1_list if len(usi) > 8] # Filtering out empty USIs
    usi2_list = [usi for usi in usi2_list if len(usi) > 8] # Filtering out empty USIs

    usi_list = usi1_list + usi2_list

    all_accessions = []
    for usi in usi_list:
        accession = usi.split(":")[1]
        if "MSV" in accession:
            all_accessions.append(accession)
        if "MTBLS" in accession:
            all_accessions.append(accession)

    if len(all_accessions) > 0:
        return [dbc.NavLink("Select Other Dataset Files", href="https://gnps-explorer.ucsd.edu/{}".format(all_accessions[0]))]
    return [dash.no_update]

@app.callback([
                  Output('overlay_mz', 'options'), 
                  Output('overlay_rt', 'options'), 
                  Output('overlay_hover', 'options'),
                  Output('overlay_color', 'options'), 
                  Output('overlay_size', 'options')
              ],
              [
                  Input('overlay_usi', 'value'),
                  Input('overlay_tabular_data', 'value'),
              ])
@cache.memoize()
def get_overlay_options(overlay_usi, overlay_tabular_data):
    """This function finds all the overlay options

    Args:
        overlay_usi ([type]): [description]

    Returns:
        [type]: [description]
    """
    
    if overlay_usi is None:
        return [dash.no_update] * 5

    overlay_df = _resolve_overlay(overlay_usi, "", "", "", "", "", "", "", overlay_tabular_data=overlay_tabular_data)

    columns = list(overlay_df.columns)

    options = []

    for column in columns:
        options.append({"label": column, "value": column})

    return [options, options, options, options, options]




# Sychronization Section for callbacks
@app.callback([
                Output('synchronization_leader_token', 'value'),
                Output('sychronization_output1', 'children')
              ],
              [
                  Input('url', 'search'),
                  Input('synchronization_leader_newtoken_button', 'n_clicks')
              ],
              [
                  State('sychronization_session_id', 'value'),
                  State('synchronization_leader_token', 'value')
              ])
def get_new_token(search, synchronization_leader_newtoken_button, sychronization_session_id, synchronization_leader_token):
    """Here we will try to get a new token for the user

    Args:
        synchronization_leader_newtoken_button ([type]): [description]
        sychronization_session_id ([type]): [description]
        synchronization_leader_token ([type]): [description]

    Returns:
        [type]: [description]
    """
    triggered_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    if "synchronization_leader_newtoken_button" in triggered_id:
        if len(sychronization_session_id) < 1:
            return [dash.no_update, "Please enter a session id"]

        if len(synchronization_leader_token) > 0:
            return [dash.no_update, "Please delete your token to get a new one"]
        else:
            try:
                session_dict = _sychronize_load_state(sychronization_session_id, redis_client)
            except:
                session_dict = {}

            if session_dict.get("synchronization_token", None) is None:
                # There exists no token, let's create one and save it
                new_token = str(uuid.uuid4()).replace("-", "")
                session_dict["synchronization_token"] = new_token
                _sychronize_save_state(sychronization_session_id, session_dict, redis_client)

                return [new_token, "New Session Token Updated"]
            else:
                # There exists a token
                return [dash.no_update, "Token already exists for this session, please enter it to be the leader"]

        return [dash.no_update, "Bad News Bears"]
    else:
        synchronization_leader_token = _get_param_from_url(search, "", "synchronization_leader_token", dash.no_update)
        return [synchronization_leader_token, "Loaded Token from URL"]


@app.callback([
                Output('sychronization_output2', 'children')
              ],
              [
                  Input('synchronization_leader_checktoken_button', 'n_clicks')
              ],
              [
                  State('sychronization_session_id', 'value'),
                  State('synchronization_leader_token', 'value')
              ])
def check_token(synchronization_leader_newtoken_button, sychronization_session_id, synchronization_leader_token):
    if len(sychronization_session_id) < 1:
        return ["Please enter a session id"]

    if len(sychronization_session_id) == 0:
        return ["Please enter a token"]
    else:
        # Lets check the session against the token
        try:
            session_dict = _sychronize_load_state(sychronization_session_id, redis_client)
            
            if session_dict.get("synchronization_token", None) is None:
                return ["Session has no token to verify against, you may create one by deleting your entry"]
            else:
                db_token = session_dict.get("synchronization_token", None)
                if db_token == synchronization_leader_token:
                    return ["Token Verified, ready to rock and roll"]
                else:
                    return ["Token Verification Failed"]
        except:
            return ["Error Verifying Session and Token"]



@app.callback([
                Output('sychronization_interval', 'interval'),
                Output('synchronization_status', 'children'),
              ],
              [
                  Input('synchronization_begin_button', 'n_clicks'),
                  Input('synchronization_stop_button', 'n_clicks'),
                  Input('sychronization_set_type_button', 'n_clicks'),
                  Input('synchronization_type_dependency', 'children')
              ],
              [
                  State('synchronization_type', 'value'),
              ])
def set_update_interval(synchronization_begin_button, synchronization_stop_button, sychronization_set_type_button, synchronization_type_dependency, synchronization_type):
    new_interval = 10000000 * 1000
    triggered_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    status_text = ""
    # If we click stop, lets not do anything anymore
    if "synchronization_stop_button" in triggered_id:
        status_text = "Sync Stopped"
        return [new_interval, status_text]

    # We know we're the follower, so lets act like it
    if synchronization_type == "FOLLOWER" or synchronization_type == "COLLAB":
        new_interval = 5 * 1000
        status_text = "Sync Started"

    return [new_interval, status_text]

###########################################
# Hiding Panels
###########################################

# Show Hide Panels
@app.callback(
    Output("second-data-exploration-dashboard-collapse", "is_open"),
    [Input("show_lcms_2nd_map", "value")],
    [State("second-data-exploration-dashboard-collapse", "is_open")],
)
def toggle_collapse2(show_lcms_2nd_map, is_open):
    return show_lcms_2nd_map

# Show Hide Panels
@app.callback(
    Output("first-data-exploration-dashboard-collapse", "is_open"),
    [Input("show_lcms_1st_map", "value")],
    [State("first-data-exploration-dashboard-collapse", "is_open")],
)
def toggle_collapse1(show_lcms_1st_map, is_open):
    return show_lcms_1st_map

@app.callback(
    [Output("usi1-filtering-collapse", "is_open"), Output("usi2-filtering-collapse", "is_open")],
    [Input("show_filters", "value")],
)
def toggle_collapse_filters(show_filters):
    return [show_filters, show_filters]

@app.callback(
    [Output("massql-collapse", "is_open")],
    [Input("feature_finding_type", "value")],
)
def toggle_collapse_massql(feature_finding_type):
    if feature_finding_type == "MassQL":
        return [True]
    return [False]

@app.callback(
    [Output("feature-finding-collapse", "is_open")],
    [Input("feature_finding_type", "value")],
)
def toggle_collapse_feature_finding(feature_finding_type):
    if feature_finding_type == "MZmine2":
        return [True]
    return [False]

@app.callback(
    [Output("featurefinding-results-collapse", "is_open")],
    [Input("feature_finding_type", "value")],
)
def toggle_collapse_feature_finding(feature_finding_type):
    if feature_finding_type == "Off":
        return [False]
    return [True]

@app.callback(
    [Output("overlay-collapse", "is_open")],
    [Input("show_overlay", "value")],
)
def toggle_collapse_overlay_options(show):
    return [show]

# Helping to toggle the modals
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open



app.callback(
    Output("spectrum_details_modal", "is_open"),
    [Input("spectrum_details_modal_button", "n_clicks"), Input("spectrum_details_modal_close", "n_clicks")],
    [State("spectrum_details_modal", "is_open")],
)(toggle_modal)

app.callback(
    Output("advanced_usi_modal", "is_open"),
    [Input("advanced_usi_modal_button", "n_clicks"), Input("advanced_usi_modal_close", "n_clicks")],
    [State("advanced_usi_modal", "is_open")],
)(toggle_modal)


app.callback(
    Output("advanced_librarysearch_modal", "is_open"),
    [Input("advanced_librarysearch_modal_button", "n_clicks"), Input("advanced_librarysearch_modal_close", "n_clicks")],
    [State("advanced_librarysearch_modal", "is_open")],
)(toggle_modal)


app.callback(
    Output("advanced_librarysearchmassivekb_modal", "is_open"),
    [Input("advanced_librarysearchmassivekb_modal_button", "n_clicks"), Input("advanced_librarysearchmassivekb_modal_close", "n_clicks")],
    [State("advanced_librarysearchmassivekb_modal", "is_open")],
)(toggle_modal)



app.callback(
    Output("advanced_visualization_modal", "is_open"),
    [Input("advanced_visualization_modal_button", "n_clicks"), Input("advanced_visualization_modal_close", "n_clicks")],
    [State("advanced_visualization_modal", "is_open")],
)(toggle_modal)

app.callback(
    Output("sychronization_options_modal", "is_open"),
    [Input("sychronization_options_modal_button", "n_clicks"), Input("sychronization_options_modal_close", "n_clicks")],
    [State("sychronization_options_modal", "is_open")],
)(toggle_modal)

app.callback(
    Output("advanced_import_modal", "is_open"),
    [Input("advanced_import_modal_button", "n_clicks"), Input("advanced_import_modal_close", "n_clicks")],
    [State("advanced_import_modal", "is_open")],
)(toggle_modal)

app.callback(
    Output("advanced_replay_modal", "is_open"),
    [Input("advanced_replay_modal_button", "n_clicks"), Input("advanced_replay_modal_close", "n_clicks")],
    [State("advanced_replay_modal", "is_open")],
)(toggle_modal)

app.callback(
    Output("advanced_xic_modal", "is_open"),
    [Input("advanced_xic_modal_button", "n_clicks"), Input("advanced_xic_modal_close", "n_clicks")],
    [State("advanced_xic_modal", "is_open")],
)(toggle_modal)

app.callback(
    Output("advanced_upload_modal", "is_open"),
    [Input("advanced_upload_modal_button", "n_clicks"), Input("advanced_upload_modal_close", "n_clicks")],
    [State("advanced_upload_modal", "is_open")],
)(toggle_modal)


# Helping to toggle the panels
def toggle_panel(n1, is_open):
    if n1:
        return not is_open
    return is_open


app.callback(
    Output("data_selection_collapse", "is_open"),
    [Input("data_selection_show_hide_button", "n_clicks")],
    [State("data_selection_collapse", "is_open")],
)(toggle_panel)


#######################
# Flask URLS
#######################

from flask import request
import glob
import shutil

@server.route("/mspreview")
@cache.memoize()
def preview():
    usi = request.args.get("usi")

    remote_link, local_filename = _resolve_usi(usi)
    temp_result_folder = os.path.join(TEMPFOLDER, "image_previews", str(uuid.uuid4()))
    target_preview_image = os.path.join(TEMPFOLDER, "image_previews", werkzeug.utils.secure_filename(os.path.basename(local_filename)) + ".png")

    if os.path.exists(target_preview_image):
        return send_from_directory(os.path.join(TEMPFOLDER, "image_previews"), os.path.basename(target_preview_image))

    cmd = 'export LC_ALL=C && ./bin/msaccess {} -o {} -x "image" '.format(local_filename, temp_result_folder)
    os.system(cmd)

    result_filename = glob.glob(os.path.join(temp_result_folder, "*.png"))[0]

    # Copying image
    shutil.copyfile(result_filename, target_preview_image)

    # Remove temp folder
    shutil.rmtree(temp_result_folder)

    # Lets create a preview with msaccess
    return send_from_directory(os.path.join(TEMPFOLDER, "image_previews"), os.path.basename(target_preview_image))

@server.route("/settingsdownload")
def settingsdownload():
    settings_json = request.args.get("settings_json")

    proxy = io.StringIO()

    proxy.write(settings_json)
    
    # Creating the byteIO object from the StringIO Object
    mem = io.BytesIO()
    mem.write(proxy.getvalue().encode())
    # seeking was necessary. Python 3.5.2, Flask 0.12.2
    mem.seek(0)
    proxy.close()

    import hashlib
    hash_value = int(hashlib.sha256(settings_json.encode('utf-8')).hexdigest(), 16) % 10**8
    output_filename = "settings_{}.json".format(hash_value)

    return send_file(
        mem,
        as_attachment=True,
        attachment_filename=output_filename,
        mimetype='text/json'
    )

@server.route("/downloadlink")
def downloadlink():
    usi = request.args.get("usi")
    download_remote_link = download._resolve_usi_remotelink(usi)
    
    return download_remote_link




if __name__ == "__main__":
    app.run_server(debug=True, port=5000, host="0.0.0.0")
