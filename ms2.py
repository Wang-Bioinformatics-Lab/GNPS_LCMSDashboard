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

def _get_ms_hover(mzs, ints):
    hover_text = []
    for i, mz in enumerate(mzs):
        hover_text.append("m/z: {:.2f}<br>Intensity: {:.2f}".format(mz, ints[i]))
    
    return hover_text

def _get_spectrum_metadata(spectrum, bs_spectrum_obj):
    spectrum_metadata = {}

    # Collision Energy
    try:
        # find tag with the name "collision energy"
        collision_energy_value = bs_spectrum_obj.find("cvParam", {"name": "collision energy"}).get("value")

        # trying to get the spectrum energy
        spectrum_metadata["collision_energy"] = collision_energy_value
    except:
        pass

    # precursors
    try:
        try:
            precursor_mz = bs_spectrum_obj.find("cvParam", {"name": "isolation window target m/z"}).get("value")
        except:
            precursor_mz = bs_spectrum_obj.find("cvParam", {"name": "selected ion m/z"}).get("value")
            
        spectrum_metadata["precursor_mz"] = precursor_mz
    except:
        pass

    # electron beam energy
    try:
        electron_beam_energy = bs_spectrum_obj.find("cvParam", {"name": "electron beam energy"}).get("value")
        spectrum_metadata["electron_beam_energy"] = electron_beam_energy
    except:
        pass
        
    # adding in polarity
    try:
        positive_tag = bs_spectrum_obj.find("cvParam", {"name": "positive scan"})
        if positive_tag:
            spectrum_metadata["polarity"] = "Positive"
        else:
            spectrum_metadata["polarity"] = "Negative"
    except:
        pass

    # Adding collision of MS2
    try:
        if bs_spectrum_obj.find("cvParam", {"name": "beam-type collision-induced dissociation"}):
            spectrum_metadata["collision_method"] = "HCD"

        if bs_spectrum_obj.find("cvParam", {"name": "collision-induced dissociation"}):
            spectrum_metadata["collision_method"] = "CID"

        if bs_spectrum_obj.find("cvParam", {"name": "electron activated dissociation"}):
            spectrum_metadata["collision_method"] = "EAD"
    except:
        pass

    return spectrum_metadata

def _get_ms2_peaks(usi, local_filename, scan_number):
    # Let's first try to get the spectrum from disk
    precursor_mz = 0
    peaks = []
    spectrum_metadata = {}
    spectrum_details_string = ""

    try:
        try:
            run = pymzml.run.Reader(local_filename, MS_precisions=MS_precisions)
            spectrum = run[int(scan_number)]
        except:
            spectrum = run[str(scan_number)]
        
        peaks = spectrum.peaks("raw")

        xml_string = ET.tostring(spectrum.element, encoding='utf8', method='xml')
        bs_spectrum_obj = BeautifulSoup(xml_string.decode("ascii", "ignore"), "xml")
        spectrum_details_string = bs_spectrum_obj.prettify()

        spectrum_metadata = _get_spectrum_metadata(spectrum, bs_spectrum_obj)

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

    return peaks, precursor_mz, spectrum_details_string, spectrum_metadata

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