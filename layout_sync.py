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


SYCHRONIZATION_MODAL = [
    dbc.Modal(
        [
            dbc.ModalHeader("Sychronization Options"),
            dbc.ModalBody([
                dbc.Row([
                        dbc.Col(
                            dbc.InputGroup(
                                [
                                    dbc.InputGroupText("Session ID"),
                                    dbc.Input(id='sychronization_session_id', placeholder="Enter Session ID", value=""),
                                ],
                                className="mb-3",
                            ),
                        ),
                    ]
                ),
                dbc.Row([
                        dbc.Col(
                            html.Div([dbc.Button("Save Session", color="secondary", id="sychronization_save_session_button")], className="d-grid gap-2"),
                        ),
                        dbc.Col(
                            html.Div([dbc.Button("Load Session", color="secondary", id="sychronization_load_session_button")], className="d-grid gap-2"),
                        ),
                    ]
                ),
                html.Hr(),
                html.H5("Dashboard Sychronization Type"),
                dbc.Row([
                    dbc.Col(
                        dcc.Dropdown(
                            id='synchronization_type',
                            options=[
                                {'label': 'MANUAL (Default)', 'value': 'MANUAL'},
                                {'label': 'COLLAB (Bidirectional sync)', 'value': 'COLLAB'},
                                {'label': 'LEADER', 'value': 'LEADER'},
                                {'label': 'FOLLOWER', 'value': 'FOLLOWER'},
                            ],
                            searchable=False,
                            clearable=False,
                            value="MANUAL",
                            style={
                                "width":"100%"
                            }
                        ),
                    ),
                    dbc.Col(
                        html.Div([dbc.Button("Set Synchronization", id="sychronization_set_type_button")], className="d-grid gap-2"),
                    )
                ]),
                html.Hr(),
                dbc.InputGroup(
                    [
                        dbc.InputGroupText("Leader Session Token"),
                        dbc.Input(id='synchronization_leader_token', placeholder="Enter Token", value=""),
                    ],
                    className="mb-3",
                ),
                dbc.Row([
                        dbc.Col(
                            html.Div([dbc.Button("Get New Token", color="secondary", id="synchronization_leader_newtoken_button")], className="d-grid gap-2"),
                        ),
                        dbc.Col(
                            html.Div([dbc.Button("Check Token", color="secondary", id="synchronization_leader_checktoken_button")], className="d-grid gap-2"),
                        ),
                    ]
                ),
                html.Br(),
                html.Div(id="sychronization_output1"),
                html.Div(id="sychronization_output2"),
                html.Br(),
                dbc.Row([
                    dbc.Col(
                        html.Div([dbc.Button("Copy Follower URL", color="primary", id="copy_follower_link_button")], className="d-grid gap-2"),
                    ),
                    dbc.Col(
                        html.Div([dbc.Button("Copy Leader URL", color="primary", id="copy_leader_link_button")], className="d-grid gap-2"),
                    ),
                    dbc.Col(
                        html.Div([dbc.Button("Copy Collab URL", color="primary", id="copy_collab_link_button")], className="d-grid gap-2"),
                    ),
                ]),
                # Links to be generated
                html.Div(
                    [
                        dcc.Link(id="follower_query_link", href="#", target="_blank"),
                        dcc.Link(id="leader_query_link", href="#", target="_blank"),
                        dcc.Link(id="collab_query_link", href="#", target="_blank"),
                    ],
                    style={
                        "display":"none"
                    }
                ),
                dbc.Row([
                    dbc.Col(id="follower_qr_code"),
                    dbc.Col()
                    
                ])
            ]),
            dbc.ModalFooter(
                dbc.Button("Close", id="sychronization_options_modal_close", className="ml-auto")
            ),
        ],
        id="sychronization_options_modal",
        size="xl",
    )
]
