# Dash imports

import dash
from dash import dcc
import dash_bootstrap_components as dbc
from dash import html

ADVANCED_LIBRARYSEARCH_MODAL = [
    dbc.Modal(
        [
            dbc.ModalHeader("Library Search Modal"),
            dbc.ModalBody([
                html.Iframe(
                    id="librarysearch_frame",
                    style={
                        "width" : "100%",
                        "height" : "800px",
                        "border" : "0"
                    }
                )
            ]),
            dbc.ModalFooter(
                dbc.Button("Close", id="advanced_librarysearch_modal_close", className="ml-auto")
            ),
        ],
        id="advanced_librarysearch_modal",
        size="xl",
        style={
            "max-width": "1920px"
        }
    ),
]


ADVANCED_LIBRARYSEARCHMASSIVEKB_MODAL = [
    dbc.Modal(
        [
            dbc.ModalHeader("Library Search MassIVE-KB Modal"),
            dbc.ModalBody([
                html.Iframe(
                    id="librarysearchmassivekb_frame",
                    style={
                        "width" : "100%",
                        "height" : "800px",
                        "border" : "0"
                    }
                )
            ]),
            dbc.ModalFooter(
                dbc.Button("Close", id="advanced_librarysearchmassivekb_modal_close", className="ml-auto")
            ),
        ],
        id="advanced_librarysearchmassivekb_modal",
        size="xl",
        style={
            "max-width": "1920px"
        }
    ),
]