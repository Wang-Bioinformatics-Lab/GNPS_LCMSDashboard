from utils import _get_scan_polarity, _spectrum_generator
import pymzml
from utils import MS_precisions
import pandas as pd
from collections import defaultdict
import numpy as np
import uuid
import os
import shutil
import glob

def _calculate_upper_lower_tolerance(target_mz, xic_tolerance, xic_ppm_tolerance, xic_tolerance_unit):
    if xic_tolerance_unit == "Da":
        return target_mz - xic_tolerance, target_mz + xic_tolerance
    else:
        calculated_tolerance = target_mz / 1000000 * xic_ppm_tolerance
        return target_mz - calculated_tolerance, target_mz + calculated_tolerance

def _xic_file_slow(input_filename, all_xic_values, xic_tolerance, xic_ppm_tolerance, xic_tolerance_unit, rt_min, rt_max, polarity_filter):
    # Saving out MS2 locations
    all_ms2_ms1_int = []
    all_ms2_rt = []
    all_ms2_scan = []

    # Performing XIC Plot
    xic_trace = defaultdict(list)
    rt_trace = []
    
    sum_i = 0 # Used by MS2 height
    for spec in _spectrum_generator(input_filename, rt_min, rt_max):
        if spec.ms_level == 1:
            scan_polarity = _get_scan_polarity(spec)

            if polarity_filter == "None":
                pass
            elif polarity_filter == "Positive":
                if scan_polarity != "Positive":
                    continue
            elif polarity_filter == "Negative":
                if scan_polarity != "Negative":
                    continue

            try:
                for target_mz in all_xic_values:
                    lower_tolerance, upper_tolerance = _calculate_upper_lower_tolerance(target_mz[1], xic_tolerance, xic_ppm_tolerance, xic_tolerance_unit)

                    # Filtering peaks by mz
                    peaks_full = spec.peaks("raw")
                    peaks = peaks_full[
                        np.where(np.logical_and(peaks_full[:, 0] >= lower_tolerance, peaks_full[:, 0] <= upper_tolerance))
                    ]

                    # summing intensity
                    sum_i = sum([peak[1] for peak in peaks])
                    xic_trace[target_mz[0]].append(sum_i)
            except:
                raise
                pass

            rt_trace.append(spec.scan_time_in_minutes())

        # Saving out the MS2 scans for the XIC
        elif spec.ms_level == 2:
            if len(all_xic_values) == 1:
                try:
                    target_mz = all_xic_values[0]
                    lower_tolerance, upper_tolerance = _calculate_upper_lower_tolerance(target_mz[1], xic_tolerance, xic_ppm_tolerance, xic_tolerance_unit)

                    ms2_mz = spec.selected_precursors[0]["mz"]
                    if ms2_mz < lower_tolerance or ms2_mz > upper_tolerance:
                        continue
                    all_ms2_ms1_int.append(sum_i)
                    all_ms2_rt.append(spec.scan_time_in_minutes())
                    all_ms2_scan.append(spec.ID)
                except:
                    pass

    # Formatting Data Frame
    xic_df = pd.DataFrame()
    for target_xic in xic_trace:
        target_name = "XIC {}".format(target_xic)
        xic_df[target_name] = xic_trace[target_xic]
    xic_df["rt"] = rt_trace

    ms2_data = {}
    ms2_data["all_ms2_ms1_int"] = all_ms2_ms1_int
    ms2_data["all_ms2_rt"] = all_ms2_rt
    ms2_data["all_ms2_scan"] = all_ms2_scan

    return xic_df, ms2_data

def _xic_file_fast(input_filename, all_xic_values, xic_tolerance, xic_ppm_tolerance, xic_tolerance_unit, rt_min, rt_max, polarity_filter, temp_folder="temp"):
    xic_df = pd.DataFrame()

    for target_mz in all_xic_values:
        lower_tolerance, upper_tolerance = _calculate_upper_lower_tolerance(target_mz[1], xic_tolerance, xic_ppm_tolerance, xic_tolerance_unit)
        temp_result_folder = os.path.join(temp_folder, str(uuid.uuid4()))

        cmd = 'export LC_ALL=C && ./bin/msaccess {} -o {} -x "tic mz={},{} delimiter=tab" --filter "msLevel 1" --filter "scanTime ["{},{}"]"'.format(input_filename, temp_result_folder, lower_tolerance, upper_tolerance, rt_min*60, rt_max*60)
        os.system(cmd)
        print(cmd)

        # Reading output file
        result_filename = glob.glob(os.path.join(temp_result_folder, "*"))[0]
        result_df = pd.read_csv(result_filename, sep="\t", skiprows=1)

        xic_df["rt"] = result_df["rt"] / 60.0
        xic_df["XIC {}".format(target_mz[0])] = result_df["sumIntensity"]

        # Remove temp folder
        shutil.rmtree(temp_result_folder)

    return xic_df, {}