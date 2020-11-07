from utils import _get_scan_polarity, _spectrum_generator
import pymzml
from utils import MS_precisions
import pandas as pd

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