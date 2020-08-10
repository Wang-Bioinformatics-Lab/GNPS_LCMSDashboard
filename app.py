# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_table
import plotly.express as px
import plotly.graph_objects as go 
from dash.dependencies import Input, Output
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

from collections import defaultdict

server = Flask(__name__)
app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

df = pd.DataFrame()
df["rt"] = [1]
df["mz"] = [1]
df["i"] = [1]
cvs = ds.Canvas(plot_width=1, plot_height=1)
agg = cvs.points(df,'rt','mz', agg=ds.sum("i"))
zero_mask = agg.values == 0
agg.values = np.log10(agg.values, where=np.logical_not(zero_mask))
fig1 = px.imshow(agg, origin='lower', labels={'color':'Log10(Abundance)'}, color_continuous_scale="Hot")

NAVBAR = dbc.Navbar(
    children=[
        dbc.NavbarBrand(
            html.Img(src="https://gnps-cytoscape.ucsd.edu/static/img/GNPS_logo.png", width="120px"),
            href="https://gnps.ucsd.edu"
        ),
        dbc.Nav(
            [
                dbc.NavItem(dbc.NavLink("GNPS LCMS Dashboard", href="#")),
            ],
        navbar=True)
    ],
    color="light",
    dark=False,
    sticky="top",
)

DATASELECTION_CARD = [
    dbc.CardHeader(html.H5("Data Selection")),
    dbc.CardBody(
        [   
            html.Br(),
            html.H3(children='GNPS USI'),
            dbc.Input(className="mb-3", id='usi', placeholder="Enter GNPS File USI"),
            html.H3(children='XIC m/z'),
            dbc.Input(className="mb-3", id='xic_mz', placeholder="Enter m/z to XIC"),
            html.H3(children='XIC Da Tolerance'),
            dbc.Input(className="mb-3", id='xic_tolerance', placeholder="Enter Da Tolerance", value="0.5"),
            html.H3(children='Show MS2 Markers'),
            dbc.Select(
                id="show_ms2_markers",
                options=[
                    {"label": "Yes", "value": "1"},
                    {"label": "No", "value": "0"},
                ],
                value="0"
            )
        ]
    )
]

DATASLICE_CARD = [
    dbc.CardHeader(html.H5("Details Panel")),
    dbc.CardBody(
        [   
            html.Br(),
            dcc.Loading(
                id="ms2-plot",
                children=[html.Div([html.Div(id="loading-output-6")])],
                type="default",
            ),
            dcc.Loading(
                id="xic-plot",
                children=[html.Div([html.Div(id="loading-output-5")])],
                type="default",
            )
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
        ]
    )
]

LEFT_DASHBOARD = [
    html.Div(
        [
            html.Div(DATASELECTION_CARD),
            html.Div(DATASLICE_CARD),
            html.Div(DEBUG_CARD),
        ]
    )
]

MIDDLE_DASHBOARD = [
    dbc.CardHeader(html.H5("Data Exploration")),
    dbc.CardBody(
        [
            html.Br(),
            dcc.Loading(
                id="tic-plot",
                children=[html.Div([html.Div(id="loading-output-4")])],
                type="default",
            ),
            html.Br(),
            dcc.Graph(
                id='map-plot',
                figure=fig1,
                config={
                    'doubleClick': 'reset'
                }
            ),
        ]
    )
]

BODY = dbc.Container(
    [
        dcc.Location(id='url', refresh=False),
        html.Div(id='version', children="Version - 1.0"),
        dbc.Row([
            dbc.Col(
                dbc.Card(LEFT_DASHBOARD),
                className="w-50"
            ),
            dbc.Col(
                dbc.Card(MIDDLE_DASHBOARD),
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

    if "MSV" in usi_splits[1]:
        # Test: mzspec:MSV000084494:GNPS00002_A3_p:scan:1
        # Bigger Test: mzspec:MSV000083388:1_p_153001_01072015:scan:12
        lookup_url = f'https://massive.ucsd.edu/ProteoSAFe/QuerySpectrum?id={usi}'
        lookup_request = requests.get(lookup_url)

        resolution_json = lookup_request.json()

        mzML_filepath = None
        # Figuring out which file is mzML
        for resolution in resolution_json["row_data"]:
            filename = resolution["file_descriptor"]
            extension = os.path.splitext(filename)[1]

            if extension == ".mzML":
                mzML_filepath = filename
                break

        # Format into FTP link
        remote_link = f"ftp://massive.ucsd.edu/{mzML_filepath[2:]}"
    elif "GNPS" in usi_splits[1]:
        # Test: mzspec:GNPS:TASK-de188599f53c43c3aaad95491743c784-spec/spec-00000.mzML:scan:31
        filename = "-".join(usi_splits[2].split("-")[2:])
        task = usi_splits[2].split("-")[1]

        remote_link = "http://gnps.ucsd.edu/ProteoSAFe/DownloadResultFile?task={}&block=main&file={}".format(task, filename)


    # Getting Data Local, TODO: likely should serialize it
    local_filename = os.path.join("temp", werkzeug.utils.secure_filename(remote_link))
    if not os.path.isfile(local_filename):
        wget_cmd = "wget '{}' -O {}".format(remote_link, local_filename)
        os.system(wget_cmd)

    return remote_link, local_filename



@app.callback([Output('debug-output', 'children'), Output('ms2-plot', 'children')],
              [Input('usi', 'value'), Input('map-plot', 'clickData')])
def click_plot(usi, clickData):
    clicked_target = clickData["points"][0]

    # This is an MS2
    if clicked_target["curveNumber"] == 1:
        updated_usi = ":".join(usi.split(":")[:-1]) + ":" + str(clicked_target["customdata"])
        usi_png_url = "https://metabolomics-usi.ucsd.edu/png/?usi={}".format(updated_usi)
        usi_url = "https://metabolomics-usi.ucsd.edu/spectrum/?usi={}".format(updated_usi)

        return [str(clickData), html.A(html.Img(src=usi_png_url), href=usi_url, target="_blank")]

    # This is an MS1
    if clicked_target["curveNumber"] == 0:
        rt_target = clicked_target["x"]

        remote_link, local_filename = resolve_usi(usi)

        # Understand parameters
        min_rt_delta = 1000
        closest_scan = 0
        run = pymzml.run.Reader(local_filename)
        for spec in tqdm(run):
            if spec.ms_level == 1:
                try:
                    delta = abs(spec.scan_time_in_minutes() - rt_target)
                    if delta < min_rt_delta:
                        closest_scan = spec.ID
                        min_rt_delta = delta
                except:
                    pass

        updated_usi = ":".join(usi.split(":")[:-1]) + ":" + str(closest_scan)
        usi_png_url = "https://metabolomics-usi.ucsd.edu/png/?usi={}".format(updated_usi)
        usi_url = "https://metabolomics-usi.ucsd.edu/spectrum/?usi={}".format(updated_usi)
        
        return [str(clickData), html.A(html.Img(src=usi_png_url), href=usi_url, target="_blank")]
    
@app.callback(Output('usi', 'value'),
              [Input('url', 'search')])
def determine_task(search):
    try:
        return str(urllib.parse.parse_qs(search[1:])["usi"][0])
    except:
        return "mzspec:MSV000084494:GNPS00002_A3_p:scan:1" 

# Calculating which xic value to use
@app.callback(Output('xic_mz', 'value'),
              [Input('url', 'search'), Input('map-plot', 'clickData')])
def determine_xic_target(search, clickData):
    try:
        clicked_target = clickData["points"][0]

        # This is MS1
        if clicked_target["curveNumber"] == 0:
            mz_target = clicked_target["y"]

            return str(mz_target)
    except:
        pass
    
    try:
        return str(urllib.parse.parse_qs(search[1:])["xicmz"][0])
    except:
        pass
    
    return ""

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

    # Understand parameters
    run = pymzml.run.Reader(filename)
    for spec in tqdm(run):
        try:
            # Still waiting for the window
            if spec.scan_time_in_minutes() < min_rt:
                continue
            
            # We've passed the window
            if spec.scan_time_in_minutes() > max_rt:
                print("BREAKING")
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
            
            
    df = pd.DataFrame()
    df["mz"] = all_mz
    df["i"] = all_i
    df["rt"] = all_rt
    df["scan"] = all_scan
    df["index"] = all_index

    min_size = min(number_spectra, int(max_mz - min_mz))
    width = min(min_size*4, 500)
    height = min(int(min_size*1.75), 500)

    cvs = ds.Canvas(plot_width=width, plot_height=height)
    agg = cvs.points(df,'rt','mz', agg=ds.sum("i"))
    zero_mask = agg.values == 0
    agg.values = np.log10(agg.values, where=np.logical_not(zero_mask))
    fig = px.imshow(agg, origin='lower', labels={'color':'Log10(abundance)'}, color_continuous_scale="Hot_r", width=1000, height=600)
    fig.update_traces(hoverongaps=False)
    fig.update_layout(coloraxis_colorbar=dict(title='Abundance', tickprefix='1.e'), plot_bgcolor="white")

    fig.update_xaxes(showline=True, linewidth=1, linecolor='black')
    fig.update_yaxes(showline=True, linewidth=1, linecolor='black')

    too_many_ms2 = False
    if len(all_ms2_scan) > 5000:
        too_many_ms2 = True

    if show_ms2_markers is True and too_many_ms2 is False:
        scatter_fig = go.Scatter(x=all_ms2_rt, y=all_ms2_mz, mode='markers', customdata=all_ms2_scan, marker=dict(color='blue', size=5, symbol="x"))
        fig.add_trace(scatter_fig)

    return fig

# Creating TIC plot
@app.callback([Output('tic-plot', 'children')],
              [Input('usi', 'value')])
def draw_tic(usi):
    remote_link, local_filename = resolve_usi(usi)

    # Performing TIC Plot
    tic_trace = []
    rt_trace = []
    run = pymzml.run.Reader(local_filename)
    for n, spec in enumerate(run):
        if spec.ms_level == 1:
            rt_trace.append(spec.scan_time_in_minutes())
            tic_trace.append(sum(spec.i))

    tic_df = pd.DataFrame()
    tic_df["tic"] = tic_trace
    tic_df["rt"] = rt_trace
    fig = px.line(tic_df, x="rt", y="tic", title='TIC Plot')

    return [dcc.Graph(figure=fig)]

# Creating XIC plot
@app.callback([Output('xic-plot', 'children')],
              [Input('usi', 'value'), Input('xic_mz', 'value'), Input('xic_tolerance', 'value'), ])
def draw_xic(usi, xic_mz, xic_tolerance):
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

    remote_link, local_filename = resolve_usi(usi)

    # Performing TIC Plot
    tic_trace = defaultdict(list)
    rt_trace = []
    run = pymzml.run.Reader(local_filename)
    for n, spec in enumerate(run):
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
                    tic_trace[target_mz[0]].append(sum_i)
            except:
                pass

            rt_trace.append(spec.scan_time_in_minutes())
    
    tic_df = pd.DataFrame()
    all_line_names = []
    for target_xic in tic_trace:
        target_name = "XIC {}".format(target_xic)
        tic_df[target_name] = tic_trace[target_xic]

        all_line_names.append(target_name)
    tic_df["rt"] = rt_trace

    df_long = pd.melt(tic_df, id_vars="rt", value_vars=all_line_names)
    fig = px.line(df_long, x="rt", y="value", color="variable", title='XIC Plot - {}'.format(":".join(all_line_names)))

    return [dcc.Graph(figure=fig)]



# Inspiration for structure from
# https://github.com/plotly/dash-datashader
# https://community.plotly.com/t/heatmap-is-slow-for-large-data-arrays/21007/2

@app.callback([Output('map-plot', 'figure'), Output('download-link', 'children')],
              [Input('usi', 'value'), Input('map-plot', 'relayoutData'), Input('show_ms2_markers', 'value')])
def draw_file(usi, map_selection, show_ms2_markers):
    remote_link, local_filename = resolve_usi(usi)

    if show_ms2_markers == "1":
        show_ms2_markers = True
    else:
        show_ms2_markers = False

    # Doing LCMS Map
    map_fig = create_map_fig(local_filename, map_selection=map_selection, show_ms2_markers=show_ms2_markers)

    return [map_fig, remote_link]
        

if __name__ == "__main__":
    app.run_server(debug=True, port=5000, host="0.0.0.0")
