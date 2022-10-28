# Dash imports

import dash
from dash import dcc
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
                                    dbc.InputGroupText("XIC Peptide"),
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
                                {'label': 'QC-6mix', 'value': 'Sulfamethazine=279.0910;Sulfamethizole=271.0317935;Sulfachloropyridazine=285.0207505;Sulfadimethoxine=311.0808522;Amitryptiline=278.1903263;Coumarin-314=314.1386846'},
                                {'label': 'Berkeley Lab - iSTD Positive', 'value': 'lysine (unlabeled)=147.1128;lysine (U - 13C, 15N)=155.127;arginine (unlabeled)=175.11895;arginine (U - 13C, 15N)=185.12722;cystine (unlabeled)=241.03112;cystine (U - 13C, 15N)=249.04532;aspartic acid (unlabeled)=134.04478;aspartic acid (U - 13C, 15N)=139.05523;glutamic acid (unlabeled)=148.06043;glutamic acid (U - 13C, 15N)=154.07424;histidine (unlabeled)=156.07675;histidine (U - 13C, 15N)=165.08798;trehalose (unlabeled)=343.12348;trehalose (U - 13C)=355.16374;asparagine (unlabeled)=133.06076;asparagine (U - 13C, 15N)=139.06825;glutamine (unlabeled)=147.07641;glutamine (U - 13C, 15N)=154.08726;serine (unlabeled)=106.04986;serine (U - 13C, 15N)=110.05696;glycine (unlabeled)=76.0393;glycine (U - 13C, 15N)=79.04304;threonine (unlabeled)=120.06551;threonine (U - 13C, 15N)=125.07597;alanine (unlabeled)=90.05495;alanine (U - 13C, 15N)=94.06205;tyrosine (unlabeled)=182.08116;tyrosine (U - 13C, 15N)=192.10839;valine (unlabeled)=118.08625;valine (U - 13C, 15N)=124.10006;proline (unlabeled)=116.0706;proline (U - 13C, 15N)=122.08441;methionine (unlabeled)=150.05832;methionine (U - 13C, 15N)=156.07213;tryptophan (unlabeled)=205.09715;tryptophan (U - 13C, 15N)=218.12812;isoleucine (unlabeled)=132.1019;isoleucine (U - 13C, 15N)=139.11906;mannitol (unlabeled)=181.07066;mannitol (U - 13C)=189.10644;leucine (unlabeled)=132.1019;leucine (U - 13C, 15N)=139.11906;phenylalanine (unlabeled)=166.08625;phenylalanine (U - 13C, 15N)=176.11348;guanine (unlabeled)=152.05668;guanine (U - 15N)=157.04186;inosine (unlabeled)=269.08804;inosine (U - 15N)=273.07618;cytosine (unlabeled)=112.05053;cytosine (13C2, 15N3)=117.04835;ABMBA (Br-nat)=229.98111;hypoxanthine (unlabeled)=137.04578;hypoxanthine (U - 15N)=141.03392;adenine (unlabeled)=136.06177;adenine (U - 15N)=141.04694;uracil (unlabeled)=113.03455;uracil (U - 13C, 15N)=119.04204;thymine (unlabeled)=127.0502'},
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