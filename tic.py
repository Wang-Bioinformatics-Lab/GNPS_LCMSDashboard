from utils import _get_scan_polarity, _spectrum_generator
import pymzml
from utils import MS_precisions
import pandas as pd
import uuid
import os
import glob
import shutil

def tic_file(input_filename, tic_option="TIC", polarity_filter="None"):
    """
    Creating the TIC data frame, trying the fast when the options are acceptable. 

    Args:
        input_filename ([type]): [description]
        tic_option (str, optional): [description]. Defaults to "TIC".
        polarity_filter (str, optional): [description]. Defaults to "None".

    Returns:
        [type]: [description]
    """
    if tic_option == "TIC" and polarity_filter == "None":
        try:
            return _tic_file_fast(input_filename)
        except:
            pass

    return _tic_file_slow(input_filename, tic_option=tic_option, polarity_filter=polarity_filter)

def _tic_file_slow(input_filename, tic_option="TIC", polarity_filter="None"):
    # Performing TIC Plot
    tic_trace = []
    rt_trace = []
    
    run = pymzml.run.Reader(input_filename, MS_precisions=MS_precisions)
    
    for n, spec in enumerate(run):
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

            rt_trace.append(spec.scan_time_in_minutes())
            if tic_option == "TIC":
                tic_trace.append(sum(spec.i))
            elif tic_option == "BPI":
                tic_trace.append(max(spec.i))

    tic_df = pd.DataFrame()
    tic_df["tic"] = tic_trace
    tic_df["rt"] = rt_trace

    return tic_df

def _tic_file_fast(input_filename, temp_folder="temp"):
    temp_result_folder = os.path.join(temp_folder, str(uuid.uuid4()))

    cmd = 'export LC_ALL=C && ./bin/msaccess {} -o {} -x "tic delimiter=tab" --filter "msLevel 1"'.format(input_filename, temp_result_folder)

    os.system(cmd)
    print(cmd)

    # Reading output file
    result_filename = glob.glob(os.path.join(temp_result_folder, "*"))[0]
    result_df = pd.read_csv(result_filename, sep="\t", skiprows=1)

    tic_df = pd.DataFrame()
    tic_df["rt"] = result_df["rt"] / 60.0
    tic_df["tic"] = result_df["sumIntensity"]

    # Remove temp folder
    shutil.rmtree(temp_result_folder)

    return tic_df