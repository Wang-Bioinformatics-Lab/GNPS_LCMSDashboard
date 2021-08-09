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


SYCHRONIZATION_MODAL = [
    dbc.Modal(
        [
            dbc.ModalHeader("Sychronization Options"),
            dbc.ModalBody([
                dbc.Row([
                        dbc.Col(
                            dbc.InputGroup(
                                [
                                    dbc.InputGroupAddon("Session ID", addon_type="prepend"),
                                    dbc.Input(id='sychronization_session_id', placeholder="Enter Session ID", value=""),
                                ],
                                className="mb-3",
                            ),
                        ),
                    ]
                ),
                dbc.Row([
                        dbc.Col(
                            dbc.Button("Save Session", block=True, id="sychronization_save_session_button"),
                        ),
                        dbc.Col(
                            dbc.Button("Load Session", block=True, id="sychronization_load_session_button"),
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
                        dbc.Button("Set Synchronization", block=True, id="sychronization_set_type_button"),
                    )
                ]),
                html.Hr(),
                dbc.InputGroup(
                    [
                        dbc.InputGroupAddon("Leader Session Token", addon_type="prepend"),
                        dbc.Input(id='synchronization_leader_token', placeholder="Enter Token", value=""),
                    ],
                    className="mb-3",
                ),
                dbc.Row([
                        dbc.Col(
                            dbc.Button("Get New Token", block=True, id="synchronization_leader_newtoken_button"),
                        ),
                        dbc.Col(
                            dbc.Button("Check Token", block=True, id="synchronization_leader_checktoken_button"),
                        ),
                    ]
                ),
                html.Br(),
                html.Div(id="sychronization_output1"),
                html.Div(id="sychronization_output2"),
                html.Br(),
                dbc.Row([
                    dbc.Col(
                        dbc.Button("Copy Follower URL", block=True, color="primary", className="mr-1", id="copy_follower_link_button")
                    ),
                    dbc.Col(
                        dbc.Button("Copy Leader URL", block=True, color="primary", className="mr-1", id="copy_leader_link_button")
                    ),
                    dbc.Col(
                        dbc.Button("Copy Collab URL", block=True, color="primary", className="mr-1", id="copy_collab_link_button")
                    ),
                ]),
                # Links to be generated
                html.Div(
                    [
                        dcc.Link(id="follower_query_link", href="#", target="_blank"),
                        dcc.Link(id="leader_query_link", href="#", target="_blank"),
                        dcc.Link(id="collab_query_link", href="#", target="_blank"),
                    ],
                    style="display:none"
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
