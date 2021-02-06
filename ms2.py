import requests
import pymzml
import json
from utils import MS_precisions
import xml.etree.ElementTree as ET
import xmltodict
import yaml
from bs4 import BeautifulSoup

def _get_ms2_peaks(usi, local_filename, scan_number):
    # Let's first try to get the spectrum from disk
    precursor_mz = 0
    peaks = []
    spectrum_details_string = ""

    try:
        run = pymzml.run.Reader(local_filename, MS_precisions=MS_precisions)
        spectrum = run[int(scan_number)]
        peaks = spectrum.peaks("raw")

        xml_string = ET.tostring(spectrum.element, encoding='utf8', method='xml')
        #spectrum_details_string = yaml.dump(xmltodict.parse(xml_string), indent=4)
        spectrum_details_string = BeautifulSoup(xml_string.decode("ascii", "ignore"), "xml").prettify()

        if len(spectrum.selected_precursors) > 0:
            precursor_mz = spectrum.selected_precursors[0]["mz"]
    except:

        raise

        # We'll have to get the MS2 peaks from USI
        usi_json_url = "https://metabolomics-usi.ucsd.edu/json/?usi={}".format(usi)
        
        r = requests.get(usi_json_url)
        spectrum_json = r.json()
        peaks = spectrum_json["peaks"]
        precursor_mz = spectrum_json["precursor_mz"]
        spectrum_details_string = json.dumps(spectrum_json)

    return peaks, precursor_mz, spectrum_details_string


# This will be the main thing to call to process a spectrum
def perform_processing_ms2(usi, local_filename, scan_number):
    print("PERFORM PROCESSING")
