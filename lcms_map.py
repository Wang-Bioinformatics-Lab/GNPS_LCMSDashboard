
import os
import pymzml
import numpy as np
import datashader as ds
from tqdm import tqdm
import json
import pandas as pd
import xarray
import time
import utils

import plotly.express as px
import plotly.graph_objects as go 

from utils import _spectrum_generator
from utils import _get_scan_polarity

# Enum for polarity
POLARITY_POS = 1
POLARITY_NEG = 2

def _gather_lcms_data(filename, min_rt, max_rt, min_mz, max_mz, polarity_filter="None", top_spectrum_peaks=100, include_polarity=False):
    all_mz = []
    all_rt = []
    all_polarity = []
    all_i = []
    all_scan = []
    all_index = []
    spectrum_index = 0
    number_spectra = 0

    all_msn_mz = []
    all_msn_rt = []
    all_msn_polarity = []
    all_msn_scan = []
    all_msn_level = []

    # Iterating through all data with a custom scan iterator
    # It handles custom bounds on RT
    for spec in _spectrum_generator(filename, min_rt, max_rt):
        rt = spec.scan_time_in_minutes()
        try:
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
                peaks = peaks[-1 * top_spectrum_peaks:]

                mz, intensity = zip(*peaks)

                all_mz += list(mz)
                all_i += list(intensity)
                all_rt += len(mz) * [rt]
                all_scan += len(mz) * [spec.ID]
                all_index += len(mz) * [number_spectra]

                # Adding polarity
                if include_polarity is True:
                    scan_polarity = _get_scan_polarity(spec)
                    if scan_polarity == "Positive":
                        all_polarity += len(mz) * [POLARITY_POS]
                    else:
                        all_polarity += len(mz) * [POLARITY_NEG]
            except:
                pass
        elif spec.ms_level > 1:
            try:
                msn_mz = spec.selected_precursors[0]["mz"]
                if msn_mz < min_mz or msn_mz > max_mz:
                    continue
                all_msn_mz.append(msn_mz)
                all_msn_rt.append(rt)
                all_msn_scan.append(spec.ID)
                all_msn_level.append(spec.ms_level)

                # Adding polarity
                if include_polarity is True:
                    scan_polarity = _get_scan_polarity(spec)
                    if scan_polarity == "Positive":
                        all_msn_polarity.append(POLARITY_POS)
                    else:
                        all_msn_polarity.append(POLARITY_NEG)
            except:
                pass
        
    ms1_results = {}
    ms1_results["mz"] = all_mz
    ms1_results["rt"] = all_rt
    ms1_results["i"] = all_i
    ms1_results["scan"] = all_scan
    ms1_results["index"] = all_index

    msn_results = {}
    msn_results["precursor_mz"] = all_msn_mz
    msn_results["rt"] = all_msn_rt
    msn_results["scan"] = all_msn_scan
    msn_results["level"] = all_msn_level

    # Adding polarity
    if include_polarity is True:
        ms1_results["polarity"] = all_polarity
        msn_results["polarity"] = all_msn_polarity

    ms1_results = pd.DataFrame(ms1_results)
    msn_results = pd.DataFrame(msn_results)

    return ms1_results, number_spectra, msn_results

def _get_feather_filenames(filename):
    output_ms1_filename = filename + ".ms1.feather"
    output_msn_filename = filename + ".msn.feather"

    return output_ms1_filename, output_msn_filename

# These are caching layers for fast loading
def _save_lcms_data_feather(filename):
    output_ms1_filename, output_msn_filename = _get_feather_filenames(filename)
    
    ms1_results, number_spectra, msn_results = _gather_lcms_data(filename, 0, 1000000, 0, 10000, polarity_filter="None", top_spectrum_peaks=100000, include_polarity=True)
    ms1_results = ms1_results.sort_values(by='i', ascending=False).reset_index()

    ms1_results.to_feather(output_ms1_filename)
    msn_results.to_feather(output_msn_filename)

def _gather_lcms_data_cached(filename, min_rt, max_rt, min_mz, max_mz, polarity_filter="None"):
    ms1_filename, msn_filename = _get_feather_filenames(filename)

    delta_rt = max_rt - min_rt

    # We don't see the feather files, so lets just do the classic thing
    if not os.path.exists(ms1_filename) or delta_rt < 1:
        print("FEATHER NOT PRESENT")
        return _gather_lcms_data(filename, min_rt, max_rt, min_mz, max_mz, polarity_filter=polarity_filter)
    else:
        print("FEATHER PRESENT")

    # Reading and filtering data
    ms1_results = pd.read_feather(ms1_filename)
    ms1_results = ms1_results[(ms1_results["rt"] > min_rt) & (ms1_results["rt"] < max_rt) & (ms1_results["mz"] > min_mz) & (ms1_results["mz"] < max_mz)]
    if polarity_filter == "Positive":
        ms1_results = ms1_results[ms1_results["polarity"] == POLARITY_POS]
    elif polarity_filter == "Negative":
        ms1_results = ms1_results[ms1_results["polarity"] == POLARITY_NEG] 
    ms1_results = ms1_results.groupby('scan').head(100).reset_index(drop=True) # Getting the top 100 peaks per scan

    msn_results = pd.read_feather(msn_filename)
    msn_results = msn_results[(msn_results["rt"] > min_rt) & (msn_results["rt"] < max_rt) & (msn_results["precursor_mz"] > min_mz) & (msn_results["precursor_mz"] < max_mz)]
    if polarity_filter == "Positive":
        msn_results = msn_results[msn_results["polarity"] == POLARITY_POS]
    elif polarity_filter == "Negative":
        msn_results = msn_results[msn_results["polarity"] == POLARITY_NEG] 

    number_spectra = len(set(ms1_results["scan"]))

    return ms1_results, number_spectra, msn_results

def _aggregate_lcms_map(filename, min_rt, max_rt, min_mz, max_mz, polarity_filter="None", map_plot_quantization_level="Medium"):
    import time
    start_time = time.time()
    ms1_results, number_spectra, msn_results = _gather_lcms_data_cached(filename, min_rt, max_rt, min_mz, max_mz, polarity_filter=polarity_filter)
    end_time = time.time()
    print("READ FILE", end_time - start_time)

    start_time = time.time()

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

    print("Datashader Len", len(ms1_results))

    cvs = ds.Canvas(plot_width=width, plot_height=height)
    agg = cvs.points(ms1_results,'rt','mz', agg=ds.sum("i"))

    print("Datashader Agg", time.time() - start_time)
    start_time = time.time()

    zero_mask = agg.values == 0
    agg.values = np.log10(agg.values, where=np.logical_not(zero_mask))
    agg_dict = agg.to_dict()

    print("Datashader Post Processing", time.time() - start_time)

    return agg_dict, msn_results


# Creates the figure for map plot
# overlay_data is a dataframe that includes the overlay, rt and mz are the expected columns
def _create_map_fig(agg_dict, msn_results, map_selection=None, show_ms2_markers=True, polarity_filter="None", highlight_box=None, color_scale="Hot_r", template="plotly_white", ms2marker_color="blue", ms2marker_size=5):
    min_rt, max_rt, min_mz, max_mz = utils._determine_rendering_bounds(map_selection)
    
    agg = xarray.DataArray.from_dict(agg_dict)

    # Creating the figures
    fig = px.imshow(agg, origin='lower', labels={'color':'Log10(abundance)'}, color_continuous_scale=color_scale, height=600, template=template)
    fig.update_traces(hoverongaps=False)
    fig.update_layout(coloraxis_colorbar=dict(title='Abundance', tickprefix='1.e'))

    fig.update_yaxes(showline=True, linewidth=1, linecolor='black', gridwidth=3, range=[min_mz, max_mz])
    fig.update_xaxes(showline=True, linewidth=1, linecolor='black', showgrid=False)
    if max_rt < 100000:
        fig.update_xaxes(range=[min_rt, max_rt])

    if len(msn_results) > 0:
        ms2_results = msn_results[msn_results["level"] == 2]
        ms3_results = msn_results[msn_results["level"] == 3]
    else:
        ms2_results = pd.DataFrame()
        ms3_results = pd.DataFrame()
        
    too_many_ms2 = False
    MAX_MS2 = 1000000
    if len(ms2_results) > MAX_MS2 or len(ms3_results) > MAX_MS2:
       too_many_ms2 = True
    
    if show_ms2_markers is True and too_many_ms2 is False and len(ms2_results) > 0:
        scatter_fig = go.Scattergl(x=ms2_results["rt"], y=ms2_results["precursor_mz"], mode='markers', customdata=ms2_results["scan"], marker=dict(color=ms2marker_color, size=ms2marker_size, symbol="x"), name="MS2s")
        fig.add_trace(scatter_fig)

    if show_ms2_markers is True and too_many_ms2 is False and len(ms3_results) > 0:
        scatter_ms3_fig = go.Scatter(x=ms3_results["rt"], y=ms3_results["precursor_mz"], mode='markers', customdata=ms3_results["scan"], marker=dict(color='green', size=ms2marker_size, symbol="x"), name="MS3s")
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