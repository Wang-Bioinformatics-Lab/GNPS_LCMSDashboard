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

MS_precisions = {
    1 : 5e-6,
    2 : 20e-6,
    3 : 20e-6
}

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

NAVBAR = dbc.Navbar(
    children=[
        dbc.NavbarBrand(
            html.Img(src="https://gnps-cytoscape.ucsd.edu/static/img/GNPS_logo.png", width="120px"),
            href="https://gnps.ucsd.edu"
        ),
        dbc.Nav(
            [
                dbc.NavItem(dbc.NavLink("GNPS LCMS Dashboard - Version 0.8", href="#")),
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
                html.Br(),
                html.H5(children='LCMS Viewer Options'),
                dbc.Row([
                    dbc.Col(
                        dbc.FormGroup(
                            [
                                dbc.Label("Show MS2 Markers", html_for="show_ms2_markers", width=4.8, style={"width":"150px", "margin-left": "25px"}),
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
                                dbc.Label("Show USI2 LCMS Map", html_for="show_lcms_2nd_map", width=5.8, style={"width":"200px"}),
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
                # Linkouts
                dcc.Loading(
                    id="link-button",
                    children=[html.Div([html.Div(id="loading-output-9")])],
                    type="default",
                )
            ], className="col-sm"),
            ## Right Panel
            dbc.Col([
                html.H5(children='XIC Options'),
                dbc.InputGroup(
                    [
                        dbc.InputGroupAddon("XIC m/z", addon_type="prepend"),
                        dbc.Input(id='xic_mz', placeholder="Enter m/z to XIC"),
                    ],
                    className="mb-3",
                ),
                dbc.Row([
                    dbc.Col(
                        dbc.InputGroup(
                            [
                                dbc.InputGroupAddon("XIC Tolerance", addon_type="prepend"),
                                dbc.Input(id='xic_tolerance', placeholder="Enter Da Tolerance", value="0.5"),
                            ],
                            className="mb-3",
                        ),
                    ),
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
                dbc.Row([
                    dbc.Col(
                        dbc.InputGroup(
                            [
                                dbc.InputGroupAddon("XIC Retention Time Window", addon_type="prepend"),
                                dbc.Input(id='xic_rt_window', placeholder="Enter RT Window (e.g. 1-2)", value=""),
                            ],
                            className="mb-3",
                        ),
                    ),
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
        dbc.Row([
            dbc.Col(
                dbc.Card(MIDDLE_DASHBOARD),
                className="w-50"
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


# Returns remote_link and local filepath
def resolve_usi(usi):
    usi_splits = usi.split(":")

    if "LOCAL" in usi_splits[1]:
        return "", os.path.join("temp", os.path.basename(usi_splits[2]))

    if "MSV" in usi_splits[1]:
        # Test: mzspec:MSV000084494:GNPS00002_A3_p:scan:1
        # Bigger Test: mzspec:MSV000083388:1_p_153001_01072015:scan:12
        lookup_url = f'https://massive.ucsd.edu/ProteoSAFe/QuerySpectrum?id={usi}'
        lookup_request = requests.get(lookup_url)

        resolution_json = lookup_request.json()

        remote_path = None
        
        mzML_resolutions = [resolution for resolution in resolution_json["row_data"] if os.path.splitext(resolution["file_descriptor"])[1] == ".mzML"]
        mzXML_resolutions = [resolution for resolution in resolution_json["row_data"] if os.path.splitext(resolution["file_descriptor"])[1] == ".mzXML"]

        if len(mzML_resolutions) > 0:
            remote_path = mzML_resolutions[0]["file_descriptor"]
        elif len(mzXML_resolutions) > 0:
            remote_path = mzXML_resolutions[0]["file_descriptor"]

        # Format into FTP link
        remote_link = f"ftp://massive.ucsd.edu/{remote_path[2:]}"
    elif "GNPS" in usi_splits[1]:
        if "TASK-" in usi_splits[2]:

            # Test: mzspec:GNPS:TASK-de188599f53c43c3aaad95491743c784-spec/spec-00000.mzML:scan:31
            filename = "-".join(usi_splits[2].split("-")[2:])
            task = usi_splits[2].split("-")[1]

            remote_link = "http://gnps.ucsd.edu/ProteoSAFe/DownloadResultFile?task={}&block=main&file={}".format(task, filename)
        elif "QUICKSTART-" in usi_splits[2]:
            filename = "-".join(usi_splits[2].split("-")[2:])
            task = usi_splits[2].split("-")[1]

            remote_link = "http://gnps-quickstart.ucsd.edu/conversion/file?sessionid={}&filename={}".format(task, filename)
            print(remote_link)

    elif "MTBLS" in usi_splits[1]:
        dataset_accession = usi_splits[1]
        filename = usi_splits[2]
        remote_link = "ftp://ftp.ebi.ac.uk/pub/databases/metabolights/studies/public/{}/{}".format(dataset_accession, filename)

    # Getting Data Local, TODO: likely should serialize it
    local_filename = os.path.join("temp", werkzeug.utils.secure_filename(remote_link))
    filename, file_extension = os.path.splitext(local_filename)
    converted_local_filename = filename + ".mzML"
    
    if not os.path.isfile(converted_local_filename):
        temp_filename = os.path.join("temp", str(uuid.uuid4()) + file_extension)
        wget_cmd = "wget '{}' -O {}".format(remote_link, temp_filename)
        os.system(wget_cmd)
        os.rename(temp_filename, local_filename)

        temp_filename = os.path.join("temp", str(uuid.uuid4()) + ".mzML")
        # Lets do a conversion
        conversion_cmd = "export LC_ALL=C && ./bin/msconvert {} --mzML --32 --outfile {} --outdir {} --filter 'threshold count 500 most-intense'".format(local_filename, temp_filename, os.path.dirname(temp_filename))
        os.system(conversion_cmd)

        os.rename(temp_filename, converted_local_filename)

        local_filename = converted_local_filename

    return remote_link, converted_local_filename


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

        remote_link, local_filename = resolve_usi(usi)

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
    updated_usi = "mzspec:{}:{}:scan:{}".format(dataset, filename, str(ms2_identifier.split(":")[-1]))

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
        r = requests.get(usi_json_url)
        spectrum_json = r.json()
        peaks = spectrum_json["peaks"]
        precursor_mz = spectrum_json["precursor_mz"]

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

@app.callback([Output("xic_tolerance", "value"), 
                Output("xic_rt_window", "value"), 
                Output("xic_norm", "value"), 
                Output("xic_file_grouping", "value"),
                Output("show_ms2_markers", "value"),
                Output("show_lcms_2nd_map", "value")],
              [Input('url', 'search')])
def determine_url_only_parameters(search):
    
    xic_tolerance = "0.5"
    xic_norm = False
    show_ms2_markers = True
    xic_file_grouping = "FILE"
    xic_rt_window = ""
    show_lcms_2nd_map = False

    try:
        xic_tolerance = str(urllib.parse.parse_qs(search[1:])["xic_tolerance"][0])
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
    

    

    return [xic_tolerance, xic_rt_window, xic_norm, xic_file_grouping, show_ms2_markers, show_lcms_2nd_map]

# Handling file upload
@app.callback([Output('usi', 'value'), Output('usi2', 'value'), Output('debug-output-2', 'children')],
              [Input('url', 'search'), Input('upload-data', 'contents')],
              [State('upload-data', 'filename'),
               State('upload-data', 'last_modified')])
def update_output(search, filecontent, filename, filedate):
    usi = "mzspec:MSV000084494:GNPS00002_A3_p:scan:1"
    usi2 = ""

    if filecontent is not None:
        extension = os.path.splitext(filename)[1]
        if extension == ".mzML" and len(filecontent) < 100000000:
            temp_filename = os.path.join("temp", "{}.mzML".format(str(uuid.uuid4())))
            data = filecontent.encode("utf8").split(b";base64,")[1]

            with open(temp_filename, "wb") as temp_file:
                temp_file.write(base64.decodebytes(data))

            output_usi = "mzspec:LOCAL:{}".format(os.path.basename(temp_filename))

            return [output_usi, "FILE Uploaded {}".format(filename)]

    # Resolving USI
    try:
        usi = str(urllib.parse.parse_qs(search[1:])["usi"][0])
    except:
        pass

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


# Binary Search, returns target
def _find_lcms_rt(filename, rt_query):
    run = pymzml.run.Reader(filename, MS_precisions=MS_precisions)

    s = 0
    e = run.get_spectrum_count()

    while True:
        jump_point = int((e + s) / 2)

        # Jump out early
        if jump_point == 0:
            break
        
        if jump_point == run.get_spectrum_count():
            break

        if s == e:
            break

        if e - s == 1:
            break

        spec = run[ jump_point ]

        if spec.scan_time_in_minutes() < rt_query:
            s = jump_point
        elif spec.scan_time_in_minutes() > rt_query:
            e = jump_point
        else:
            break

    return e

def _spectrum_generator(filename, min_rt, max_rt):
    run = pymzml.run.Reader(filename, MS_precisions=MS_precisions)
    try:
        min_rt_index = _find_lcms_rt(filename, min_rt) # These are inclusive on left
        max_rt_index = _find_lcms_rt(filename, max_rt) + 1 # Exclusive on the right

        for spec_index in tqdm(range(min_rt_index, max_rt_index)):
            spec = run[spec_index]
            yield spec
        print("USED INDEX")
    except:
        for spec in run:
            yield spec
        print("USED BRUTEFORCE")

def _gather_lcms_data(filename, min_rt, max_rt, min_mz, max_mz):
    all_mz = []
    all_rt = []
    all_i = []
    all_scan = []
    all_index = []
    spectrum_index = 0
    number_spectra = 0

    all_ms2_mz = []
    all_ms2_rt = []
    all_ms2_scan = []

    all_ms3_mz = []
    all_ms3_rt = []
    all_ms3_scan = []

    # Iterating through all data with a custom scan iterator
    # It handles custom bounds on RT
    for spec in _spectrum_generator(filename, min_rt, max_rt):
        try:
            # Still waiting for the window
            if spec.scan_time_in_minutes() < min_rt:
                continue
            
            # We've passed the window
            if spec.scan_time_in_minutes() > max_rt:            
                break
        except:
            pass
        
        if spec.ms_level == 1:
            spectrum_index += 1

            number_spectra += 1
            rt = spec.scan_time_in_minutes()

            try:
                # Filtering peaks by mz
                peaks = spec.reduce(mz_range=(min_mz, max_mz))

                # Sorting by intensity
                peaks = peaks[peaks[:,1].argsort()]
                peaks = peaks[-100:]

                mz, intensity = zip(*peaks)

                all_mz += list(mz)
                all_i += list(intensity)
                all_rt += len(mz) * [rt]
                all_scan += len(mz) * [spec.ID]
                all_index += len(mz) * [number_spectra]
            except:
                pass
        elif spec.ms_level == 2:
            try:
                ms2_mz = spec.selected_precursors[0]["mz"]
                if ms2_mz < min_mz or ms2_mz > max_mz:
                    continue
                all_ms2_mz.append(ms2_mz)
                all_ms2_rt.append(spec.scan_time_in_minutes())
                all_ms2_scan.append(spec.ID)
            except:
                pass
        elif spec.ms_level == 3:
            try:
                ms3_mz = spec.selected_precursors[0]["mz"]
                if ms3_mz < min_mz or ms3_mz > max_mz:
                    continue
                all_ms3_mz.append(ms3_mz)
                all_ms3_rt.append(spec.scan_time_in_minutes())
                all_ms3_scan.append(spec.ID)
            except:
                pass

    ms1_results = {}
    ms1_results["mz"] = all_mz
    ms1_results["rt"] = all_rt
    ms1_results["i"] = all_i
    ms1_results["scan"] = all_scan
    ms1_results["index"] = all_index
    ms1_results["number_spectra"] = number_spectra

    ms2_results = {}
    ms2_results["all_ms2_mz"] = all_ms2_mz
    ms2_results["all_ms2_rt"] = all_ms2_rt
    ms2_results["all_ms2_scan"] = all_ms2_scan

    ms3_results = {}
    ms3_results["all_ms3_mz"] = all_ms3_mz
    ms3_results["all_ms3_rt"] = all_ms3_rt
    ms3_results["all_ms3_scan"] = all_ms3_scan

    return ms1_results, ms2_results, ms3_results

@cache.memoize()
def create_map_fig(filename, map_selection=None, show_ms2_markers=True):
    min_rt = 0
    max_rt = 1000000
    min_mz = 0
    max_mz = 2000

    if map_selection is not None:
        if "xaxis.range[0]" in map_selection:
            min_rt = float(map_selection["xaxis.range[0]"])
        if "xaxis.range[1]" in map_selection:
            max_rt = float(map_selection["xaxis.range[1]"])

        if "yaxis.range[0]" in map_selection:
            min_mz = float(map_selection["yaxis.range[0]"])
        if "yaxis.range[1]" in map_selection:
            max_mz = float(map_selection["yaxis.range[1]"])

    import time
    start_time = time.time()
    ms1_results, ms2_results, ms3_results = _gather_lcms_data(filename, min_rt, max_rt, min_mz, max_mz)
    end_time = time.time()
    print("READ FILE", end_time - start_time)

    start_time = time.time()

    all_mz = ms1_results["mz"]
    all_rt = ms1_results["rt"]
    all_i = ms1_results["i"]
    all_scan = ms1_results["scan"]
    all_index = ms1_results["index"]
    number_spectra = ms1_results["number_spectra"]

    all_ms2_mz = ms2_results["all_ms2_mz"]
    all_ms2_rt = ms2_results["all_ms2_rt"]
    all_ms2_scan = ms2_results["all_ms2_scan"]

    all_ms3_mz = ms3_results["all_ms3_mz"]
    all_ms3_rt = ms3_results["all_ms3_rt"]
    all_ms3_scan = ms3_results["all_ms3_scan"]
            
    df = pd.DataFrame()
    df["mz"] = all_mz
    df["i"] = all_i
    df["rt"] = all_rt
    df["scan"] = all_scan
    df["index"] = all_index

    min_size = min(number_spectra, int(max_mz - min_mz))
    width = max(min(min_size*4, 500), 20)
    height = max(min(int(min_size*1.75), 500), 20)

    cvs = ds.Canvas(plot_width=width, plot_height=height)
    agg = cvs.points(df,'rt','mz', agg=ds.sum("i"))

    end_time = time.time()
    print("Datashader Agg", end_time - start_time)

    zero_mask = agg.values == 0
    agg.values = np.log10(agg.values, where=np.logical_not(zero_mask))
    fig = px.imshow(agg, origin='lower', labels={'color':'Log10(abundance)'}, color_continuous_scale="Hot_r", height=600, template="plotly_white")
    fig.update_traces(hoverongaps=False)
    fig.update_layout(coloraxis_colorbar=dict(title='Abundance', tickprefix='1.e'))

    fig.update_xaxes(showline=True, linewidth=1, linecolor='black', showgrid=False)
    fig.update_yaxes(showline=True, linewidth=1, linecolor='black', gridwidth=3)

    too_many_ms2 = False
    if len(all_ms2_scan) > 5000 or len(all_ms3_scan) > 5000:
        too_many_ms2 = True

    if show_ms2_markers is True and too_many_ms2 is False:
        scatter_fig = go.Scatter(x=all_ms2_rt, y=all_ms2_mz, mode='markers', customdata=all_ms2_scan, marker=dict(color='blue', size=5, symbol="x"), name="MS2s")
        fig.add_trace(scatter_fig)

        if len(all_ms3_scan) > 0:
            scatter_ms3_fig = go.Scatter(x=all_ms3_rt, y=all_ms3_mz, mode='markers', customdata=all_ms3_scan, marker=dict(color='green', size=5, symbol="x"), name="MS3s")
            fig.add_trace(scatter_ms3_fig)

    

    return fig

# Creating TIC plot
@app.callback([Output('tic-plot', 'figure'), Output('tic-plot', 'config')],
              [Input('usi', 'value'), Input('image_export_format', 'value'), Input("plot_theme", "value")])
def draw_tic(usi, export_format, plot_theme):
    tic_df = perform_tic(usi)
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
              [Input('usi2', 'value'), Input('image_export_format', 'value'), Input("plot_theme", "value")])
def draw_tic2(usi, export_format, plot_theme):
    tic_df = perform_tic(usi)
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
def perform_tic(usi):
    remote_link, local_filename = resolve_usi(usi)

    # Performing TIC Plot
    tic_trace = []
    rt_trace = []
    
    run = pymzml.run.Reader(local_filename, MS_precisions=MS_precisions)
    
    for n, spec in enumerate(run):
        if spec.ms_level == 1:
            rt_trace.append(spec.scan_time_in_minutes())
            tic_trace.append(sum(spec.i))

    tic_df = pd.DataFrame()
    tic_df["tic"] = tic_trace
    tic_df["rt"] = rt_trace

    return tic_df


@cache.memoize()
def perform_xic(usi, all_xic_values, xic_tolerance, rt_min, rt_max):
    # This is the business end of XIC extraction
    remote_link, local_filename = resolve_usi(usi)

    # Saving out MS2 locations
    all_ms2_ms1_int = []
    all_ms2_rt = []
    all_ms2_scan = []

    # Performing XIC Plot
    xic_trace = defaultdict(list)
    rt_trace = []
    
    #run = pymzml.run.Reader(local_filename, MS_precisions=MS_precisions)

    sum_i = 0 # Used by MS2 height
    for spec in _spectrum_generator(local_filename, rt_min, rt_max):
        if spec.ms_level == 1:
            try:
                for target_mz in all_xic_values:
                    lower_tolerance = target_mz[1] - xic_tolerance
                    upper_tolerance = target_mz[1] + xic_tolerance

                    # Filtering peaks by mz
                    peaks_full = spec.peaks("raw")
                    peaks = peaks_full[
                        np.where(np.logical_and(peaks_full[:, 0] >= lower_tolerance, peaks_full[:, 0] <= upper_tolerance))
                    ]

                    # summing intensity
                    sum_i = sum([peak[1] for peak in peaks])
                    xic_trace[target_mz[0]].append(sum_i)
            except:
                pass

            rt_trace.append(spec.scan_time_in_minutes())

        # Saving out the MS2 scans for the XIC
        elif spec.ms_level == 2:
            if len(all_xic_values) == 1:
                try:
                    lower_tolerance = target_mz[1] - xic_tolerance
                    upper_tolerance = target_mz[1] + xic_tolerance

                    ms2_mz = spec.selected_precursors[0]["mz"]
                    if ms2_mz < lower_tolerance or ms2_mz > upper_tolerance:
                        continue
                    all_ms2_ms1_int.append(sum_i)
                    all_ms2_rt.append(spec.scan_time_in_minutes())
                    all_ms2_scan.append(spec.ID)
                except:
                    pass

    # Formatting Data Frame
    xic_df = pd.DataFrame()
    for target_xic in xic_trace:
        target_name = "XIC {}".format(target_xic)
        print(target_name)
        xic_df[target_name] = xic_trace[target_xic]
    xic_df["rt"] = rt_trace

    ms2_data = {}
    ms2_data["all_ms2_ms1_int"] = all_ms2_ms1_int
    ms2_data["all_ms2_rt"] = all_ms2_rt
    ms2_data["all_ms2_scan"] = all_ms2_scan

    return xic_df, ms2_data


def _integrate_files(long_data_df):
    # Integrating Data
    # TODO: This is not the super best way to do this, but it gets you most of the way there
    grouped_df = long_data_df.groupby(["variable", "USI", "GROUP"]).sum().reset_index()
    grouped_df = grouped_df.drop("rt", axis=1)
    
    return grouped_df

# Creating XIC plot
@app.callback([Output('xic-plot', 'figure'), Output('xic-plot', 'config'), Output("integration-table", "children"), Output("integration-boxplot", "children")],
              [Input('usi', 'value'), 
              Input('usi2', 'value'), 
              Input('xic_mz', 'value'), 
              Input('xic_tolerance', 'value'), 
              Input('xic_rt_window', 'value'),
              Input('xic_norm', 'value'),
              Input('xic_file_grouping', 'value'),              
              Input('image_export_format', 'value'), 
              Input("plot_theme", "value")])
#@cache.memoize()
def draw_xic(usi, usi2, xic_mz, xic_tolerance, xic_rt_window, xic_norm, xic_file_grouping, export_format, plot_theme):
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
    usi_list = usi_list[:10]

    all_xic_values = []

    if xic_mz is None:
        return ["Please enter XIC"]
    else:
        for xic_value in xic_mz.split(";"):
            all_xic_values.append((str(xic_value), float(xic_value)))

    if xic_tolerance is None:
        return ["Please enter XIC Tolerance"]
    else:
        xic_tolerance = float(xic_tolerance)

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
        xic_df, ms2_data = perform_xic(usi_element, all_xic_values, xic_tolerance, rt_min, rt_max)

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
    
    if len(usi_list) == 1:
        if xic_file_grouping == "FILE":
            height = 400
            fig = px.line(merged_df_long, x="rt", y="value", color="variable", title='XIC Plot - Single File', height=height, template=plot_theme)
        else:
            height = 400 * len(all_xic_values)
            fig = px.line(merged_df_long, x="rt", y="value", facet_row="variable", title='XIC Plot - Single File', height=height, template=plot_theme)
    else:
        if xic_file_grouping == "FILE":
            height = 400 * len(usi_list)
            fig = px.line(merged_df_long, x="rt", y="value", color="variable", facet_row="USI", title='XIC Plot - Grouped Per File', height=height, template=plot_theme)
        elif xic_file_grouping == "MZ":
            height = 400 * len(all_xic_values)
            fig = px.line(merged_df_long, x="rt", y="value", color="USI", facet_row="variable", title='XIC Plot - Grouped Per M/Z', height=height, template=plot_theme)
        elif xic_file_grouping == "GROUP":
            height = 400 * len(all_xic_values)
            fig = px.line(merged_df_long, x="rt", y="value", color="GROUP", facet_row="variable", title='XIC Plot - By Group', height=height, template=plot_theme)

    # Plotting the MS2 on the XIC
    if len(usi_list) == 1:
        all_ms2_ms1_int = ms2_data["all_ms2_ms1_int"]
        all_ms2_rt = ms2_data["all_ms2_rt"]
        all_ms2_scan = ms2_data["all_ms2_scan"]

        if len(all_ms2_scan) > 0:
            scatter_fig = go.Scatter(x=all_ms2_rt, y=all_ms2_ms1_int, mode='markers', customdata=all_ms2_scan, marker=dict(color='red', size=8, symbol="x"), name="MS2 Acquisitions")
            fig.add_trace(scatter_fig)

    table_graph = dash.no_update
    box_graph = dash.no_update

    try:
        # Doing actual integration
        integral_df = _integrate_files(merged_df_long)

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

@app.callback([Output('map-plot', 'figure'), Output('download-link', 'children')],
              [Input('usi', 'value'), Input('map-plot', 'relayoutData'), Input('show_ms2_markers', 'value')])
def draw_file(usi, map_selection, show_ms2_markers):
    usi_list = usi.split("\n")

    remote_link, local_filename = resolve_usi(usi_list[0])

    if show_ms2_markers == 1:
        show_ms2_markers = True
    else:
        show_ms2_markers = False

    # Doing LCMS Map
    map_fig = create_map_fig(local_filename, map_selection=map_selection, show_ms2_markers=show_ms2_markers)

    return [map_fig, remote_link]


@app.callback([Output('map-plot2', 'figure')],
              [Input('usi2', 'value'), 
              Input('map-plot', 'relayoutData'), 
              Input('show_ms2_markers', 'value'),
              Input("show_lcms_2nd_map", "value")])
def draw_file2(usi, map_selection, show_ms2_markers, show_lcms_2nd_map):
    if show_lcms_2nd_map is False:
        return [dash.no_update]

    print("XZZZZZZZZZZZZZZZZZZ", usi)

    usi_list = usi.split("\n")

    remote_link, local_filename = resolve_usi(usi_list[0])

    if show_ms2_markers == 1:
        show_ms2_markers = True
    else:
        show_ms2_markers = False

    # Doing LCMS Map
    map_fig = create_map_fig(local_filename, map_selection=map_selection, show_ms2_markers=show_ms2_markers)

    return [map_fig]

@app.callback(Output('link-button', 'children'),
              [Input('usi', 'value'), 
              Input('usi2', 'value'), 
              Input('xic_mz', 'value'), 
              Input('xic_tolerance', 'value'), 
              Input('xic_rt_window', 'value'),
              Input("xic_norm", "value"),
              Input('xic_file_grouping', 'value'),
              Input("show_ms2_markers", "value"),
              Input("ms2_identifier", "value"),
              Input("show_lcms_2nd_map", "value")])
def create_link(usi, usi2, xic_mz, xic_tolerance, xic_rt_window, xic_norm, xic_file_grouping, show_ms2_markers, ms2_identifier, show_lcms_2nd_map):
    url_params = {}
    url_params["usi"] = usi
    url_params["usi2"] = usi2
    url_params["xicmz"] = xic_mz
    url_params["xic_tolerance"] = xic_tolerance
    url_params["xic_rt_window"] = xic_rt_window
    url_params["xic_norm"] = xic_norm
    url_params["xic_file_grouping"] = xic_file_grouping
    url_params["show_ms2_markers"] = show_ms2_markers
    url_params["ms2_identifier"] = ms2_identifier
    url_params["show_lcms_2nd_map"] = show_lcms_2nd_map

    url_provenance = dbc.Button("Link to these plots", block=True, color="primary", className="mr-1")
    provenance_link_object = dcc.Link(url_provenance, href="/?" + urllib.parse.urlencode(url_params) , target="_blank")

    return provenance_link_object

# Show Hide Panels
@app.callback(
    Output("second-data-exploration-dashboard-collapse", "is_open"),
    [Input("show_lcms_2nd_map", "value")],
    [State("second-data-exploration-dashboard-collapse", "is_open")],
)
def toggle_collapse(show_lcms_2nd_map, is_open):
    return show_lcms_2nd_map

if __name__ == "__main__":
    app.run_server(debug=True, port=5000, host="0.0.0.0")
