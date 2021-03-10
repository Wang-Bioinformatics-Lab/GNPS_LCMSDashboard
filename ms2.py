import requests
import pymzml
import json
from utils import MS_precisions
import xml.etree.ElementTree as ET
import xmltodict
import yaml
from bs4 import BeautifulSoup
from tqdm import tqdm
from utils import _spectrum_generator

def _get_ms_peak_labels(mzs, ints, partitions=8):
    max_mz = max(mzs)
    min_mz = min(mzs)
    mz_radius = (max_mz - min_mz) / partitions

    labeled_peaks = set()
    
    for i in range(partitions):
        try:
            segment_min_mz = min_mz + mz_radius * i
            segment_max_mz = min_mz + mz_radius * (i+1)

            segment_peaks = [(mz, ints[i]) for i, mz in enumerate(mzs) if mz >= segment_min_mz and mz <= segment_max_mz]
            sorted_segment_peaks = sorted(segment_peaks, key=lambda x: x[1], reverse=True)
            segment_most_intense_peak = sorted_segment_peaks[0]

            labeled_peaks.add(segment_most_intense_peak[0])
        except:
            pass

    mzs_text = []
    for mz in mzs:
        if mz in labeled_peaks:
            mzs_text.append("{:.2f}".format(mz))
        else:
            mzs_text.append("")
    
    return mzs_text

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

    for spec in tqdm(_spectrum_generator(local_filename, rt - 0.1, rt + 0.1)):
        if spec.ms_level == ms_level:
            try:
                delta = abs(spec.scan_time_in_minutes() - rt)
                if delta < min_rt_delta:
                    closest_scan = spec.ID
                    min_rt_delta = delta
            except:
                pass

    return closest_scan