
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
            # Still waiting for the window
            if spec.scan_time_in_minutes() < min_rt:
                continue
            
            # We've passed the window
            if spec.scan_time_in_minutes() > max_rt:            
                break
        except:
            pass

        scan_polarity = _get_scan_polarity(spec)

        if polarity_filter == "None":
            pass
        elif polarity_filter == "Positive":
            if scan_polarity != "Positive":
                continue
        elif polarity_filter == "Negative":
            if scan_polarity != "Negative":
                continue
        
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

# Creates the figure for map plot
# overlay_data is a dataframe that includes the overlay, rt and mz are the expected columns
def _create_map_fig(filename, map_selection=None, show_ms2_markers=True, polarity_filter="None", highlight_box=None, overlay_data=None):
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

    print("Datashader Len", len(df))

    cvs = ds.Canvas(plot_width=width, plot_height=height)
    agg = cvs.points(df,'rt','mz', agg=ds.sum("i"))

    end_time = time.time()
    print("Datashader Agg", end_time - start_time)

    zero_mask = agg.values == 0
    agg.values = np.log10(agg.values, where=np.logical_not(zero_mask))
    fig = px.imshow(agg, origin='lower', labels={'color':'Log10(abundance)'}, color_continuous_scale="Hot_r", height=600, template="plotly_white")
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

    # Adding in overlay data
    # Adding a few extra things to the figure
    try:
        overlay_data = overlay_data[overlay_data["rt"] > min_rt]
        overlay_data = overlay_data[overlay_data["rt"] < max_rt]
        overlay_data = overlay_data[overlay_data["mz"] > min_mz]
        overlay_data = overlay_data[overlay_data["mz"] < max_mz]

        size_column = None
        color_column = None
        
        if "size" in overlay_data:
            size_column = "size"
            overlay_data[size_column] = overlay_data[size_column].clip(lower=1)
            #overlay_data[size_column] = np.log(overlay_data[size_column])
            #overlay_data[size_column] = overlay_data[size_column] / max(overlay_data[size_column]) * 10
        
        if "color" in overlay_data:
            color_column = "color"
            overlay_data[color_column] = overlay_data[color_column] / max(overlay_data[color_column]) * 10


        if size_column is None and color_column is None:
            scatter_overlay_fig = go.Scattergl(x=overlay_data["rt"], y=overlay_data["mz"], mode='markers', marker=dict(color='gray', size=10, symbol="circle", opacity=0.7), name="Overlay")
            fig.add_trace(scatter_overlay_fig)
        elif size_column is not None and color_column is None:
            scatter_overlay_fig = px.scatter(overlay_data, x="rt", y="mz", size=size_column)
            scatter_overlay_fig.update_traces(marker=dict(color="gray", symbol="circle", opacity=0.7))
            fig.add_trace(scatter_overlay_fig.data[0])
        elif size_column is None and color_column is not None:
            scatter_overlay_fig = px.scatter(overlay_data, x="rt", y="mz", color=color_column)
            scatter_overlay_fig.update_traces(marker=dict(size=10, symbol="circle", opacity=0.7))
            fig.add_trace(scatter_overlay_fig.data[0])
        else:
            scatter_overlay_fig = px.scatter(overlay_data, x="rt", y="mz", color=color_column, size=size_column)
            scatter_overlay_fig.update_traces(marker=dict(symbol="circle", opacity=0.7))
            fig.add_trace(scatter_overlay_fig.data[0])
            
    except:
        pass

    return fig