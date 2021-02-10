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

def _get_usi_display_filename(usi):
    usi_splits = usi.split(":")

    return os.path.basename(usi_splits[2])

def _usi_to_local_filename(usi):
    """
        This returns the converted filename
    """
    usi_splits = usi.split(":")

    if "LOCAL" in usi_splits[1]:
        converted_local_filename = werkzeug.utils.secure_filename(":".join(usi_splits[:3]))
        filename, file_extension = os.path.splitext(converted_local_filename)
        converted_local_filename = filename + ".mzML"
        return  converted_local_filename
    
    if "MSV" in usi_splits[1]:
        converted_local_filename = werkzeug.utils.secure_filename(":".join(usi_splits[:3])) + ".mzML"
        return converted_local_filename.replace(".mzML.mzML", ".mzML")

    if "GNPS" in usi_splits[1]:
        if "TASK-" in usi_splits[2]:
            converted_local_filename = werkzeug.utils.secure_filename(":".join(usi_splits[:3]))
            filename, file_extension = os.path.splitext(converted_local_filename)
            converted_local_filename = filename + ".mzML"
            return converted_local_filename
        elif "QUICKSTART-" in usi_splits[2]:
            converted_local_filename = werkzeug.utils.secure_filename(":".join(usi_splits[:3]))
            filename, file_extension = os.path.splitext(converted_local_filename)
            converted_local_filename = filename + ".mzML"
            return converted_local_filename
        elif "GNPS" in usi_splits[2] and "accession" in usi_splits[3]:
            return werkzeug.utils.secure_filename(":".join(usi_splits[:5])) + ".mzML"

    if "MTBLS" in usi_splits[1]:
        converted_local_filename = werkzeug.utils.secure_filename(":".join(usi_splits[:3]))
        filename, file_extension = os.path.splitext(converted_local_filename)
        converted_local_filename = filename + ".mzML"
        return converted_local_filename

    if "ST" in usi_splits[1]:
        converted_local_filename = werkzeug.utils.secure_filename(":".join(usi_splits[:3]))
        filename, file_extension = os.path.splitext(converted_local_filename)
        converted_local_filename = filename + ".mzML"
        return converted_local_filename

    if "PXD" in usi_splits[1]:
        converted_local_filename = werkzeug.utils.secure_filename(":".join(usi_splits[:3])) + ".mzML"
        print(converted_local_filename, file=sys.stderr)
        return converted_local_filename.replace(".mzML.mzML", ".mzML")




def _resolve_msv_usi(usi):
    usi_splits = usi.split(':')

    msv_usi = usi
    if len(usi.split(":")) == 3:
        msv_usi = "{}:scan:1".format(usi)
    
    lookup_url = f'https://massive.ucsd.edu/ProteoSAFe/QuerySpectrum?id={msv_usi}'
    lookup_request = requests.get(lookup_url)

    try:
        resolution_json = lookup_request.json()

        remote_path = None
        
        mzML_resolutions = [resolution for resolution in resolution_json["row_data"] if os.path.splitext(resolution["file_descriptor"])[1] == ".mzML"]
        mzXML_resolutions = [resolution for resolution in resolution_json["row_data"] if os.path.splitext(resolution["file_descriptor"])[1] == ".mzXML"]
        raw_resolutions = [resolution for resolution in resolution_json["row_data"] if os.path.splitext(resolution["file_descriptor"])[1].lower() == ".raw"]

        if len(mzML_resolutions) > 0:
            remote_path = mzML_resolutions[0]["file_descriptor"]
        elif len(mzXML_resolutions) > 0:
            remote_path = mzXML_resolutions[0]["file_descriptor"]
        elif len(raw_resolutions) > 0:
            remote_path = raw_resolutions[0]["file_descriptor"]

        # Format into FTP link
        remote_link = f"ftp://massive.ucsd.edu/{remote_path[2:]}"
    except:
        # We did not successfully look it up, this is the fallback try
        remote_link = f"ftp://massive.ucsd.edu/{usi_splits[1]}/{usi_splits[2]}"

    return remote_link

def _resolve_gnps_usi(usi):
    usi_splits = usi.split(':')

    if "TASK-" in usi_splits[2]:
        # Test: mzspec:GNPS:TASK-de188599f53c43c3aaad95491743c784-spec/spec-00000.mzML:scan:31
        filename = "-".join(usi_splits[2].split("-")[2:])
        task = usi_splits[2].split("-")[1]

        remote_link = "http://massive.ucsd.edu/ProteoSAFe/DownloadResultFile?task={}&block=main&file={}".format(task, urllib.parse.quote(filename))
    elif "QUICKSTART-" in usi_splits[2]:
        filename = "-".join(usi_splits[2].split("-")[2:])
        task = usi_splits[2].split("-")[1]
        remote_link = "http://gnps-quickstart.ucsd.edu/conversion/file?sessionid={}&filename={}".format(task, urllib.parse.quote(filename))
    elif "GNPS" in usi_splits[2] and "accession" in usi_splits[3]:
        print("Library Entry")
        # Lets find the provenance file
        accession = usi_splits[4]
        url = "https://gnps.ucsd.edu/ProteoSAFe/SpectrumCommentServlet?SpectrumID={}".format(accession)
        r = requests.get(url)
        spectrum_dict = r.json()
        task = spectrum_dict["spectruminfo"]["task"]
        source_file = os.path.basename(spectrum_dict["spectruminfo"]["source_file"])
        remote_link = "ftp://ccms-ftp.ucsd.edu/GNPS_Library_Provenance/{}/{}".format(task, source_file)

    return remote_link

def _resolve_mtbls_usi(usi):
    usi_splits = usi.split(':')

    dataset_accession = usi_splits[1]
    filename = usi_splits[2]
    remote_link = "ftp://ftp.ebi.ac.uk/pub/databases/metabolights/studies/public/{}/{}".format(dataset_accession, filename)

    return remote_link

def _resolve_metabolomicsworkbench_usi(usi):
    usi_splits = usi.split(':')

    # First looking 
    dataset_accession = usi_splits[1]
    filename = usi_splits[2]
        
    # Query Accession
    url = "https://massive.ucsd.edu/ProteoSAFe/QueryDatasets?task=N%2FA&file=&pageSize=30&offset=0&query=%257B%2522full_search_input%2522%253A%2522%2522%252C%2522table_sort_history%2522%253A%2522createdMillis_dsc%2522%252C%2522query%2522%253A%257B%257D%252C%2522title_input%2522%253A%2522{}%2522%257D&target=&_=1606254845533".format(dataset_accession)
    r = requests.get(url)
    data_json = r.json()

    msv_accession = data_json["row_data"][0]["dataset"]

    msv_usi = "mzspec:{}:{}:scan:1".format(msv_accession, filename)

    return _resolve_msv_usi(msv_usi)

def _resolve_pxd_usi(usi):
    usi_splits = usi.split(':')

    # Lets first do lookup in PXD, and then try to find the filename and path
    dataset_accession = usi_splits[1]
    filename = usi_splits[2]

    lookup_url = f"http://proteomecentral.proteomexchange.org/cgi/GetDataset?ID={dataset_accession}&outputMode=json&test=no"
    lookup_request = requests.get(lookup_url)
    resolution_json = lookup_request.json()

    # Checking if this is a dataset from PRIDE or MassIVE
    remote_link = ""
    full_dataset_links = [dataset_obj["name"] for dataset_obj in resolution_json["fullDatasetLinks"]]
    if "MassIVE dataset URI" in full_dataset_links:
        return _resolve_msv_usi(usi)
    elif "PRIDE project URI" in full_dataset_links:
        for filename_object in resolution_json["datasetFiles"]:
            if filename in filename_object["value"]:
                remote_link = filename_object["value"]

    return remote_link

def _resolve_usi_remotelink(usi):
    """
    Tries to convert usi to a remote URL path to get the file

    Args:
        usi ([type]): [description]

    Returns:
        [type]: [description]
    """

    usi_splits = usi.split(":")
    
    if "MSV" in usi_splits[1]:
        remote_link = _resolve_msv_usi(usi)
    elif "GNPS" in usi_splits[1]:
        remote_link = _resolve_gnps_usi(usi)
    elif "MTBLS" in usi_splits[1]:
        remote_link = _resolve_mtbls_usi(usi)
    elif "ST" in usi_splits[1]:
        remote_link = _resolve_metabolomicsworkbench_usi(usi)
    elif "PXD" in usi_splits[1]:
        remote_link = _resolve_pxd_usi(usi)

    return remote_link

def _usi_to_ccms_path(usi):
    """
    Tries to convert usi to a relative path in CCMS. None if not found

    Args:
        usi ([type]): [description]

    Returns:
        [type]: [description]
    """
    usi_splits = usi.split(":")

    if "LOCAL" in usi_splits[1]:
        return None
    
    if "MSV" in usi_splits[1]:
        msv_ftp = _resolve_msv_usi(usi)
        msv_ftp = msv_ftp.replace("ftp://massive.ucsd.edu/", "")

        return "f.{}".format(msv_ftp)

    if "GNPS" in usi_splits[1]:
        if "TASK-" in usi_splits[2]:
            return usi_splits[2].split("-")[-1]
        elif "QUICKSTART-" in usi_splits[2]:
            return None
        elif "GNPS" in usi_splits[2] and "accession" in usi_splits[3]:
            return None

    if "MTBLS" in usi_splits[1]:
        return None

    if "ST" in usi_splits[1]:
        msv_ftp = _resolve_metabolomicsworkbench_usi(usi)
        msv_ftp = msv_ftp.replace("ftp://massive.ucsd.edu/", "")

        return "f.{}".format(msv_ftp)

    if "PXD" in usi_splits[1]:
        return None

def _resolve_exists_local(usi, temp_folder="temp"):
    usi_splits = usi.split(":")

    converted_local_filename = os.path.join(temp_folder, _usi_to_local_filename(usi))

    # Only call if does not exists
    if os.path.exists(converted_local_filename):
        return True
    
    return False


# Returns remote_link and local filepath
def _resolve_usi(usi, temp_folder="temp"):
    usi_splits = usi.split(":")

    converted_local_filename = os.path.join(temp_folder, _usi_to_local_filename(usi))

    # Only call if does not exists
    if os.path.exists(converted_local_filename):
        return "", converted_local_filename

    if "LOCAL" in usi_splits[1]:
        local_filename = os.path.join(temp_folder, os.path.basename(usi_splits[2]))
        filename, file_extension = os.path.splitext(local_filename)

        if not os.path.isfile(converted_local_filename):
            temp_filename = os.path.join(temp_folder, str(uuid.uuid4()) + ".mzML")
            # Lets do a conversion
            if file_extension == ".cdf":
                _convert_cdf_to_mzML(local_filename, temp_filename)
            else:
                _convert_mzML(local_filename, temp_filename)

            os.rename(temp_filename, converted_local_filename)

        return "", converted_local_filename

    remote_link = _resolve_usi_remotelink(usi)

    # Getting Data Local, TODO: likely should serialize it
    local_filename = os.path.join(temp_folder, werkzeug.utils.secure_filename(remote_link))
    filename, file_extension = os.path.splitext(local_filename)

    temp_filename = os.path.join(temp_folder, str(uuid.uuid4()) + file_extension)
    wget_cmd = "wget '{}' -O {} 2> /dev/null".format(remote_link, temp_filename)
    os.system(wget_cmd)
    os.rename(temp_filename, local_filename)

    temp_filename = os.path.join(temp_folder, str(uuid.uuid4()) + ".mzML")
    # Lets do a conversion
    if file_extension.lower() == ".cdf":
        _convert_cdf_to_mzML(local_filename, temp_filename)
    elif file_extension.lower() == ".raw":
        _convert_raw_to_mzML(local_filename, temp_filename)
    else:
        _convert_mzML(local_filename, temp_filename)

    # Renaming the temp
    os.rename(temp_filename, converted_local_filename)

    # Cleanup
    try:
        if local_filename != converted_local_filename:
            os.remove(local_filename)
    except:
        pass

    return remote_link, converted_local_filename


def _convert_raw_to_mzML(input_raw, output_mzML):
    """
    This will convert Thermo RAW to mzML
    """

    output_directory = "temp"
    thermo_converted_filename = os.path.join(output_directory, os.path.splitext(os.path.basename(input_raw))[0] + ".mzML")

    import subprocess
    conversion_cmd = ["mono", "/src/bin/x64/Debug/ThermoRawFileParser.exe", "-i={}".format(input_raw), "-o={}".format(output_directory), "-f=1"]
    subprocess.check_call(" ".join(conversion_cmd), shell=True)


    #conversion_cmd = "export LC_ALL=C && ./bin/msconvert {} --mzML --32 --outfile {} --outdir {} --filter 'threshold count 500 most-intense'".format(thermo_converted_filename, output_mzML, os.path.dirname(output_mzML))
    conversion_cmd = "export LC_ALL=C && ./bin/msconvert {} --mzML --32 --outfile {} --outdir {} --filter 'threshold absolute 1 most-intense' --filter 'msLevel 1-4'".format(thermo_converted_filename, output_mzML, os.path.dirname(output_mzML))
    os.system(conversion_cmd)


# First try msconvert, if the output fails, then we will do pyteomics to mzML and then msconvert
def _convert_mzML(input_mzXML, output_mzML):
    """
    This will convert mzXML and mzML to mzML
    """

    #conversion_cmd = "export LC_ALL=C && ./bin/msconvert {} --mzML --32 --outfile {} --outdir {} --filter 'threshold count 500 most-intense' --filter 'msLevel 1' --filter 'MS2Denoise 0 4000'".format(input_mzXML, output_mzML, os.path.dirname(output_mzML))
    #conversion_cmd = "export LC_ALL=C && ./bin/msconvert {} --mzML --32 --outfile {} --outdir {} --filter 'threshold count 500 most-intense' --filter 'MS2Denoise 0 4000'".format(input_mzXML, output_mzML, os.path.dirname(output_mzML))
    #conversion_cmd = "export LC_ALL=C && ./bin/msconvert {} --mzML --32 --outfile {} --outdir {} --filter 'threshold count 500 most-intense'".format(input_mzXML, output_mzML, os.path.dirname(output_mzML))
    conversion_cmd = "export LC_ALL=C && ./bin/msconvert {} --mzML --32 --outfile {} --outdir {} --filter 'threshold absolute 1 most-intense' --filter 'msLevel 1-4'".format(input_mzXML, output_mzML, os.path.dirname(output_mzML))
    #conversion_cmd = "export LC_ALL=C && ./bin/msconvert {} --mzML --32 --outfile {} --outdir {}".format(input_mzXML, output_mzML, os.path.dirname(output_mzML))
    conversion_ret_code = os.system(conversion_cmd)

    # Checking the conversion only if the source is mzXML
    filename, file_extension = os.path.splitext(input_mzXML)
    if file_extension != ".mzXML":
        return

    reconvert = False
    
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
        #conversion_cmd = "export LC_ALL=C && ./bin/msconvert {} --mzML --32 --outfile {} --outdir {} --filter 'threshold count 500 most-intense'".format(temp_filename, output_mzML, os.path.dirname(output_mzML))
        conversion_cmd = "export LC_ALL=C && ./bin/msconvert {} --mzML --32 --outfile {} --outdir {} --filter 'threshold absolute 1 most-intense' --filter 'msLevel 1-4'".format(temp_filename, output_mzML, os.path.dirname(output_mzML))

        conversion_ret_code = os.system(conversion_cmd)

        try:
            os.remove(temp_filename)
        except:
            pass

# in python doing a conversion from cdf to mzML
def _convert_cdf_to_mzML(input_cdf, output_mzML):
    from netCDF4 import Dataset
    from psims.mzml.writer import MzMLWriter
    import numpy as np

    temp_filename = os.path.join("temp", str(uuid.uuid4()) + ".mzML")

    # lets put the cdf reader here
    cdf_reader = Dataset(input_cdf, "r")
    mass_values      = np.array(cdf_reader.variables["mass_values"][:])
    intensity_values = np.array(cdf_reader.variables["intensity_values"][:])
    time_values = np.array(cdf_reader.variables["scan_acquisition_time"][:])
    scan_values = np.array(cdf_reader.variables["scan_index"][:])

    #removing empty scans
    dd = np.diff(scan_values) != 0
    dd = np.append(dd, True)
    ddi = np.arange(scan_values.shape[0], dtype = np.int64)[dd]
    time_values = time_values[ddi]
    scan_values = scan_values[ddi]

    # getting scan boundaries
    scan_end_values = np.append(scan_values[1:]-1, mass_values.shape[0]-1)
    scan_indcs = zip(scan_values, scan_end_values)

    # Writing everything out
    with MzMLWriter(open(temp_filename, 'wb')) as out:
        out.controlled_vocabularies()
        with out.run(id="my_analysis"):
            with out.spectrum_list(count=1000):
                # Iterating through all scans in the reader
                try:
                    # reading through scans
                    for i, scan_range in enumerate(scan_indcs):
                        time_min_rt = time_values[i] / 60

                        _mz_array = np.array(mass_values[scan_range[0]:scan_range[1]])
                        _i_array = np.array(intensity_values[scan_range[0]:scan_range[1]])
                        
                        out.write_spectrum(
                            _mz_array, _i_array,
                            id=str(i), params=[
                                "MS1 Spectrum",
                                {"ms level": 1},
                                {"total ion current": sum(_i_array)}
                            ],
                            scan_start_time=time_min_rt)
                except:
                    print("Reading Failed, skipping to end")
                    pass

    # # Round trip through MsConvert
    # conversion_cmd = "export LC_ALL=C && ./bin/msconvert {} --mzML --32 --outfile {} --outdir {} --filter 'threshold count 500 most-intense'".format(temp_filename, output_mzML, os.path.dirname(output_mzML))
    # conversion_ret_code = os.system(conversion_cmd)

    # try:
    #     os.remove(temp_filename)
    # except:
    #     pass

    try:
        os.rename(temp_filename, output_mzML)
    except:
        pass