# -*- coding: utf-8 -*-

# Dash imports

import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output, State
import dash_daq as daq
from time import sleep

# Plotly Imports

import plotly.express as px
import plotly.graph_objects as go 

# Flask

from flask import Flask, send_from_directory
import werkzeug
from flask_caching import Cache

# Misc Library

import sys
import os
from zipfile import ZipFile
import urllib.parse
from scipy import integrate
import pandas as pd
import requests
import uuid
import pymzml
import numpy as np
import datashader as ds
from tqdm import tqdm
import json
from collections import defaultdict
import uuid
import base64
from molmass import Formula
from pyteomics import mass

# Project Imports

from utils import _calculate_file_stats
from utils import _get_scan_polarity
from utils import _resolve_map_plot_selection, _get_param_from_url, _spectrum_generator
from utils import MS_precisions
import utils

import download
import ms2
import lcms_map
import tasks
from formula_utils import get_adduct_mass
import xic

# Importing layout for HTML
from layout_misc import EXAMPLE_DASHBOARD

server = Flask(__name__)
app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = 'GNPS - LCMS Browser'

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
else:
    WORKER_UP = True
    cache = Cache(app.server, config={
        #'CACHE_TYPE': "null",
        'CACHE_TYPE': 'filesystem',
        'CACHE_DIR': 'temp/flask-cache',
        'CACHE_DEFAULT_TIMEOUT': 0,
        'CACHE_THRESHOLD': 1000000
    })

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
placeholder_map_plot = px.imshow(agg, origin='lower', labels={'color':'Log10(Abundance)'}, color_continuous_scale="Hot")
placeholder_xic_plot = px.line(df, x="rt", y="mz", title='XIC Placeholder')
placeholder_ms2_plot = px.line(df, x="rt", y="mz", title='Spectrum Placeholder')

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
                dbc.NavItem(dbc.NavLink("GNPS LCMS Dashboard - Version 0.23", href="/")),
            ],
        navbar=True)
    ],
    color="light",
    dark=False,
    sticky="top",
)

DATASELECTION_CARD = [
    dbc.CardHeader([
        html.H5("Data Selection"),
    ]),
    dbc.CardBody(dbc.Row(
        [   ## Left Panel
            dbc.Col([
                html.H5(children='File Selection'),
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
                dcc.Upload(
                    id='upload-data',
                    children=html.Div([
                        'Enter USI Above or Drag and Drop your own file',
                        html.A(' or Select Files')
                    ]),
                    style={
                        'width': '95%',
                        'height': '60px',
                        'lineHeight': '60px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                        'margin': '10px'
                    },
                    multiple=False
                ),
                # Linkouts
                dcc.Loading(
                    id="link-button",
                    children=[html.Div([html.Div(id="loading-output-9")])],
                    type="default",
                ),
                html.Br(),
                dcc.Loading(
                    id="network-link-button",
                    children=[html.Div([html.Div(id="loading-output-232")])],
                    type="default",
                ),
                html.H5(children='LCMS Viewer Options'),
                dbc.Row([
                    dbc.Col(
                        dbc.FormGroup(
                            [
                                dbc.Label("Show MS2 Markers", html_for="show_ms2_markers", width=4.8, style={"width":"160px", "margin-left": "25px"}),
                                dbc.Col(
                                    daq.ToggleSwitch(
                                        id='show_ms2_markers',
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
                                dbc.Label("Feature Finding (Beta)", width=4.8, style={"width":"150px"}),
                                dcc.Dropdown(
                                    id='feature_finding_type',
                                    options=[
                                        {'label': 'Off', 'value': 'Off'},
                                        {'label': 'Test', 'value': 'Test'},
                                        {'label': 'Trivial', 'value': 'Trivial'},
                                        # {'label': 'TidyMS', 'value': 'TidyMS'},
                                        {'label': 'MZmine2 (Metabolomics)', 'value': 'MZmine2'},
                                        {'label': 'Dinosaur (Proteomics)', 'value': 'Dinosaur'},
                                    ],
                                    searchable=False,
                                    clearable=False,
                                    value="Off",
                                    style={
                                        "width":"60%"
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
            ], className="col-sm"),
            ## Right Panel
            dbc.Col([
                html.H5(children='XIC Options'),
                dbc.Row([
                    dbc.Col(
                        dbc.InputGroup(
                            [
                                dbc.InputGroupAddon("XIC m/z", addon_type="prepend"),
                                dbc.Input(id='xic_mz', placeholder="Enter m/z to XIC"),
                            ],
                            className="mb-3",
                        ),
                    ),
                    dbc.Col(
                        dbc.InputGroup(
                            [
                                dbc.InputGroupAddon("XIC Formula", addon_type="prepend"),
                                dbc.Input(id='xic_formula', placeholder="Enter Molecular Formula to XIC"),
                            ],
                            className="mb-3",
                        ),
                    ),
                    dbc.Col(
                        dbc.InputGroup(
                            [
                                dbc.InputGroupAddon("XIC Peptide", addon_type="prepend"),
                                dbc.Input(id='xic_peptide', placeholder="Enter Peptide to XIC"),
                            ],
                            className="mb-3",
                        ),
                    ),
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
                                        "width":"60%"
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
                                dbc.Label("XIC Integration Type", width=4.8, style={"width":"150px"}),
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
                                        "width":"60%"
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
                                dbc.Label("XIC Normalization", html_for="xic_norm", width=4.8, style={"width":"150px"}),
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
                                dbc.Label("XIC File Grouping", width=4.8, style={"width":"150px"}),
                                dcc.Dropdown(
                                    id='xic_file_grouping',
                                    options=[
                                        {'label': 'By File', 'value': 'FILE'},
                                        {'label': 'By m/z', 'value': 'MZ'},
                                        {'label': 'By Group', 'value': 'GROUP'}
                                    ],
                                    searchable=False,
                                    clearable=False,
                                    value="FILE",
                                    style={
                                        "width":"60%"
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
                html.H5(children='Rendering Options'),
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
                                    value="simple_white",
                                    style={
                                        "width":"60%"
                                    }
                                )  
                            ],
                            row=True,
                            className="mb-3",
                        )),
                ]),
                dbc.Button("Advanced Visualization Options", block=True, id="advanced_visualization_modal_button"),
            ], className="col-sm")
        ])
    )
]

DATASLICE_CARD = [
    dbc.CardHeader(html.H5("Details Panel")),
    dbc.CardBody(
        [   
            html.Br(),
            dcc.Loading(
                id="loading-20",
                children=[dcc.Graph(
                    id='xic-plot',
                    figure=placeholder_xic_plot,
                    config={
                        'doubleClick': 'reset'
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
            dbc.Button("Spectrum Details", block=True, id="spectrum_details_modal_button"),
            html.Br(),
            dcc.Loading(
                id="ms2-plot-buttons",
                children=[html.Div([html.Div(id="loading-output-1034")])],
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
                            dbc.Button("Update Feature Finding Interactively", color="primary", className="mr-1", id="run-feature-finding-button", block=True),
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

OVERLAY_PANEL = [
    dbc.CardHeader(html.H5("LCMS Overlay Options")),
    dbc.CardBody(
        [
            dbc.Row([
                dbc.Col(
                    dbc.InputGroup(
                        [
                            dbc.InputGroupAddon("Overlay USI", addon_type="prepend"),
                            dbc.Input(id='overlay-usi', placeholder="Enter Overlay File USI"),
                        ],
                        className="mb-3",
                    ),
                )
            ]),
            dbc.Row([
                dbc.Col(
                    dbc.InputGroup(
                        [
                            dbc.InputGroupAddon("Overlay m/z", addon_type="prepend"),
                            dbc.Input(id='overlay-mz', placeholder="Enter Overlay mz column", value="row m/z"),
                        ],
                        className="mb-3",
                    ),
                ),
                dbc.Col(
                    dbc.InputGroup(
                        [
                            dbc.InputGroupAddon("Overlay rt", addon_type="prepend"),
                            dbc.Input(id='overlay-rt', placeholder="Enter Overlay rt column", value="row retention time"),
                        ],
                        className="mb-3",
                    ),
                )
            ]),
            dbc.Row([
                dbc.Col(
                    dbc.InputGroup(
                        [
                            dbc.InputGroupAddon("Overlay color", addon_type="prepend", style={"margin-right":"20px"}),
                            #dbc.Input(id='overlay-color', placeholder="Enter Overlay color column", value=""),
                            dcc.Dropdown(
                                id='overlay-color',
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
                    dbc.InputGroup(
                        [
                            dbc.InputGroupAddon("Overlay size", addon_type="prepend", style={"margin-right":"20px"}),
                            #dbc.Input(id='overlay-size', placeholder="Enter Overlay size column", value=""),
                            dcc.Dropdown(
                                id='overlay-size',
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
                )
            ]),
            dbc.Row([
                dbc.Col(
                    dbc.InputGroup(
                        [
                            dbc.InputGroupAddon("Overlay Label Column", addon_type="prepend", style={"margin-right":"20px"}),
                            dcc.Dropdown(
                                id='overlay-hover',
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
            ]),
            dbc.Row([
                dbc.Col(
                    dbc.InputGroup(
                        [
                            dbc.InputGroupAddon("Overlay Filter Column", addon_type="prepend"),
                            dbc.Input(id='overlay-filter-column', placeholder="Enter Overlay filter column", value=""),
                        ],
                        className="mb-3",
                    ),
                ),
                dbc.Col(
                    dbc.InputGroup(
                        [
                            dbc.InputGroupAddon("Overlay Filter Value", addon_type="prepend"),
                            dbc.Input(id='overlay-filter-value', placeholder="Enter Overlay size column", value=""),
                        ],
                        className="mb-3",
                    ),
                )
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
                                id='polarity-filtering',
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
                                id='polarity-filtering2',
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
        ]
    )
]

INTEGRATION_CARD = [
    dbc.CardHeader(html.H5("XIC Integration")),
    dbc.CardBody(
        [
            dcc.Loading(
                id="integration-table",
                children=[html.Div([html.Div(id="loading-output-1001")])],
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
                "Wout Bittremieux PhD - UC San Diego",
                html.Br(),
                "Benjamin Pullman - UC San Diego",
                html.Br(),
                "Daniel Petras PhD - UC San Diego",
                html.Br(),
                "Vanessa Phelan PhD - CU Anschutz",
                html.Br(),
                "Tristan de Rond PhD - UC San Diego",
                html.Br(),
                "Alan Jarmusch PhD - UC San Diego",
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
    dbc.CardHeader(html.H5("Data Exploration")),
    dbc.CardBody(
        [
            html.Br(),
            html.Div(id='map-plot-zoom', style={'display': 'none'}),
            dcc.Graph(
                id='map-plot',
                figure=placeholder_map_plot,
                config={
                    'doubleClick': 'reset'
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

SPECTRUM_DETAILS_MODAL = [
    dbc.Modal(
        [
            dbc.ModalHeader("Spectrum Details as YAML"),
            dbc.ModalBody([
                dcc.Loading(
                    id="spectrum_details_area",
                    children=[html.Div([html.Div(id="loading-output-1035")])],
                    type="default",
                ),
            ]),
            dbc.ModalFooter(
                dbc.Button("Close", id="spectrum_details_modal_close", className="ml-auto")
            ),
        ],
        id="spectrum_details_modal",
        size="xl",
    ),
]


ADVANCED_VISUALIZATION_MODAL = [
    dbc.Modal(
        [
            dbc.ModalHeader("Advanced Visualization Modal"),
            dbc.ModalBody([
                dbc.Row([
                    dbc.Col(
                        dbc.FormGroup(
                            [
                                dbc.Label("LCMS Quantization Map Level", width=4.8, style={"width":"250px"}),
                                dcc.Dropdown(
                                    id='map_plot_quantization_level',
                                    options=[
                                        {'label': 'Low', 'value': 'Low'},
                                        {'label': 'Medium', 'value': 'Medium'},
                                        {'label': 'High', 'value': 'High'},
                                    ],
                                    searchable=False,
                                    clearable=False,
                                    value="Medium",
                                    style={
                                        "width":"60%"
                                    }
                                )  
                            ],
                            row=True,
                            className="mb-3",
                            style={"margin-left": "4px"}
                    )),
                ]),
                html.Hr(),
                dbc.Row([
                    dbc.Col(
                        dbc.InputGroup(
                            [
                                dbc.InputGroupAddon("RT Range", addon_type="prepend"),
                                dbc.Input(id='map_plot_rt_min', placeholder="Enter Min RT", value=""),
                                dbc.Input(id='map_plot_rt_max', placeholder="Enter Max RT", value=""),
                            ],
                            className="mb-3",
                            style={"margin-left": "4px"}
                    )),
                ]),
                dbc.Row([
                    dbc.Col(
                        dbc.InputGroup(
                            [
                                dbc.InputGroupAddon("m/z Range", addon_type="prepend"),
                                dbc.Input(id='map_plot_mz_min', placeholder="Enter Min m/z", value=""),
                                dbc.Input(id='map_plot_mz_max', placeholder="Enter Max m/z", value=""),
                            ],
                            className="mb-3",
                            style={"margin-left": "4px"}
                    )),
                ]),
            ]),
            dbc.ModalFooter(
                dbc.Button("Close", id="advanced_visualization_modal_close", className="ml-auto")
            ),
        ],
        id="advanced_visualization_modal",
        size="lg",
    ),
]

BODY = dbc.Container(
    [
        dcc.Location(id='url', refresh=False),
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
        dbc.Row(ADVANCED_VISUALIZATION_MODAL),
        
    ],
    fluid=True,
    className="",
)

app.layout = html.Div(children=[NAVBAR, BODY])



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
                sleep(3)
            result = result.get()
            return result
        else:
            # If we have the celery instance is not up, we'll do it local
            print("Downloading Local")
            return tasks._download_convert_file(usi, temp_folder=temp_folder)


# This helps to update the ms2/ms1 plot
@app.callback([Output("ms2_identifier", "value")],
              [Input('url', 'search'), Input('usi', 'value'), Input('map-plot', 'clickData'), Input('xic-plot', 'clickData'), Input('tic-plot', 'clickData')])
def click_plot(url_search, usi, mapclickData, xicclickData, ticclickData):

    triggered_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    print(triggered_id, ticclickData)

    clicked_target = None
    if "map-plot" in triggered_id:
        clicked_target = mapclickData["points"][0]
    elif "xic-plot" in triggered_id:
        clicked_target = xicclickData["points"][0]
    elif "tic-plot" in triggered_id:
        clicked_target = ticclickData["points"][0]

    # nothing was clicked, so read from URL
    if clicked_target is None:
        return [str(urllib.parse.parse_qs(url_search[1:])["ms2_identifier"][0])]
    
    # This is an MS2
    if clicked_target["curveNumber"] == 1:
        return ["MS2:" + str(clicked_target["customdata"])]
    
    # This is an MS3
    if clicked_target["curveNumber"] == 2:
        return ["MS3:" + str(clicked_target["customdata"])]
    
    # This is an MS1
    if clicked_target["curveNumber"] == 0:
        rt_target = clicked_target["x"]

        remote_link, local_filename = _resolve_usi(usi)

        # Understand parameters
        min_rt_delta = 1000
        closest_scan = 0
        run = pymzml.run.Reader(local_filename, MS_precisions=MS_precisions)
        for spec in tqdm(run):
            if spec.ms_level == 1:
                try:
                    delta = abs(spec.scan_time_in_minutes() - rt_target)
                    if delta < min_rt_delta:
                        closest_scan = spec.ID
                        min_rt_delta = delta
                except:
                    pass

        return ["MS1:" + str(closest_scan)]

    


# This helps to update the ms2/ms1 plot
@app.callback([Output('debug-output', 'children'), 
                Output('ms2-plot', 'figure'), 
                Output('ms2-plot', 'config'), 
                Output('ms2-plot-buttons', 'children'),
                Output('spectrum_details_area', 'children')],
              [Input('usi', 'value'), Input('ms2_identifier', 'value'), Input('image_export_format', 'value'), Input("plot_theme", "value")], [State('xic_mz', 'value')])
def draw_spectrum(usi, ms2_identifier, export_format, plot_theme, xic_mz):
    usi_splits = usi.split(":")
    dataset = usi_splits[1]
    filename = usi_splits[2]
    scan_number = str(ms2_identifier.split(":")[-1])
    updated_usi = "mzspec:{}:{}:scan:{}".format(dataset, filename, scan_number)

    # For Drawing and Exporting
    graph_config = {
        "toImageButtonOptions":{
            "format": export_format,
            'height': None, 
            'width': None,
        }
    }

    # Getting Spectrum Peaks
    remote_link, local_filename = _resolve_usi(usi)
    peaks, precursor_mz, spectrum_details_string = ms2._get_ms2_peaks(updated_usi, local_filename, scan_number)
    usi_url = "https://metabolomics-usi.ucsd.edu/spectrum/?usi={}".format(updated_usi)

    spectrum_type = "MS"
    button_elements = []

    if "MS2" in ms2_identifier or "MS3" in ms2_identifier:
        spectrum_type = "MS2"

        mzs = [peak[0] for peak in peaks]
        ints = [peak[1] for peak in peaks]
        neg_ints = [intensity * -1 for intensity in ints]

        interactive_fig = go.Figure(
            data=go.Scatter(x=mzs, y=ints, 
                mode='markers',
                marker=dict(size=1),
                error_y=dict(
                    symmetric=False,
                    arrayminus=[0]*len(neg_ints),
                    array=neg_ints,
                    width=0
                ),
                hoverinfo="x",
                text=mzs
            )
        )

        interactive_fig.update_layout(title='{}'.format(ms2_identifier))
        interactive_fig.update_layout(template=plot_theme)
        interactive_fig.update_xaxes(title_text='m/z')
        interactive_fig.update_yaxes(title_text='intensity')
        interactive_fig.update_xaxes(showline=True, linewidth=1, linecolor='black')
        interactive_fig.update_yaxes(showline=True, linewidth=1, linecolor='black')
        interactive_fig.update_yaxes(range=[0, max(ints)])

        masst_dict = {}
        masst_dict["workflow"] = "SEARCH_SINGLE_SPECTRUM"
        masst_dict["precursor_mz"] = str(precursor_mz)
        masst_dict["spectrum_string"] = "\n".join(["{}\t{}".format(peak[0], peak[1]) for peak in peaks])

        masst_url = "https://gnps.ucsd.edu/ProteoSAFe/index.jsp#{}".format(json.dumps(masst_dict))
        masst_button = html.A(dbc.Button("MASST Spectrum in GNPS", color="primary", className="mr-1", block=True), href=masst_url, target="_blank")

        USI_button = html.A(dbc.Button("View Vector Metabolomics USI", color="primary", className="mr-1", block=True), href=usi_url, target="_blank")

        button_elements = [USI_button, html.Br(), masst_button]


    if "MS1" in ms2_identifier:
        spectrum_type = "MS1"

        mzs = [peak[0] for peak in peaks]
        ints = [peak[1] for peak in peaks]
        neg_ints = [intensity * -1 for intensity in ints]

        interactive_fig = go.Figure(
            data=go.Scatter(x=mzs, y=ints, 
                mode='markers',
                marker=dict(size=1),
                error_y=dict(
                    symmetric=False,
                    arrayminus=[0]*len(neg_ints),
                    array=neg_ints,
                    width=0
                ),
                hoverinfo="x",
                text=mzs
            )
        )

        interactive_fig.update_layout(title='{}'.format(ms2_identifier))
        interactive_fig.update_layout(template=plot_theme)
        interactive_fig.update_xaxes(title_text='m/z')
        interactive_fig.update_yaxes(title_text='intensity')
        interactive_fig.update_xaxes(showline=True, linewidth=1, linecolor='black')
        interactive_fig.update_yaxes(showline=True, linewidth=1, linecolor='black')
        interactive_fig.update_yaxes(range=[0, max(ints)])

        USI_button = html.A(dbc.Button("View Vector Metabolomics USI", color="primary", className="mr-1", block=True), href=usi_url, target="_blank")

        button_elements = [USI_button]

    return [spectrum_type, interactive_fig, graph_config, button_elements, html.Pre(spectrum_details_string)]

@app.callback([ Output("xic_formula", "value"),
                Output("xic_peptide", "value"),
                Output("xic_tolerance", "value"), 
                Output("xic_ppm_tolerance", "value"), 
                Output("xic_tolerance_unit", "value"), 
                Output("xic_rt_window", "value"), 
                Output("xic_norm", "value"), 
                Output("xic_file_grouping", "value"),
                Output("xic_integration_type", "value"),
                Output("show_ms2_markers", "value"),
                Output("show_lcms_2nd_map", "value"),
                Output("tic_option", "value"),
                Output("polarity-filtering", "value"),
                Output("polarity-filtering2", "value"),
                Output("overlay-usi", "value"),
                Output("overlay-mz", "value"),
                Output("overlay-rt", "value"),
                Output("overlay-color", "value"),
                Output("overlay-size", "value"),
                Output("overlay-hover", "value"),
                Output('overlay-filter-column', 'value'),
                Output('overlay-filter-value', 'value'),
                Output("feature_finding_type", "value"),
                Output("feature_finding_ppm", "value"),
                Output("feature_finding_noise", "value"),
                Output("feature_finding_min_peak_rt", "value"),
                Output("feature_finding_max_peak_rt", "value"),
                Output("feature_finding_rt_tolerance", "value"),
                ],
              [Input('url', 'search')])
def determine_url_only_parameters(search):
    xic_formula = ""
    xic_peptide = ""
    xic_tolerance = "0.5"
    xic_ppm_tolerance = "10"
    xic_tolerance_unit = "Da"
    xic_norm = False
    xic_integration_type = "AUC"
    show_ms2_markers = True
    xic_file_grouping = "FILE"
    xic_rt_window = ""
    show_lcms_2nd_map = False
    tic_option = "TIC"
    polarity_filtering = "None"
    polarity_filtering2 = "None"
    overlay_usi = dash.no_update
    overlay_mz = dash.no_update
    overlay_rt = dash.no_update
    overlay_color = dash.no_update
    overlay_size = dash.no_update
    overlay_hover = dash.no_update
    overlay_filter_column = dash.no_update
    overlay_filter_value = dash.no_update

    # Feature Finding
    feature_finding_type = dash.no_update
    feature_finding_ppm = dash.no_update
    feature_finding_noise = dash.no_update
    feature_finding_min_peak_rt = dash.no_update
    feature_finding_max_peak_rt = dash.no_update
    feature_finding_rt_tolerance = dash.no_update

    try:
        xic_formula = str(urllib.parse.parse_qs(search[1:])["xic_formula"][0])
    except:
        pass

    try:
        xic_peptide = str(urllib.parse.parse_qs(search[1:])["xic_peptide"][0])
    except:
        pass
        
    try:
        xic_tolerance = str(urllib.parse.parse_qs(search[1:])["xic_tolerance"][0])
    except:
        pass

    try:
        xic_ppm_tolerance = str(urllib.parse.parse_qs(search[1:])["xic_ppm_tolerance"][0])
    except:
        pass

    try:
        xic_tolerance_unit = str(urllib.parse.parse_qs(search[1:])["xic_tolerance_unit"][0])
    except:
        pass

    try:
        xic_integration_type = str(urllib.parse.parse_qs(search[1:])["xic_integration_type"][0])
    except:
        pass

    try:
        xic_norm = str(urllib.parse.parse_qs(search[1:])["xic_norm"][0])
        if xic_norm == "True":
            xic_norm = True
        else:
            xic_norm = False
    except:
        pass

    try:
        show_ms2_markers = str(urllib.parse.parse_qs(search[1:])["show_ms2_markers"][0])
        if show_ms2_markers == "False":
            show_ms2_markers = False
        else:
            show_ms2_markers = True
    except:
        pass

    try:
        xic_file_grouping = str(urllib.parse.parse_qs(search[1:])["xic_file_grouping"][0])
    except:
        pass

    try:
        xic_rt_window = str(urllib.parse.parse_qs(search[1:])["xic_rt_window"][0])
    except:
        pass

    try:
        show_lcms_2nd_map = str(urllib.parse.parse_qs(search[1:])["show_lcms_2nd_map"][0])
        if show_lcms_2nd_map == "False":
            show_lcms_2nd_map = False
        else:
            show_lcms_2nd_map = True
    except:
        pass

    try:
        tic_option = str(urllib.parse.parse_qs(search[1:])["tic_option"][0])
    except:
        pass

    try:
        polarity_filtering = str(urllib.parse.parse_qs(search[1:])["polarity_filtering"][0])
    except:
        pass
    
    try:
        polarity_filtering2 = str(urllib.parse.parse_qs(search[1:])["polarity_filtering2"][0])
    except:
        pass

    try:
        overlay_usi = str(urllib.parse.parse_qs(search[1:])["overlay_usi"][0])
    except:
        pass

    try:
        overlay_mz = str(urllib.parse.parse_qs(search[1:])["overlay_mz"][0])
    except:
        pass

    try:
        overlay_rt = str(urllib.parse.parse_qs(search[1:])["overlay_rt"][0])
    except:
        pass

    try:
        overlay_color = str(urllib.parse.parse_qs(search[1:])["overlay_color"][0])
    except:
        pass

    try:
        overlay_size = str(urllib.parse.parse_qs(search[1:])["overlay_size"][0])
    except:
        pass

    try:
        overlay_hover = str(urllib.parse.parse_qs(search[1:])["overlay_hover"][0])
    except:
        pass

    try:
        overlay_filter_column = str(urllib.parse.parse_qs(search[1:])["overlay_filter_column"][0])
    except:
        pass

    try:
        overlay_filter_value = str(urllib.parse.parse_qs(search[1:])["overlay_filter_value"][0])
    except:
        pass

    try:
        feature_finding_type = str(urllib.parse.parse_qs(search[1:])["feature_finding_type"][0])
    except:
        pass

    try:
        feature_finding_ppm = str(urllib.parse.parse_qs(search[1:])["feature_finding_ppm"][0])
    except:
        pass

    try:
        feature_finding_noise = str(urllib.parse.parse_qs(search[1:])["feature_finding_noise"][0])
    except:
        pass

    try:
        feature_finding_min_peak_rt = str(urllib.parse.parse_qs(search[1:])["feature_finding_min_peak_rt"][0])
    except:
        pass

    try:
        feature_finding_max_peak_rt = str(urllib.parse.parse_qs(search[1:])["feature_finding_max_peak_rt"][0])
    except:
        pass
    
    try:
        feature_finding_rt_tolerance = str(urllib.parse.parse_qs(search[1:])["feature_finding_rt_tolerance"][0])
    except:
        pass
    
    return [xic_formula, 
            xic_peptide, 
            xic_tolerance, 
            xic_ppm_tolerance, 
            xic_tolerance_unit, 
            xic_rt_window, xic_norm, 
            xic_file_grouping, xic_integration_type, 
            show_ms2_markers, 
            show_lcms_2nd_map, 
            tic_option, polarity_filtering, 
            polarity_filtering2, 
            overlay_usi, overlay_mz, overlay_rt, overlay_color, overlay_size, overlay_hover, overlay_filter_column, overlay_filter_value,
            feature_finding_type, feature_finding_ppm, feature_finding_noise, feature_finding_min_peak_rt, feature_finding_max_peak_rt, feature_finding_rt_tolerance]


# Handling file upload
@app.callback([Output('usi', 'value'), Output('usi2', 'value'), Output('debug-output-2', 'children')],
              [Input('url', 'search'), Input('url', 'hash'), Input('upload-data', 'contents')],
              [State('upload-data', 'filename'),
               State('upload-data', 'last_modified')])
def update_usi(search, url_hash, filecontent, filename, filedate):
    usi = "mzspec:MSV000084494:GNPS00002_A3_p"
    usi2 = ""

    if filecontent is not None:
        if len(filecontent) > 100000000:
            raise Exception

        extension = os.path.splitext(filename)[1]
        if extension == ".mzML":
            temp_filename = os.path.join("temp", "{}.mzML".format(str(uuid.uuid4())))
            data = filecontent.encode("utf8").split(b";base64,")[1]

            with open(temp_filename, "wb") as temp_file:
                temp_file.write(base64.decodebytes(data))

            usi = "mzspec:LOCAL:{}".format(os.path.basename(temp_filename))

            return [usi, usi2, "FILE Uploaded {}".format(filename)]

        if extension == ".mzXML":
            mangled_name = str(uuid.uuid4())
            temp_filename = os.path.join("temp", "{}.mzXML".format(mangled_name))
            data = filecontent.encode("utf8").split(b";base64,")[1]

            with open(temp_filename, "wb") as temp_file:
                temp_file.write(base64.decodebytes(data))

            usi = "mzspec:LOCAL:{}".format(os.path.basename(temp_filename))

            return [usi, usi2, "FILE Uploaded {}".format(filename)]

        if extension.lower() == ".cdf":
            mangled_name = str(uuid.uuid4())
            temp_filename = os.path.join("temp", "{}.cdf".format(mangled_name))
            data = filecontent.encode("utf8").split(b";base64,")[1]

            with open(temp_filename, "wb") as temp_file:
                temp_file.write(base64.decodebytes(data))

            usi = "mzspec:LOCAL:{}".format(os.path.basename(temp_filename))

            return [usi, usi2, "FILE Uploaded {}".format(filename)]

    # Resolving USI
    usi = _get_param_from_url(search, url_hash, "usi", usi)
    usi2 = _get_param_from_url(search, url_hash, "usi2", usi2)

    return [usi, usi2, "Using URL USI"]
    

# Calculating which xic value to use
@app.callback(Output('xic_mz', 'value'),
              [Input('url', 'search'), Input('map-plot', 'clickData')], [State('xic_mz', 'value')])
def determine_xic_target(search, clickData, existing_xic):
    try:
        if existing_xic is None:
            existing_xic = ""
        else:
            existing_xic = str(existing_xic)
    except:
        existing_xic = ""

    # Clicked points for MS1
    try:
        clicked_target = clickData["points"][0]

        # This is MS1
        if clicked_target["curveNumber"] == 0:
            mz_target = clicked_target["y"]

            if len(existing_xic) > 0:
                return existing_xic + ";" + str(mz_target)

            return str(mz_target)
        # This is MS2
        elif clicked_target["curveNumber"] == 1:
            mz_target = clicked_target["y"]

            if len(existing_xic) > 0:
                return existing_xic + ";" + str(mz_target)

            return str(mz_target)
    except:
        pass

    # Reading from the URL    
    try:
        return str(urllib.parse.parse_qs(search[1:])["xicmz"][0])
    except:
        pass
    
    return ""


@cache.memoize()
def _create_map_fig(filename, map_selection=None, show_ms2_markers=True, polarity_filter="None", highlight_box=None, map_plot_quantization_level="Medium"):
    min_rt, max_rt, min_mz, max_mz = utils._determine_rendering_bounds(map_selection)

    print("BEFORE AGGREGATE")

    if _is_worker_up():
        print("WORKER AGGREGATE")
        result = tasks.task_lcms_aggregate.delay(filename, min_rt, max_rt, min_mz, max_mz, polarity_filter=polarity_filter, map_plot_quantization_level=map_plot_quantization_level)

        # Waiting
        while(1):
            if result.ready():
                break
            sleep(0.25)
        agg_dict, all_ms2_mz, all_ms2_rt, all_ms2_scan, all_ms3_mz, all_ms3_rt, all_ms3_scan = result.get()
    else:
        print("CALL AGGREGATE")
        agg_dict, all_ms2_mz, all_ms2_rt, all_ms2_scan, all_ms3_mz, all_ms3_rt, all_ms3_scan = tasks.task_lcms_aggregate(filename, min_rt, max_rt, min_mz, max_mz, polarity_filter=polarity_filter, map_plot_quantization_level=map_plot_quantization_level)

    lcms_fig = lcms_map._create_map_fig(agg_dict, all_ms2_mz, all_ms2_rt, all_ms2_scan, all_ms3_mz, all_ms3_rt, all_ms3_scan, map_selection=map_selection, show_ms2_markers=show_ms2_markers, polarity_filter=polarity_filter, highlight_box=highlight_box)

    return lcms_fig


# This calls the actual feature finding so it can be cached
@cache.memoize()
def _perform_feature_finding(filename, feature_finding=None):
    import tasks

    print("BEFORE WORKER")
    print(_is_worker_up())

    # Checking if local or worker
    if _is_worker_up():
        # If we have the celery instance up, we'll push it
        result = tasks.task_featurefinding.delay(filename, feature_finding)

        # Waiting
        while(1):
            if result.ready():
                break
            sleep(3)
        features_list = result.get()
    else:
        features_list = tasks.task_featurefinding(filename, feature_finding)

    features_df = pd.DataFrame(features_list)

    return features_df


@cache.memoize()
def _resolve_overlay(overlay_usi, overlay_mz, overlay_rt, overlay_filter_column, overlay_filter_value, overlay_size, overlay_color, overlay_hover):
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

    overlay_df = utils._resolve_overlay(overlay_usi, overlay_mz, overlay_rt, overlay_filter_column, overlay_filter_value, overlay_size, overlay_color, overlay_hover)
    
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
            pass

    return lcms_fig, features_df

def _integrate_overlay(overlay_usi, lcms_fig, overlay_mz, overlay_rt, overlay_filter_column, overlay_filter_value, overlay_size, overlay_color, overlay_hover, map_selection=None):
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
        overlay_df = _resolve_overlay(overlay_usi, overlay_mz, overlay_rt, overlay_filter_column, overlay_filter_value, overlay_size, overlay_color, overlay_hover)

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
@app.callback([Output('tic-plot', 'figure'), Output('tic-plot', 'config')],
              [Input('usi', 'value'), 
              Input('image_export_format', 'value'), 
              Input("plot_theme", "value"), 
              Input("tic_option", "value"),
              Input("polarity-filtering", "value"),
              Input("show_multiple_tic", "value")])
def draw_tic(usi, export_format, plot_theme, tic_option, polarity_filter, show_multiple_tic):
    # Calculating all TICs for all USIs
    all_usi = usi.split("\n")

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
        fig = px.line(merged_tic_df, x="rt", y="tic", title='TIC Plot', template=plot_theme, color="USI")
    else:
        tic_df = _perform_tic(usi.split("\n")[0], tic_option=tic_option, polarity_filter=polarity_filter)
        fig = px.line(tic_df, x="rt", y="tic", title='TIC Plot', template=plot_theme)

    # For Drawing and Exporting
    graph_config = {
        "toImageButtonOptions":{
            "format": export_format,
            'height': None, 
            'width': None,
        }
    }

    return [fig, graph_config]

# Creating TIC plot
@app.callback([Output('tic-plot2', 'figure'), Output('tic-plot2', 'config')],
              [Input('usi2', 'value'), 
              Input('image_export_format', 'value'), 
              Input("plot_theme", "value"), 
              Input("tic_option", "value"),
              Input("polarity-filtering2", "value"),
              Input("show_multiple_tic", "value")])
def draw_tic2(usi, export_format, plot_theme, tic_option, polarity_filter, show_multiple_tic):
    # Calculating all TICs for all USIs
    all_usi = usi.split("\n")

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
        fig = px.line(merged_tic_df, x="rt", y="tic", title='TIC Plot', template=plot_theme, color="USI")
    else:
        tic_df = _perform_tic(usi.split("\n")[0], tic_option=tic_option, polarity_filter=polarity_filter)
        fig = px.line(tic_df, x="rt", y="tic", title='TIC Plot', template=plot_theme)

    # For Drawing and Exporting
    graph_config = {
        "toImageButtonOptions":{
            "format": export_format,
            'height': None, 
            'width': None,
        }
    }

    return [fig, graph_config]

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
                result = tasks.task_xic.delay(local_filename, [xic_value], xic_tolerance, xic_ppm_tolerance, xic_tolerance_unit, rt_min, rt_max, polarity_filter, get_ms2=GET_MS2)
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

# Creating XIC plot
@app.callback([Output('xic-plot', 'figure'), Output('xic-plot', 'config'), Output("integration-table", "children"), Output("integration-boxplot", "children")],
              [Input('usi', 'value'), 
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
              Input('polarity-filtering', 'value'),
              Input('image_export_format', 'value'), 
              Input("plot_theme", "value")])
def draw_xic(usi, usi2, xic_mz, xic_formula, xic_peptide, xic_tolerance, xic_ppm_tolerance, xic_tolerance_unit, xic_rt_window, xic_integration_type, xic_norm, xic_file_grouping, polarity_filter, export_format, plot_theme):

    # For Drawing and Exporting
    graph_config = {
        "toImageButtonOptions":{
            "format": export_format,
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

    # Performing XIC for all USI in the list
    merged_df_long, ms2_data = _perform_batch_xic(usi_list, usi1_list, usi2_list, xic_norm, all_xic_values, parsed_xic_da_tolerance, parsed_xic_ppm_tolerance, xic_tolerance_unit, rt_min, rt_max, polarity_filter)

    # Limit the plotting USIs, but not the integrals below
    plotting_df = merged_df_long
    plot_usi_list = usi_list[:MAX_XIC_PLOT_LCMS_FILES]
    plotting_df = plotting_df[plotting_df["USI"].isin(plot_usi_list)]

    # Cleaning up the USI to show
    plotting_df["USI"] = plotting_df["USI"].apply(lambda x: download._get_usi_display_filename(x))

    
    if len(plot_usi_list) == 1:
        if xic_file_grouping == "FILE":
            height = 400
            fig = px.scatter(plotting_df, x="rt", y="value", color="variable", title='XIC Plot - Single File', height=height, template=plot_theme)
        else:
            height = 400 * len(all_xic_values)
            fig = px.scatter(plotting_df, x="rt", y="value", facet_row="variable", title='XIC Plot - Single File', height=height, template=plot_theme)
    else:
        if xic_file_grouping == "FILE":
            height = 400 * len(plot_usi_list)
            fig = px.scatter(plotting_df, x="rt", y="value", color="variable", facet_row="USI", title='XIC Plot - Grouped Per File', height=height, template=plot_theme)
        elif xic_file_grouping == "MZ":
            height = 400 * len(all_xic_values)
            fig = px.scatter(plotting_df, x="rt", y="value", color="USI", facet_row="variable", title='XIC Plot - Grouped Per M/Z', height=height, template=plot_theme)
        elif xic_file_grouping == "GROUP":
            height = 400 * len(all_xic_values)
            fig = px.scatter(plotting_df, x="rt", y="value", color="GROUP", facet_row="variable", title='XIC Plot - By Group', height=height, template=plot_theme)

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

    table_graph = dash.no_update
    box_graph = dash.no_update

    try:
        # Doing actual integration
        integral_df = _integrate_files(merged_df_long, xic_integration_type)

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
        box_fig = px.box(integral_df, x="GROUP", y="value", facet_col="variable", facet_col_wrap=3, color="GROUP", height=box_height, boxmode="overlay", template=plot_theme)
        box_graph = dcc.Graph(figure=box_fig, config=graph_config)
    except:
        pass

    return [fig, graph_config, table_graph, box_graph]

# Inspiration for structure from
# https://github.com/plotly/dash-datashader
# https://community.plotly.com/t/heatmap-is-slow-for-large-data-arrays/21007/2

@app.callback([Output('map-plot', 'figure'), Output('download-link', 'children'), Output('map-plot-zoom', 'children'), Output("feature-finding-table", 'children')],
              [Input('url', 'search'), 
              Input('usi', 'value'), 
              Input('map-plot', 'relayoutData'), 
              Input('map_plot_quantization_level', 'value'), 
              Input('show_ms2_markers', 'value'),
              Input('polarity-filtering', 'value'),
              Input('overlay-usi', 'value'),
              Input('overlay-mz', 'value'),
              Input('overlay-rt', 'value'),
              Input('overlay-size', 'value'),
              Input('overlay-color', 'value'),
              Input('overlay-hover', 'value'),
              Input('overlay-filter-column', 'value'),
              Input('overlay-filter-value', 'value'),
              Input('feature_finding_type', 'value'),
              Input('run-feature-finding-button', 'n_clicks')
              ],
              [
                State('feature_finding_ppm', 'value'),
                State('feature_finding_noise', 'value'),
                State('feature_finding_min_peak_rt', 'value'),
                State('feature_finding_max_peak_rt', 'value'),
                State('feature_finding_rt_tolerance', 'value'),
              ])
def draw_file(url_search, usi, 
                map_selection, map_plot_quantization_level,
                show_ms2_markers, polarity_filter, 
                overlay_usi, overlay_mz, overlay_rt, overlay_size, overlay_color, overlay_hover, overlay_filter_column, overlay_filter_value, 
                feature_finding_type,
                feature_finding_click,
                feature_finding_ppm,
                feature_finding_noise,
                feature_finding_min_peak_rt,
                feature_finding_max_peak_rt, 
                feature_finding_rt_tolerance):
    triggered_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    usi_list = usi.split("\n")

    remote_link, local_filename = _resolve_usi(usi_list[0])

    if show_ms2_markers == 1:
        show_ms2_markers = True
    else:
        show_ms2_markers = False

    current_map_selection, highlight_box, min_rt, max_rt, min_mz, max_mz = _resolve_map_plot_selection(url_search, usi, local_filename, ui_map_selection=map_selection)

    import sys
    print(triggered_id, file=sys.stderr)
    print(url_search, file=sys.stderr)


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

        
    # Doing LCMS Map
    map_fig = _create_map_fig(local_filename, map_selection=current_map_selection, show_ms2_markers=show_ms2_markers, polarity_filter=polarity_filter, highlight_box=highlight_box, map_plot_quantization_level=map_plot_quantization_level)

    # Adding on Feature Finding data
    map_fig, features_df = _integrate_feature_finding(local_filename, map_fig, map_selection=current_map_selection, feature_finding=feature_finding_params)

    # Adding on Overlay Data
    map_fig = _integrate_overlay(overlay_usi, map_fig, overlay_mz, overlay_rt, overlay_filter_column, overlay_filter_value, overlay_size, overlay_color, overlay_hover, map_selection=current_map_selection)

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


    return [map_fig, remote_link, json.dumps(map_selection), table_graph]


@app.callback([Output('map-plot2', 'figure')],
              [Input('url', 'search'), 
              Input('usi2', 'value'), 
              Input('map-plot', 'relayoutData'), 
              Input('map_plot_quantization_level', 'value'), 
              Input('show_ms2_markers', 'value'),
              Input("show_lcms_2nd_map", "value"),
              Input('polarity-filtering2', 'value')])
def draw_file2(url_search, usi, 
                map_selection, map_plot_quantization_level, 
                show_ms2_markers, show_lcms_2nd_map, polarity_filter):

    if show_lcms_2nd_map is False:
        return [dash.no_update]

    triggered_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    usi_list = usi.split("\n")

    remote_link, local_filename = _resolve_usi(usi_list[0])

    if show_ms2_markers == 1:
        show_ms2_markers = True
    else:
        show_ms2_markers = False

    current_map_selection, highlight_box, min_rt, max_rt, min_mz, max_mz = _resolve_map_plot_selection(url_search, usi, local_filename, ui_map_selection=map_selection)

    # Doing LCMS Map
    map_fig = _create_map_fig(local_filename, map_selection=current_map_selection, show_ms2_markers=show_ms2_markers, polarity_filter=polarity_filter, highlight_box=highlight_box, map_plot_quantization_level=map_plot_quantization_level)

    return [map_fig]


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


@app.callback(Output('link-button', 'children'),
              [Input('usi', 'value'), 
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
              Input("ms2_identifier", "value"),
              Input("map-plot-zoom", "children"),
              Input('polarity-filtering', 'value'),
              Input('polarity-filtering2', 'value'),
              Input("show_lcms_2nd_map", "value"),
              Input("tic_option", "value"),
              Input("overlay-usi", "value"),
              Input("overlay-mz", "value"),
              Input("overlay-rt", "value"),
              Input("overlay-color", "value"),
              Input("overlay-size", "value"),
              Input("overlay-hover", "value"),
              Input('overlay-filter-column', 'value'),
              Input('overlay-filter-value', 'value'),
              Input("feature_finding_type", "value"),
              Input("feature_finding_ppm", "value"),
              Input("feature_finding_noise", "value"),
              Input("feature_finding_min_peak_rt", "value"),
              Input("feature_finding_max_peak_rt", "value"),
              Input("feature_finding_rt_tolerance", "value"),
              ])
def create_link(usi, usi2, xic_mz, xic_formula, xic_peptide, 
                xic_tolerance, xic_ppm_tolerance, xic_tolerance_unit, xic_rt_window, xic_norm, xic_file_grouping, 
                xic_integration_type, show_ms2_markers, ms2_identifier, map_plot_zoom, polarity_filtering, polarity_filtering2, show_lcms_2nd_map, tic_option,
                overlay_usi, overlay_mz, overlay_rt, overlay_color, overlay_size, overlay_hover, overlay_filter_column, overlay_filter_value,
                feature_finding_type, feature_finding_ppm, feature_finding_noise, feature_finding_min_peak_rt, feature_finding_max_peak_rt, feature_finding_rt_tolerance):

    url_params = {}
    url_params["xicmz"] = xic_mz
    url_params["xic_formula"] = xic_formula
    url_params["xic_peptide"] = xic_peptide
    url_params["xic_tolerance"] = xic_tolerance
    url_params["xic_ppm_tolerance"] = xic_ppm_tolerance
    url_params["xic_tolerance_unit"] = xic_tolerance_unit
    url_params["xic_rt_window"] = xic_rt_window
    url_params["xic_norm"] = xic_norm
    url_params["xic_file_grouping"] = xic_file_grouping
    url_params["xic_integration_type"] = xic_integration_type
    url_params["show_ms2_markers"] = show_ms2_markers
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

    hash_params = {}
    hash_params["usi"] = usi
    hash_params["usi2"] = usi2

    full_url = "/?{}#{}".format(urllib.parse.urlencode(url_params), json.dumps(hash_params))
    url_provenance = dbc.Button("Link to these plots", block=True, color="primary", className="mr-1")
    provenance_link_object = dcc.Link(url_provenance, href=full_url, target="_blank")

    return provenance_link_object



@app.callback(Output('network-link-button', 'children'),
              [Input('usi', 'value'), 
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

    if len(g1_list) > 0 or len(g0_list) > 0:
        parameters = {}
        parameters["workflow"] = "METABOLOMICS-SNETS-V2"
        parameters["spec_on_server"] = ";".join(g1_list)
        parameters["spec_on_server_group2"] = ";".join(g2_list)

        gnps_url = "https://gnps.ucsd.edu/ProteoSAFe/index.jsp?params="
        gnps_url = gnps_url + urllib.parse.quote(json.dumps(parameters))

        url_provenance = dbc.Button("Molecular Network {} Files".format(len(g1_list) + len(g2_list)), block=True, color="secondary", className="mr-1")
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
    table = dbc.Table.from_dataframe(stats_df, striped=True, bordered=True, hover=True, size="sm")

    return [table]


@app.callback([Output('overlay-hover', 'options'), Output('overlay-color', 'options'), Output('overlay-size', 'options')],
              [Input('overlay-usi', 'value')])
@cache.memoize()
def get_overlay_options(overlay_usi):
    """This function finds all the overlay options

    Args:
        overlay_usi ([type]): [description]

    Returns:
        [type]: [description]
    """

    overlay_df = _resolve_overlay(overlay_usi, "", "", "", "", "", "", "")

    columns = list(overlay_df.columns)

    options = []

    for column in columns:
        options.append({"label": column, "value": column})

    return [options, options, options]

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
    Output("advanced_visualization_modal", "is_open"),
    [Input("advanced_visualization_modal_button", "n_clicks"), Input("advanced_visualization_modal_close", "n_clicks")],
    [State("advanced_visualization_modal", "is_open")],
)(toggle_modal)



if __name__ == "__main__":
    app.run_server(debug=True, port=5000, host="0.0.0.0")
