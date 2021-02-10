import requests
import pymzml
import json
from utils import MS_precisions
import xml.etree.ElementTree as ET
import xmltodict
import yaml
from bs4 import BeautifulSoup
from tqdm import tqdm

def _get_ms2_peaks(usi, local_filename, scan_number):
    # Let's first try to get the spectrum from disk
    precursor_mz = 0
    peaks = []
    spectrum_details_string = ""

    try:
        try:
            run = pymzml.run.Reader(local_filename, MS_precisions=MS_precisions)
            spectrum = run[int(scan_number)]
        except:
            spectrum = run[str(scan_number)]
        
        peaks = spectrum.peaks("raw")

        xml_string = ET.tostring(spectrum.element, encoding='utf8', method='xml')
        spectrum_details_string = BeautifulSoup(xml_string.decode("ascii", "ignore"), "xml").prettify()

        if len(spectrum.selected_precursors) > 0:
            precursor_mz = spectrum.selected_precursors[0]["mz"]
    except:
        # We'll have to get the MS2 peaks from USI
        usi_json_url = "https://metabolomics-usi.ucsd.edu/json/?usi={}".format(usi)
        
        r = requests.get(usi_json_url)
        spectrum_json = r.json()
        peaks = spectrum_json["peaks"]
        precursor_mz = spectrum_json["precursor_mz"]
        spectrum_details_string = json.dumps(spectrum_json)

    return peaks, precursor_mz, spectrum_details_string

def determine_scan_by_rt(usi, local_filename, rt, ms_level=1):
    # Understand parameters
    min_rt_delta = 1000
    closest_scan = 0
    run = pymzml.run.Reader(local_filename, MS_precisions=MS_precisions)
    for spec in tqdm(run):
        if spec.ms_level == ms_level:
            try:
                delta = abs(spec.scan_time_in_minutes() - rt)
                if delta < min_rt_delta:
                    closest_scan = spec.ID
                    min_rt_delta = delta
            except:
                pass

    return closest_scan