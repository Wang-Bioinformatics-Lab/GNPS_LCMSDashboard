
import os
import pymzml
import numpy as np
import datashader as ds
from tqdm import tqdm
import json
import pandas as pd
from utils import _spectrum_generator
from utils import _get_scan_polarity
import plotly.express as px
import plotly.graph_objects as go 
import xarray
import time

import utils

def _gather_lcms_data(filename, min_rt, max_rt, min_mz, max_mz, polarity_filter="None"):
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
            rt = spec.scan_time_in_minutes()
            # Still waiting for the window
            if rt < min_rt:
                continue
            
            # We've passed the window
            if rt > max_rt:            
                break
        except:
            pass

        if polarity_filter == "None":
            pass
        else:
            scan_polarity = _get_scan_polarity(spec)
            if polarity_filter != scan_polarity:
                continue
        
        if spec.ms_level == 1:
            spectrum_index += 1
            number_spectra += 1

            try:
                # Filtering peaks by mz
                if min_mz <= 0 and max_mz >= 2000:
                    peaks = spec.peaks("raw")
                else:
                    peaks = spec.reduce(mz_range=(min_mz, max_mz))

                # Filtering out zero rows
                peaks = peaks[~np.any(peaks < 1.0, axis=1)]

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

def _aggregate_lcms_map(filename, min_rt, max_rt, min_mz, max_mz, polarity_filter="None", map_plot_quantization_level="Medium"):
    import time
    start_time = time.time()
    ms1_results, ms2_results, ms3_results = _gather_lcms_data(filename, min_rt, max_rt, min_mz, max_mz, polarity_filter=polarity_filter)
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

    min_size = min(number_spectra, int(max_mz - min_mz) * 4)
    width = max(min(min_size*4, 750), 120)
    height = max(min(int(min_size*1.75), 500), 80)

    if map_plot_quantization_level == "Low":
        width = int(width / 2)
        height = int(height / 2)
    elif map_plot_quantization_level == "High":
        width = int(width * 2)
        height = int(height * 2)

    print("Datashader Len", len(df))

    cvs = ds.Canvas(plot_width=width, plot_height=height)
    agg = cvs.points(df,'rt','mz', agg=ds.sum("i"))

    end_time = time.time()
    print("Datashader Agg", end_time - start_time)

    zero_mask = agg.values == 0
    agg.values = np.log10(agg.values, where=np.logical_not(zero_mask))
    agg_dict = agg.to_dict()

    return agg_dict, all_ms2_mz, all_ms2_rt, all_ms2_scan, all_ms3_mz, all_ms3_rt, all_ms3_scan


# Creates the figure for map plot
# overlay_data is a dataframe that includes the overlay, rt and mz are the expected columns
def _create_map_fig(agg_dict, all_ms2_mz, all_ms2_rt, all_ms2_scan, all_ms3_mz, all_ms3_rt, all_ms3_scan, map_selection=None, show_ms2_markers=True, polarity_filter="None", highlight_box=None, color_scale="Hot_r"):
    min_rt, max_rt, min_mz, max_mz = utils._determine_rendering_bounds(map_selection)

    agg = xarray.DataArray.from_dict(agg_dict)

    # Creating the figures
    fig = px.imshow(agg, origin='lower', labels={'color':'Log10(abundance)'}, color_continuous_scale=color_scale, height=600, template="plotly_white")
    fig.update_traces(hoverongaps=False)
    fig.update_layout(coloraxis_colorbar=dict(title='Abundance', tickprefix='1.e'))

    fig.update_yaxes(showline=True, linewidth=1, linecolor='black', gridwidth=3, range=[min_mz, max_mz])
    fig.update_xaxes(showline=True, linewidth=1, linecolor='black', showgrid=False)
    if max_rt < 100000:
        fig.update_xaxes(range=[min_rt, max_rt])
        
    too_many_ms2 = False
    MAX_MS2 = 1000000
    if len(all_ms2_scan) > MAX_MS2 or len(all_ms3_scan) > MAX_MS2:
        too_many_ms2 = True

    if show_ms2_markers is True and too_many_ms2 is False:
        scatter_fig = go.Scattergl(x=all_ms2_rt, y=all_ms2_mz, mode='markers', customdata=all_ms2_scan, marker=dict(color='blue', size=5, symbol="x"), name="MS2s")
        fig.add_trace(scatter_fig)

        if len(all_ms3_scan) > 0:
            scatter_ms3_fig = go.Scatter(x=all_ms3_rt, y=all_ms3_mz, mode='markers', customdata=all_ms3_scan, marker=dict(color='green', size=5, symbol="x"), name="MS3s")
            fig.add_trace(scatter_ms3_fig)

    if highlight_box is not None:
        print("ADDING HIGHLIGHT BOX")
        fig.add_shape(type="rect",
            x0=highlight_box["left"], y0=highlight_box["top"], x1=highlight_box["right"], y1=highlight_box["bottom"],
            line=dict(
                color="RoyalBlue",
                width=2,
            ),
        )

    # Adding final bounding box to where we zoomed to
    if max_rt < 100000:
        fig.add_shape(type="rect",
            x0=min_rt, y0=min_mz, x1=max_rt, y1=max_mz,
            line=dict(
                color="Green",
                width=0.1,
            ),
        )


    return fig