# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_table
import plotly.express as px
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


server = Flask(__name__)
app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

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

DASHBOARD = [
    dbc.CardHeader(html.H5("GNPS LCMS Dashboard")),
    dbc.CardBody(
        [   
            dcc.Location(id='url', refresh=False),

            html.Div(id='version', children="Version - 1.0"),

            html.Br(),
            html.H3(children='GNPS USI'),
            dbc.Input(className="mb-3", id='usi', placeholder="Enter GNPS File USI"),
            html.Br(),
            dcc.Loading(
                id="tic-plot",
                children=[html.Div([html.Div(id="loading-output-4")])],
                type="default",
            ),
            html.Br(),
            dcc.Loading(
                id="map-plot",
                children=[html.Div([html.Div(id="loading-output-5")])],
                type="default",
            )
        ]
    )
]

BODY = dbc.Container(
    [
        dbc.Row([dbc.Col(dbc.Card(DASHBOARD)),], style={"marginTop": 30}),
    ],
    className="mt-12",
)

app.layout = html.Div(children=[NAVBAR, BODY])


@app.callback(Output('usi', 'value'),
              [Input('url', 'pathname')])
def determine_task(pathname):
    # Otherwise, lets use the url
    if pathname is not None and len(pathname) > 1:
        return pathname[1:]
    else:
        return dash.no_update

# This will create a graph object
def create_map_fig(filepath):
    N = 1000
    M = 500
    xx = np.arange(N, dtype=np.float64)
    yy = np.arange(M, dtype=np.float64)
    x, y = np.meshgrid(xx, yy)
    b = N/20.0
    c = M/2.0
    r = np.sqrt(((x-c)/b)**2 + ((y-c)/b)**2)
    a = np.sin(r)

    # Limits
    xmin = xx[0]
    xmax = xx[-1]
    ymin = yy[0]
    ymax = yy[-1]
    amin = np.amin(a)
    amax = np.amax(a)

    from PIL import Image
    from matplotlib import cm
    from matplotlib.colors import Normalize

    # Some normalization from matplotlib
    cNorm = Normalize(vmin=amin, vmax=amax)
    scalarMap  = cm.ScalarMappable(norm=cNorm, cmap='viridis' )
    seg_colors = scalarMap.to_rgba(a) 
    img = Image.fromarray(np.uint8(seg_colors*255))

    # Now the plotly code
    import plotly.graph_objects as go

    # Create figure
    fig = go.Figure()

    # Constants
    img_width = 1000
    img_height = 600

    # Add invisible scatter trace.
    # This trace is added to help the autoresize logic work.
    # We also add a color to the scatter points so we can have a colorbar next to our image
    fig.add_trace(
        go.Scatter(
            x=[xmin, xmax],
            y=[ymin, ymax],
            mode="markers",
            marker={"color":[np.amin(a), np.amax(a)],
                    "colorscale":'Viridis',
                    "showscale":True,
                    "colorbar":{"title":"Counts",
                                "titleside": "right"},
                    "opacity": 0
                }
        )
    )

    # Add image
    fig.update_layout(
        images=[go.layout.Image(
            x=xmin,
            sizex=xmax-xmin,
            y=ymax,
            sizey=ymax-ymin,
            xref="x",
            yref="y",
            opacity=1.0,
            layer="below",
            sizing="stretch",
            source=img)]
    )

    # Configure other layout
    fig.update_layout(
            xaxis=dict(showgrid=False, zeroline=False, range=[xmin, xmax]),
            yaxis=dict(showgrid=False, zeroline=False, range=[ymin, ymax]),
        width=img_width,
        height=img_height,
    )

    return fig

@app.callback([Output('tic-plot', 'children'), Output('map-plot', 'children')],
              [Input('usi', 'value')])
def draw_file(usi):
    usi_splits = usi.split(":")

    if "MSV" in usi_splits[1]:
        # Test: mzspec:MSV000084494:GNPS00002_A3_p:scan:1
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
        ftp_link = f"ftp://massive.ucsd.edu/{mzML_filepath[2:]}"

        # Getting Data Local, TODO: likely should serialize it
        local_filename = os.path.join("temp", werkzeug.utils.secure_filename(ftp_link))
        wget_cmd = "wget {} -O {}".format(ftp_link, local_filename)

        os.system(wget_cmd)

        # Performing TIC Plot
        tic_trace = []
        rt_trace = []
        run = pymzml.run.Reader(local_filename)
        for n, spec in enumerate(run):
            if spec.ms_level == 1:
                rt_trace.append(spec.scan_time_in_minutes() * 60)
                tic_trace.append(sum(spec.i))

        tic_df = pd.DataFrame()
        tic_df["tic"] = tic_trace
        tic_df["rt"] = rt_trace
        fig = px.line(tic_df, x="rt", y="tic", title='TIC Plot')

        # Doing LCMS Map
        # Using this as starting code: https://community.plotly.com/t/heatmap-is-slow-for-large-data-arrays/21007/2
        map_fig = create_map_fig(local_filename)


        return [dcc.Graph(figure=fig), dcc.Graph(figure=map_fig)]
    if "GNPS" in usi_splits[1]:
        
        # Test: mzspec:GNPS:TASK-ea65c1b165054c3492974b8e4f0bf675-f.mwang87/data/Yao_Streptomyces/roseosporus/0518_s_BuOH.mzXML:scan:171
        filename = usi_splits[2].split("-")[2]
        task = usi_splits[2].split("-")[1]

        return "GNPS"
    

    return "X"


if __name__ == "__main__":
    app.run_server(debug=True, port=5000, host="0.0.0.0")
