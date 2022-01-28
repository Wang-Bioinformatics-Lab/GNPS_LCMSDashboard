import pandas as pd
import requests
import uuid
import werkzeug
from scipy import integrate
import os
import sys
import pymzml
import json
import urllib.parse
from tqdm import tqdm
from time import sleep
import sys

MS_precisions = {
    1 : 5e-6,
    2 : 20e-6,
    3 : 20e-6,
    4 : 20e-6,
    5 : 20e-6,
    6 : 20e-6,
    7 : 20e-6
}


import subprocess, io



def _calculate_file_stats(usi, local_filename):
    run = pymzml.run.Reader(local_filename, MS_precisions=MS_precisions)
    number_scans = run.get_spectrum_count()

    response_dict = {}
    response_dict["USI"] = usi
    response_dict["Scans"] = number_scans

    try:
        cmd = ["./bin/msaccess", local_filename, "-x",  'run_summary delimiter=tab']

        my_env = os.environ.copy()
        my_env["LC_ALL"] = "C"

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, env=my_env)
        out = proc.communicate()[0]

        all_lines = str(out).replace("\\t", "\t").split("\\n")
        all_lines = [line for line in all_lines if len(line) > 10 ]
        updated_version = "\n".join(all_lines)
                
        data = io.StringIO(updated_version)
        df = pd.read_csv(data, sep="\t")
        
        record = df.to_dict(orient='records')[0]

        fields = ["Vendor", "Model", "MS1s", "MS2s"]
        for field in fields:
            if field in record:
                response_dict[field] = record[field]
            else:
                response_dict[field] = "N/A"
    except:
        pass
    
    return response_dict

# Gets Positive and Negative return values, or None
def _get_scan_polarity(spec):
    # Determining scan polarity
    polarity = None
    try:
        if spec["negative scan"] is True:
            polarity = "Negative"
        if spec["positive scan"] is True:
            polarity = "Positive"
    except:    
        pass
     
    return polarity

# Given URL, will try to parse and get key
def _get_param_from_url(search, url_hash, param_key, default, session_dict={}, old_value=None, no_change_default=None):
    try:
        param_value = session_dict[param_key]
        if param_value == old_value:
            return no_change_default
        return param_value
    except:
        pass

    try:
        params_dict = urllib.parse.parse_qs(search[1:])
        if param_key in params_dict:
            param_value = str(params_dict[param_key][0])
            if param_value == old_value:
                return no_change_default
            return param_value
    except:
        pass

    try:
        hash_dict = json.loads(urllib.parse.unquote(url_hash[1:]))
        if param_key in hash_dict:
            param_value = str(hash_dict[param_key])
            if param_value == old_value:
                return no_change_default
            return param_value
    except:
        pass

    param_value = default
    if param_value == old_value:
        return no_change_default
    return param_value

def _resolve_map_plot_selection(url_search, usi, local_filename, 
                ui_map_selection=None, 
                map_plot_rt_min="",
                map_plot_rt_max="",
                map_plot_mz_min="",
                map_plot_mz_max="",
                session_dict={},
                priority="url"):
    """
    This resolves the map plot selection, given url

    Args:
        url_search ([type]): [description]
        usi ([type]): [description]
        local_filename ([type]): [description]

    Raises:
        Exception: [description]

    Returns:
        [type]: [description]
    """

    system_map_selection = {}
    manual_map_selection = {}
    

    highlight_box = None

    # Lets start off with taking the url bounds
    try:
        system_map_selection = json.loads(_get_param_from_url(url_search, "", "map_plot_zoom", "{}", session_dict=session_dict))
    except:
        pass

    try:
        usi_splits = usi.split(":")
        dataset = usi_splits[1]
        filename = usi_splits[2]

        if len(usi_splits) > 3 and usi_splits[3] == "scan":
            scan_number = int(usi_splits[4])

            if scan_number == 1:
                # Lets get out of here and not set anything
                raise Exception
            
            run = pymzml.run.Reader(local_filename, MS_precisions=MS_precisions)
            spec = run[scan_number]
            rt = spec.scan_time_in_minutes()
            mz = spec.selected_precursors[0]["mz"]

            min_rt = max(rt - 0.5, 0)
            max_rt = rt + 0.5

            min_mz = mz - 3
            max_mz = mz + 3

            # If this is already set in the URL, we don't overwrite
            if len(system_map_selection) == 0 or "autosize" in system_map_selection:
                system_map_selection["xaxis.range[0]"] = min_rt
                system_map_selection["xaxis.range[1]"] = max_rt
                system_map_selection["yaxis.range[0]"] = min_mz
                system_map_selection["yaxis.range[1]"] = max_mz

            highlight_box = {}
            highlight_box["left"] = rt - 0.01
            highlight_box["right"] = rt + 0.01
            highlight_box["top"] = mz + 0.1
            highlight_box["bottom"] = mz - 0.1
    except:
        pass

    # If the entries are set, then we will override the UI map selection
    try:
        min_rt = float(map_plot_rt_min)
        # Check if the values one by one, are not default
        if min_rt > 0:
            manual_map_selection["xaxis.range[0]"] = min_rt
    except:
        pass
    try:
        max_rt = float(map_plot_rt_max)
        # Check if the values one by one, are not default
        if max_rt < 1000000:
            manual_map_selection["xaxis.range[1]"] = max_rt
    except:
        pass
    try:
        min_mz = float(map_plot_mz_min)
        # Check if the values one by one, are not default
        if min_mz > 0:
            manual_map_selection["yaxis.range[0]"] = min_mz
    except:
        pass
    try:
        max_mz = float(map_plot_mz_max)
        # Check if the values one by one, are not default
        if max_mz < 1000000:
            manual_map_selection["yaxis.range[1]"] = max_mz
    except:
        pass

    current_map_selection = system_map_selection

    if priority == "ui":
        # Special case when the ui gives you something and we should use or not use it
        if "xaxis.autorange" in ui_map_selection:
            current_map_selection = ui_map_selection
        if "xaxis.range[0]" in ui_map_selection:
            current_map_selection = ui_map_selection
        if "autosize" in ui_map_selection:
            pass
    if priority == "ui_update_range":
        current_map_selection = manual_map_selection
    if priority == "session":
        current_map_selection = system_map_selection

    # Getting values for rt and mz
    try:
        min_rt = current_map_selection.get("xaxis.range[0]", 0)
        max_rt = current_map_selection.get("xaxis.range[1]", 1000000)
        min_mz = current_map_selection.get("yaxis.range[0]", 0)
        max_mz = current_map_selection.get("yaxis.range[1]", 1000000)
    except:
        min_rt = 0
        max_rt = 1000000
        min_mz = 0
        max_mz = 1000000

    return current_map_selection, highlight_box, min_rt, max_rt, min_mz, max_mz


def _determine_rendering_bounds(map_selection):
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

    return min_rt, max_rt, min_mz, max_mz

# Binary Search, returns target
def _find_lcms_rt(run, rt_query):
    spectrum_count = run.get_spectrum_count()

    s = 0
    e = spectrum_count

    while True:
        jump_point = int((e + s) / 2)
        print("BINARY SEARCH", jump_point)

        # Jump out early
        if jump_point == 0:
            break
        
        if jump_point == spectrum_count:
            break

        if s == e:
            break

        if e - s == 1:
            break

        spec = run[ jump_point ]

        rt = spec.scan_time_in_minutes()

        if rt < rt_query:
            s = jump_point
        elif rt > rt_query:
            e = jump_point
        else:
            break

    return e


def _spectrum_generator(filename, min_rt, max_rt):
    run = pymzml.run.Reader(filename, MS_precisions=MS_precisions)

    # Don't do this if the min_rt and max_rt are not reasonable values
    if min_rt <= 0 and max_rt > 1000:
        for spec in run:
            yield spec
    else:
        try:
            min_rt_index = _find_lcms_rt(run, min_rt) # These are inclusive on left
            max_rt_index = _find_lcms_rt(run, max_rt) + 1 # Exclusive on the right

            for spec_index in tqdm(range(min_rt_index, max_rt_index)):
                spec = run[spec_index]
                yield spec
            print("USED INDEX")
        except:
            run = pymzml.run.Reader(filename, MS_precisions=MS_precisions)
            for spec in run:
                yield spec
            print("USED BRUTEFORCE")

# Getting the Overlay data
def _resolve_overlay(overlay_usi, overlay_mz, overlay_rt, overlay_filter_column, overlay_filter_value, overlay_size, overlay_color, overlay_hover, overlay_tabular_data=""):
    # Let's try the UDI
    try:
        overlay_usi_splits = overlay_usi.split(":")
        file_path = overlay_usi_splits[2].split("-")[-1]
        task = overlay_usi_splits[2].split("-")[1]
        url = "http://massive.ucsd.edu/ProteoSAFe/DownloadResultFile?task={}&block=main&file={}".format(task, file_path)
        overlay_df = pd.read_csv(url, sep=None, nrows=400000)
    except:
        if len(overlay_tabular_data) > 0:
            # if this fails, we can try parsing overlay_tabular_data
            # overlay_tabular_data
            from io import StringIO
            temp_data = StringIO(overlay_tabular_data)
            overlay_df = pd.read_csv(temp_data, sep=None)
        else:
            return pd.DataFrame()

    # Adding mz
    if len(overlay_mz) > 0 and overlay_mz in overlay_df:
        overlay_df["mz"] = overlay_df[overlay_mz]

    # Adding rt
    if len(overlay_rt) > 0 and overlay_rt in overlay_df:
        overlay_df["rt"] = overlay_df[overlay_rt]

    # Filtering
    if len(overlay_filter_column) > 0 and overlay_filter_column in overlay_df:
        if len(overlay_filter_value) > 0:
            overlay_df = overlay_df[overlay_df[overlay_filter_column] == overlay_filter_value]

    # Adding Size
    if len(overlay_size) > 0 and overlay_size in overlay_df:
        overlay_df["size"] = overlay_df[overlay_size]
    
    # Adding Color
    if len(overlay_color) > 0 and overlay_color in overlay_df:
        overlay_df["color"] = overlay_df[overlay_color]
    
    # Adding Label
    if len(overlay_hover) > 0 and overlay_hover in overlay_df:
        overlay_df["hover"] = overlay_df[overlay_hover]

    return overlay_df

def determine_usi_to_use(usi_string, usi_select):
    """
    More intelligently decide whether to use the usi select or the default first USI
    """
    plot_usi = usi_string.split("\n")[0]
    if usi_select is not None and len(usi_select) > 3:
        plot_usi = usi_select

    return plot_usi