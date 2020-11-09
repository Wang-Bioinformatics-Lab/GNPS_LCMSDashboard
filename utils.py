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


MS_precisions = {
    1 : 5e-6,
    2 : 20e-6,
    3 : 20e-6
}

# Returns remote_link and local filepath
def _resolve_usi(usi):
    usi_splits = usi.split(":")

    if "LOCAL" in usi_splits[1]:
        return "", os.path.join("temp", os.path.basename(usi_splits[2]))

    if "MSV" in usi_splits[1]:
        # Test: mzspec:MSV000084494:GNPS00002_A3_p:scan:1
        # Bigger Test: mzspec:MSV000083388:1_p_153001_01072015:scan:12
        lookup_url = f'https://massive.ucsd.edu/ProteoSAFe/QuerySpectrum?id={usi}'
        lookup_request = requests.get(lookup_url)

        resolution_json = lookup_request.json()

        remote_path = None
        
        mzML_resolutions = [resolution for resolution in resolution_json["row_data"] if os.path.splitext(resolution["file_descriptor"])[1] == ".mzML"]
        mzXML_resolutions = [resolution for resolution in resolution_json["row_data"] if os.path.splitext(resolution["file_descriptor"])[1] == ".mzXML"]

        if len(mzML_resolutions) > 0:
            remote_path = mzML_resolutions[0]["file_descriptor"]
        elif len(mzXML_resolutions) > 0:
            remote_path = mzXML_resolutions[0]["file_descriptor"]

        # Format into FTP link
        remote_link = f"ftp://massive.ucsd.edu/{remote_path[2:]}"
    elif "GNPS" in usi_splits[1]:
        if "TASK-" in usi_splits[2]:

            # Test: mzspec:GNPS:TASK-de188599f53c43c3aaad95491743c784-spec/spec-00000.mzML:scan:31
            filename = "-".join(usi_splits[2].split("-")[2:])
            task = usi_splits[2].split("-")[1]

            remote_link = "http://massive.ucsd.edu/ProteoSAFe/DownloadResultFile?task={}&block=main&file={}".format(task, filename)
        elif "QUICKSTART-" in usi_splits[2]:
            filename = "-".join(usi_splits[2].split("-")[2:])
            task = usi_splits[2].split("-")[1]

            remote_link = "http://gnps-quickstart.ucsd.edu/conversion/file?sessionid={}&filename={}".format(task, filename)
            print(remote_link)
        elif "GNPS-LIBRARY" in usi_splits[2]:
            print("Library Entry")
            # Lets find the provenance file
            accession = usi_splits[4]
            url = "https://gnps.ucsd.edu/ProteoSAFe/SpectrumCommentServlet?SpectrumID={}".format(accession)
            r = requests.get(url)
            spectrum_dict = r.json()
            task = spectrum_dict["spectruminfo"]["task"]
            source_file = os.path.basename(spectrum_dict["spectruminfo"]["source_file"])
            remote_link = "ftp://ccms-ftp.ucsd.edu/GNPS_Library_Provenance/{}/{}".format(task, source_file)
    elif "MTBLS" in usi_splits[1]:
        dataset_accession = usi_splits[1]
        filename = usi_splits[2]
        remote_link = "ftp://ftp.ebi.ac.uk/pub/databases/metabolights/studies/public/{}/{}".format(dataset_accession, filename)

    # Getting Data Local, TODO: likely should serialize it
    local_filename = os.path.join("temp", werkzeug.utils.secure_filename(remote_link))
    filename, file_extension = os.path.splitext(local_filename)
    converted_local_filename = filename + ".mzML"
    
    if not os.path.isfile(converted_local_filename):
        temp_filename = os.path.join("temp", str(uuid.uuid4()) + file_extension)
        wget_cmd = "wget '{}' -O {}".format(remote_link, temp_filename)
        os.system(wget_cmd)
        os.rename(temp_filename, local_filename)

        temp_filename = os.path.join("temp", str(uuid.uuid4()) + ".mzML")
        # Lets do a conversion
        _convert_mzML(local_filename, temp_filename)

        os.rename(temp_filename, converted_local_filename)

        local_filename = converted_local_filename

    return remote_link, converted_local_filename

# First try msconvert, if the output fails, then we will do pyteomics to mzML and then msconvert
def _convert_mzML(input_mzXML, output_mzML):
    conversion_cmd = "export LC_ALL=C && ./bin/msconvert {} --mzML --32 --outfile {} --outdir {} --filter 'threshold count 500 most-intense'".format(input_mzXML, output_mzML, os.path.dirname(output_mzML))
    conversion_ret_code = os.system(conversion_cmd)

    reconvert = False
    # Checking the conversion
    try:
        from lxml import etree
        doc = etree.parse(output_mzML)
    except:
        reconvert = True
        try:
            os.remove(output_mzML)
        except:
            pass
        print("XML PARSE FAILED, Presuming incomplete conversion")

    if reconvert:
        print("RECONVERTING")

        from psims.mzml.writer import MzMLWriter
        from pyteomics import mzxml, auxiliary

        temp_filename = os.path.join("temp", str(uuid.uuid4()) + ".mzML")

        previous_ms1_scan = 0
        with MzMLWriter(open(temp_filename, 'wb')) as out:
            out.controlled_vocabularies()
            with out.run(id="my_analysis"):
                with out.spectrum_list(count=1000):
                    # Iterating through all scans in the reader
                    try:
                        with mzxml.read(input_mzXML) as reader:
                            for spectrum in reader:
                                ms_level = spectrum["msLevel"]

                                if len(spectrum["intensity array"]) == 0:
                                    continue

                                if ms_level == 1:
                                    out.write_spectrum(
                                            spectrum["m/z array"], spectrum["intensity array"],
                                            id=spectrum["id"], params=[
                                                "MS1 Spectrum",
                                                {"ms level": 1},
                                                {"total ion current": sum(spectrum["intensity array"])}
                                            ],
                                            scan_start_time=spectrum["retentionTime"])

                                    previous_ms1_scan = spectrum["id"]
                                else:
                                    out.write_spectrum(
                                        spectrum["m/z array"], spectrum["intensity array"],
                                        id=spectrum["id"], params=[
                                            "MSn Spectrum",
                                            {"ms level": 2},
                                            {"total ion current": sum(spectrum["intensity array"])}
                                        ],
                                        scan_start_time=spectrum["retentionTime"],
                                        # Include precursor information
                                        precursor_information={
                                            "mz": spectrum["precursorMz"][0]["precursorMz"],
                                            "intensity": spectrum["precursorMz"][0]["precursorIntensity"],
                                            "charge": 0,
                                            "scan_id": previous_ms1_scan,
                                            "activation": ["beam-type collisional dissociation", {"collision energy": spectrum["collisionEnergy"]}],
                                        })
                    except:
                        print("Reading Failed, skipping to end")
                        pass

                            
        # Round trip through MsConvert
        conversion_cmd = "export LC_ALL=C && ./bin/msconvert {} --mzML --32 --outfile {} --outdir {} --filter 'threshold count 500 most-intense'".format(temp_filename, output_mzML, os.path.dirname(output_mzML))
        conversion_ret_code = os.system(conversion_cmd)

        try:
            os.remove(temp_filename)
        except:
            pass


    

import subprocess, io

def _calculate_file_stats(usi):
    remote_link, local_filename = _resolve_usi(usi)

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
        import sys
        print(updated_version, file=sys.stderr)
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
def _get_param_from_url(search, param_key, default):
    try:
        return str(urllib.parse.parse_qs(search[1:])[param_key][0])
    except:
        return default
    return default

def _resolve_map_plot_selection(url_search, usi):
    current_map_selection = None
    highlight_box = None

    # Lets start off with taking the url bounds
    try:
        current_map_selection = json.loads(_get_param_from_url(url_search, "map_plot_zoom", "{}"))
    except:
        pass

    try:
        if "scan" in current_map_selection:
            # Lets do the lookup on the scan
            scan_number = current_map_selection["scan"]
            
            remote_link, local_filename = _resolve_usi(usi)
            run = pymzml.run.Reader(local_filename, MS_precisions=MS_precisions)
            spec = run[scan_number]
            rt = spec.scan_time_in_minutes()
            mz = spec.selected_precursors[0]["mz"]

            min_rt = max(rt - 0.5, 0)
            max_rt = rt + 0.5

            min_mz = mz - 2
            max_mz = mz + 2
            
            current_map_selection["xaxis.range[0]"] = min_rt
            current_map_selection["xaxis.range[1]"] = max_rt
            current_map_selection["yaxis.range[0]"] = min_mz
            current_map_selection["yaxis.range[1]"] = max_mz

            highlight_box = {}
            highlight_box["left"] = rt - 0.01
            highlight_box["right"] = rt + 0.01
            highlight_box["top"] = mz + 0.1
            highlight_box["bottom"] = mz - 0.1
    except:
        pass

    return current_map_selection, highlight_box


# Binary Search, returns target
def _find_lcms_rt(filename, rt_query):
    run = pymzml.run.Reader(filename, MS_precisions=MS_precisions)

    s = 0
    e = run.get_spectrum_count()

    while True:
        jump_point = int((e + s) / 2)

        # Jump out early
        if jump_point == 0:
            break
        
        if jump_point == run.get_spectrum_count():
            break

        if s == e:
            break

        if e - s == 1:
            break

        spec = run[ jump_point ]

        if spec.scan_time_in_minutes() < rt_query:
            s = jump_point
        elif spec.scan_time_in_minutes() > rt_query:
            e = jump_point
        else:
            break

    return e


def _spectrum_generator(filename, min_rt, max_rt):
    run = pymzml.run.Reader(filename, MS_precisions=MS_precisions)
    try:
        min_rt_index = _find_lcms_rt(filename, min_rt) # These are inclusive on left
        max_rt_index = _find_lcms_rt(filename, max_rt) + 1 # Exclusive on the right

        for spec_index in tqdm(range(min_rt_index, max_rt_index)):
            spec = run[spec_index]
            yield spec
        print("USED INDEX")
    except:
        for spec in run:
            yield spec
        print("USED BRUTEFORCE")