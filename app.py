# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_table
import plotly.express as px
import plotly.graph_objects as go 
from dash.dependencies import Input, Output, State
import dash_daq as daq
import os
from zipfile import ZipFile
import urllib.parse
from scipy import integrate
from flask import Flask, send_from_directory

import pandas as pd
import requests
import uuid
import werkzeug

import pymzml
import numpy as np
import datashader as ds
from tqdm import tqdm
import json

from collections import defaultdict
import uuid
import base64
from flask_caching import Cache

from utils import _resolve_usi
from utils import _calculate_file_stats
from utils import _get_scan_polarity
from utils import _resolve_map_plot_selection, _get_param_from_url, _spectrum_generator
from utils import MS_precisions
from utils import _convert_mzML
import lcms_map
from formula_utils import get_adduct_mass
from molmass import Formula
from pyteomics import mass

from xic import _xic_file_slow, _xic_file_fast



server = Flask(__name__)
app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = 'GNPS - LCMS Browser'
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
placeholder_ms2_plot = px.imshow(agg, origin='lower', labels={'color':'Log10(Abundance)'}, color_continuous_scale="Hot")
placeholder_xic_plot = px.line(df, x="rt", y="mz", title='XIC Placeholder')

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
                dbc.NavItem(dbc.NavLink("GNPS LCMS Dashboard - Version 0.15", href="/")),
            ],
        navbar=True)
    ],
    color="light",
    dark=False,
    sticky="top",
)

DATASELECTION_CARD = [
    dbc.CardHeader(html.H5("Data Selection")),
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
                id="ms2-plot",
                children=[html.Div([html.Div(id="loading-output-6")])],
                type="default",
            ),
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
                children=[html.Div([html.Div(id="loading-output-100")])],
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
                figure=placeholder_ms2_plot,
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

EXAMPLE_DASHBOARD = [
    dbc.CardHeader(html.H5("Example Exploration Dashboards")),
    dbc.CardBody(
        [
            html.A("LCMS Multiple m/z XIC for QC Files", href="/?usi=mzspec%3AMSV000085852%3AQC_0&xicmz=271.0315%3B278.1902%3B279.0909%3B285.0205%3B311.0805%3B314.1381&xic_tolerance=0.5&xic_norm=No&show_ms2_markers=1&ms2_identifier="),
            html.Br(),
            html.A("LCMS Side By Side Visualization", href='/?usi=mzspec%3AMSV000085852%3AQC_0&usi2=mzspec%3AMSV000085852%3AQC_1&xicmz=271.0315%3B278.1902%3B279.0909%3B285.0205%3B311.0805%3B314.1381%3B833.062397505189&xic_tolerance=0.5&xic_rt_window=&xic_norm=False&xic_file_grouping=FILE&show_ms2_markers=True&ms2_identifier=MS2%3A2277&show_lcms_2nd_map=True&map_plot_zoom=%7B"xaxis.range%5B0%5D"%3A+3.2846848333333334%2C+"xaxis.range%5B1%5D"%3A+3.5981121270270275%2C+"yaxis.range%5B0%5D"%3A+815.4334319736646%2C+"yaxis.range%5B1%5D"%3A+853.5983309206755%7D'),
            html.Br(),
            html.A("LCMS XIC by Formula - QC Amitryptiline", href='/?usi=mzspec%3AMSV000085852%3AQC_0&usi2=&xicmz=&xic_formula=C20H23N&xic_tolerance=0.01&xic_ppm_tolerance=20&xic_tolerance_unit=Da&xic_rt_window=&xic_norm=False&xic_file_grouping=FILE&xic_integration_type=AUC&show_ms2_markers=True&ms2_identifier=None&show_lcms_2nd_map=False&map_plot_zoom=%7B"autosize"%3A+true%7D&polarity_filtering=None&polarity_filtering2=None&tic_option=TIC'),
            html.Br(),
            html.A("LCMS auto zoomed by scan in USI", href="/?usi=mzspec:MSV000085852:QC_0:scan:2277"),
            html.Br(),
            html.A("Thermo LCMS", href="/?usi=mzspec%3AMSV000084951%3AAH22&xicmz=870.9543493652343&xic_tolerance=0.5&xic_norm=False&show_ms2_markers=True&ms2_identifier=None"),
            html.Br(),
            html.A("Sciex LCMS", href="/?usi=mzspec%3AMSV000085042%3AQC1_pos-QC1&xicmz=&xic_tolerance=0.5&xic_norm=False&show_ms2_markers=True&ms2_identifier=None"),
            html.Br(),
            html.A("Bruker LCMS", href="/?usi=mzspec%3AMSV000086015%3AStdMix_02__GA2_01_55623&xicmz=&xic_tolerance=0.5&xic_norm=False&show_ms2_markers=True&ms2_identifier=None"),
            html.Br(),
            html.A("Waters LCMS", href="/?usi=mzspec%3AMSV000084977%3AOEPKS7_B_1_neg&xicmz=&xic_tolerance=0.5&xic_norm=False&show_ms2_markers=True&ms2_identifier=None"),
            html.Br(),
            html.A("Agilent LCMS", href="/?usi=mzspec:MSV000084060:KM0001"),
            html.Br(),
            html.A("Thermo Proteomics LCMS", href="/?usi=mzspec:MSV000079514:Adult_CD4Tcells_bRP_Elite_28_f01"),
            html.Br(),
            html.A("LCMS from Metabolights", href="/?usi=mzspec:MTBLS1124:QC07.mzML"),
            html.Br(),
            html.A("LCMS from Metabolomics Workbench that include MS/MS", href="/?usi=mzspec:ST000763:20160411_MB_CS00000074-1_P.mzXML"),
            html.Br(),
            html.A("Thermo GCMS", href="/?usi=mzspec:MSV000086150:BA1.mzML"),
            html.Br(),
            html.A("GCMS in CDF Format", href="/?usi=mzspec:GNPS:TASK-ce31b7fdd01244dbb31478147889de1e-f.aaksenov/GC_data/Sterols_data/Samples/0104006.cdf"),
            html.Br(),
            html.A("Thermo LCMS from GNPS Analysis Classical Molecular Networking Task", href="/?usi=mzspec:GNPS:TASK-5ecfcf81cb3c471698995b194d8246a0-f.MSV000085444/ccms_peak/peak/Hui_N1_fe.mzML#%7B%7D"),
            html.Br(),
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
                figure=placeholder_ms2_plot,
                config={
                    'doubleClick': 'reset'
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
                style={"width": "50%"}
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
                style={"width": "50%"}
            )
        ], style={"marginTop": 30}),

        # Show Data
        dbc.Row([
            dbc.Collapse(
                [
                    dbc.Col([
                        dbc.Card(MIDDLE_DASHBOARD),
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
    ],
    fluid=True,
    className="",
)

app.layout = html.Div(children=[NAVBAR, BODY])





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
@app.callback([Output('debug-output', 'children'), Output('ms2-plot', 'children')],
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

    if "MS2" in ms2_identifier or "MS3" in ms2_identifier:
        usi_image_url = "https://metabolomics-usi.ucsd.edu/svg/?usi={}&plot_title={}".format(updated_usi, ms2_identifier)
        usi_url = "https://metabolomics-usi.ucsd.edu/spectrum/?usi={}".format(updated_usi)

        # Lets also make a MASST link here
        # We'll have to get the MS2 peaks from USI
        usi_json_url = "https://metabolomics-usi.ucsd.edu/json/?usi={}".format(updated_usi)
        
        try:
            r = requests.get(usi_json_url)
            spectrum_json = r.json()
            peaks = spectrum_json["peaks"]
            precursor_mz = spectrum_json["precursor_mz"]
        except:
            # Lets look at file on disk
            print("JSON USI EXCEPTION")
            remote_link, local_filename = _resolve_usi(usi)
            run = pymzml.run.Reader(local_filename, MS_precisions=MS_precisions)
            spectrum = run[scan_number]
            peaks = spectrum.peaks("raw")
            precursor_mz = spectrum.selected_precursors[0]["mz"]

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

        return ["MS2", [dcc.Graph(figure=interactive_fig, config=graph_config), USI_button, html.Br(), masst_button]]

    if "MS1" in ms2_identifier:
        usi_image_url = "https://metabolomics-usi.ucsd.edu/svg/?usi={}&plot_title={}".format(updated_usi, ms2_identifier)
        usi_url = "https://metabolomics-usi.ucsd.edu/spectrum/?usi={}".format(updated_usi)

        try:
            xic_mz = float(xic_mz)

            # Adding zoom in the USI plotter
            min_mz = xic_mz - 10
            max_mz = xic_mz + 10
            
            usi_png_url += "&mz_min={}&mz_max={}".format(min_mz, max_mz)
            usi_url += "&mz_min={}&mz_max={}".format(min_mz, max_mz)
        except:
            pass

        usi_json_url = "https://metabolomics-usi.ucsd.edu/json/?usi={}".format(updated_usi)
        r = requests.get(usi_json_url)
        spectra_obj = r.json()
        peaks = spectra_obj["peaks"]
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
        return ["MS1", [dcc.Graph(figure=interactive_fig, config=graph_config), USI_button]]

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
                Output("polarity-filtering2", "value"),],
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

    
    return [xic_formula, xic_peptide, xic_tolerance, xic_ppm_tolerance, xic_tolerance_unit, xic_rt_window, xic_norm, xic_file_grouping, xic_integration_type, show_ms2_markers, show_lcms_2nd_map, tic_option, polarity_filtering, polarity_filtering2]



# Handling file upload
@app.callback([Output('usi', 'value'), Output('usi2', 'value'), Output('debug-output-2', 'children')],
              [Input('url', 'search'), Input('upload-data', 'contents')],
              [State('upload-data', 'filename'),
               State('upload-data', 'last_modified')])
def update_output(search, filecontent, filename, filedate):
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
            temp_filename_mzXML = os.path.join("temp", "{}.mzXML".format(mangled_name))
            temp_filename = os.path.join("temp", "{}.mzXML".format(mangled_name))
            data = filecontent.encode("utf8").split(b";base64,")[1]

            with open(temp_filename_mzXML, "wb") as temp_file:
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
    usi = _get_param_from_url(search, "usi", usi)

    # Resolving USI
    try:
        usi2 = str(urllib.parse.parse_qs(search[1:])["usi2"][0])
    except:
        pass

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
def _create_map_fig(filename, map_selection=None, show_ms2_markers=True, polarity_filter="None", highlight_box=None):
    return lcms_map._create_map_fig(filename, map_selection=map_selection, show_ms2_markers=show_ms2_markers, polarity_filter=polarity_filter, highlight_box=highlight_box)

# Creating TIC plot
@app.callback([Output('tic-plot', 'figure'), Output('tic-plot', 'config')],
              [Input('usi', 'value'), 
              Input('image_export_format', 'value'), 
              Input("plot_theme", "value"), 
              Input("tic_option", "value"),
              Input("polarity-filtering", "value")])
def draw_tic(usi, export_format, plot_theme, tic_option, polarity_filter):
    tic_df = _perform_tic(usi, tic_option=tic_option, polarity_filter=polarity_filter)
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
              Input("polarity-filtering2", "value")])
def draw_tic2(usi, export_format, plot_theme, tic_option, polarity_filter):
    tic_df = _perform_tic(usi, tic_option=tic_option, polarity_filter=polarity_filter)
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

    from tic import _tic_file_slow

    return _tic_file_slow(local_filename, tic_option=tic_option, polarity_filter=polarity_filter)
    


@cache.memoize()
def _perform_xic(usi, all_xic_values, xic_tolerance, xic_ppm_tolerance, xic_tolerance_unit, rt_min, rt_max, polarity_filter, get_ms2=False):
    # This is the business end of XIC extraction
    remote_link, local_filename = _resolve_usi(usi)


    if get_ms2 is False:
        try:
            return _xic_file_fast(local_filename, all_xic_values, xic_tolerance, xic_ppm_tolerance, xic_tolerance_unit, rt_min, rt_max, polarity_filter)
        except:
            pass

    return _xic_file_slow(local_filename, all_xic_values, xic_tolerance, xic_ppm_tolerance, xic_tolerance_unit, rt_min, rt_max, polarity_filter)



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
    df_long_list = []
    for usi_element in usi_list:
        if len(usi_list) == 1 and len(all_xic_values) == 1:
            xic_df, ms2_data = _perform_xic(usi_element, all_xic_values, parsed_xic_da_tolerance, parsed_xic_ppm_tolerance, xic_tolerance_unit, rt_min, rt_max, polarity_filter, get_ms2=True)
        else:
            xic_df, ms2_data = _perform_xic(usi_element, all_xic_values, parsed_xic_da_tolerance, parsed_xic_ppm_tolerance, xic_tolerance_unit, rt_min, rt_max, polarity_filter, get_ms2=False)

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

    merged_df_long = pd.concat(df_long_list)

    # Limit the plotting USIs, but not the integrals below
    plotting_df = merged_df_long
    plot_usi_list = usi_list[:MAX_XIC_PLOT_LCMS_FILES]
    plotting_df = plotting_df[plotting_df["USI"].isin(plot_usi_list)]
    
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

@app.callback([Output('map-plot', 'figure'), Output('download-link', 'children'), Output('map-plot-zoom', 'children')],
              [Input('url', 'search'), 
              Input('usi', 'value'), 
              Input('map-plot', 'relayoutData'), 
              Input('show_ms2_markers', 'value'),
              Input('polarity-filtering', 'value')])
def draw_file(url_search, usi, map_selection, show_ms2_markers, polarity_filter):
    triggered_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    usi_list = usi.split("\n")

    remote_link, local_filename = _resolve_usi(usi_list[0])

    if show_ms2_markers == 1:
        show_ms2_markers = True
    else:
        show_ms2_markers = False

    current_map_selection, highlight_box = _resolve_map_plot_selection(url_search, usi)

    import sys
    print(triggered_id, file=sys.stderr)
    print(url_search, file=sys.stderr)
    print("MAP SELECTION XXXXXXXXXX", map_selection, current_map_selection, triggered_id, usi, file=sys.stderr)

    # We have to do a bit of convoluted object, if {'autosize': True}, that means loading from the URL
    try:
        # Force an override if user input is detected in map_selection
        if "xaxis.autorange" in map_selection:
            current_map_selection = map_selection
        if "xaxis.range[0]" in map_selection:
            current_map_selection = map_selection
        if "autosize" in map_selection:
            pass
    except:
        pass

    # Doing LCMS Map
    map_fig = _create_map_fig(local_filename, map_selection=current_map_selection, show_ms2_markers=show_ms2_markers, polarity_filter=polarity_filter, highlight_box=highlight_box)

    return [map_fig, remote_link, json.dumps(map_selection)]


@app.callback([Output('map-plot2', 'figure')],
              [Input('url', 'search'), 
              Input('usi2', 'value'), 
              Input('map-plot', 'relayoutData'), 
              Input('show_ms2_markers', 'value'),
              Input("show_lcms_2nd_map", "value"),
              Input('polarity-filtering2', 'value')])
def draw_file2(url_search, usi, map_selection, show_ms2_markers, show_lcms_2nd_map, polarity_filter):
    if show_lcms_2nd_map is False:
        return [dash.no_update]

    triggered_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    usi_list = usi.split("\n")

    remote_link, local_filename = _resolve_usi(usi_list[0])

    if show_ms2_markers == 1:
        show_ms2_markers = True
    else:
        show_ms2_markers = False

    current_map_selection, highlight_box = _resolve_map_plot_selection(url_search, usi)
    
    # We have to do a bit of convoluted object, if {'autosize': True}, that means the original load
    try:
        if "xaxis.autorange" in map_selection:
            current_map_selection = map_selection
        if "xaxis.range[0]" in map_selection:
            current_map_selection = map_selection
        if "autosize" in map_selection:
            pass
    except:
        pass

    # Doing LCMS Map
    map_fig = _create_map_fig(local_filename, map_selection=current_map_selection, show_ms2_markers=show_ms2_markers, polarity_filter=polarity_filter, highlight_box=highlight_box)

    return [map_fig]

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
              Input("tic_option", "value")])
def create_link(usi, usi2, xic_mz, xic_formula, xic_peptide, xic_tolerance, xic_ppm_tolerance, xic_tolerance_unit, xic_rt_window, xic_norm, xic_file_grouping, xic_integration_type, show_ms2_markers, ms2_identifier, map_plot_zoom, polarity_filtering, polarity_filtering2, show_lcms_2nd_map, tic_option):

    url_params = {}
    url_params["usi"] = usi
    url_params["usi2"] = usi2
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

    url_provenance = dbc.Button("Link to these plots", block=True, color="primary", className="mr-1")
    provenance_link_object = dcc.Link(url_provenance, href="/?" + urllib.parse.urlencode(url_params) , target="_blank")

    return provenance_link_object

# Creating TIC plot
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

    all_file_stats = [_calculate_file_stats(usi) for usi in usi_list]
    stats_df = pd.DataFrame(all_file_stats)        
    table = dbc.Table.from_dataframe(stats_df, striped=True, bordered=True, hover=True, size="sm")

    return [table]

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


if __name__ == "__main__":
    app.run_server(debug=True, port=5000, host="0.0.0.0")
