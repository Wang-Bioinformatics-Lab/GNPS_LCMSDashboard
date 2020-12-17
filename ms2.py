import requests
import pymzml
import json
from download import _resolve_usi
from utils import MS_precisions

def _get_ms2_peaks(usi, scan_number):
    # Lets also make a MASST link here
    # We'll have to get the MS2 peaks from USI
    usi_json_url = "https://metabolomics-usi.ucsd.edu/json/?usi={}".format(usi)
    
    try:
        r = requests.get(usi_json_url)
        spectrum_json = r.json()
        peaks = spectrum_json["peaks"]
        precursor_mz = spectrum_json["precursor_mz"]
    except:
        # Lets look at file on disk
        print("JSON USI EXCEPTION")
        remote_link, local_filename = _resolve_usi(usi)
        run = pymzml.run.Reader(local_filename, MS_precisions=MS_precisions)
        spectrum = run[scan_number]
        peaks = spectrum.peaks("raw")
        precursor_mz = spectrum.selected_precursors[0]["mz"]

    return peaks, precursor_mz

