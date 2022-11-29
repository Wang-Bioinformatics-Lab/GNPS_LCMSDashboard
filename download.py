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

from download_msv import _resolve_msv_usi
from download_workbench import _resolve_metabolomicsworkbench_usi

def _get_usi_display_filename(usi):
    usi_splits = usi.split(":")

    return os.path.basename(usi_splits[2])

def _usi_to_local_filename(usi):
    """
        This returns the converted filename
    """
    usi_splits = usi.split(":")

    converted_local_filename = ""

    if "LOCAL" in usi_splits[1]:
        converted_local_filename = werkzeug.utils.secure_filename(":".join(usi_splits[:3]))
        filename, file_extension = os.path.splitext(converted_local_filename)
        converted_local_filename = filename + ".mzML"
    
    elif "MSV" in usi_splits[1]:
        converted_local_filename = werkzeug.utils.secure_filename(":".join(usi_splits[:3])) + ".mzML"
        converted_local_filename =  converted_local_filename.replace(".mzML.mzML", ".mzML")

    elif "GNPS" in usi_splits[1]:
        if "TASK-" in usi_splits[2]:
            converted_local_filename = werkzeug.utils.secure_filename(":".join(usi_splits[:3]))
            filename, file_extension = os.path.splitext(converted_local_filename)
            converted_local_filename = filename + ".mzML"
        elif "QUICKSTART-" in usi_splits[2]:
            converted_local_filename = werkzeug.utils.secure_filename(":".join(usi_splits[:3]))
            filename, file_extension = os.path.splitext(converted_local_filename)
            converted_local_filename = filename + ".mzML"
        elif "GNPS" in usi_splits[2] and "accession" in usi_splits[3]:
            converted_local_filename =  werkzeug.utils.secure_filename(":".join(usi_splits[:5])) + ".mzML"

    elif "MTBLS" in usi_splits[1]:
        converted_local_filename = werkzeug.utils.secure_filename(":".join(usi_splits[:3]))
        filename, file_extension = os.path.splitext(converted_local_filename)
        converted_local_filename = filename + ".mzML"

    elif "ST" in usi_splits[1]:
        converted_local_filename = werkzeug.utils.secure_filename(":".join(usi_splits[:3]))
        filename, file_extension = os.path.splitext(converted_local_filename)
        converted_local_filename = filename + ".mzML"

    elif "PXD" in usi_splits[1]:
        converted_local_filename = werkzeug.utils.secure_filename(":".join(usi_splits[:3])) + ".mzML"
        converted_local_filename = converted_local_filename.replace(".mzML.mzML", ".mzML")

    # Cleaning it up
    if len(converted_local_filename) > 250:
        converted_local_filename = "convertedfile_" + str(hash(converted_local_filename)) + "_" + converted_local_filename[-150:]

    return converted_local_filename


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

        # TODO: update this to the API
        remote_link = "ftp://ccms-ftp.ucsd.edu/GNPS_Library_Provenance/{}/{}".format(task, source_file)

    return remote_link

def _resolve_mtbls_usi(usi):
    usi_splits = usi.split(':')

    dataset_accession = usi_splits[1]
    filename = usi_splits[2]
    
    # FTP Deprecated
    #remote_link = "ftp://ftp.ebi.ac.uk/pub/databases/metabolights/studies/public/{}/{}".format(dataset_accession, filename)
    
    # HTTPS Download
    # Getting obfuscation code
    r = requests.get("https://www.ebi.ac.uk/metabolights/ws/studies/{}/files?include_raw_data=false".format(dataset_accession))
    obfuscation_code = r.json()["obfuscationCode"]
    remote_link = "https://www.ebi.ac.uk/metabolights/ws/studies/{}/download/{}?file={}".format(dataset_accession, obfuscation_code, filename)

    return remote_link

def _resolve_glycopost_usi(usi):
    usi_splits = usi.split(':')
    dataset_accession = usi_splits[1]

    # Making adding the revision if its not in the accession
    if not "." in dataset_accession:
        dataset_accession = dataset_accession + ".0"

    filename = usi_splits[2]
    remote_link = "https://glycopost.glycosmos.org/data/{}/{}".format(dataset_accession, urllib.parse.quote(filename))

    return remote_link

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
                remote_link = filename_object["value"].replace("ftp://", "https://")

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

    resource = ""
    
    if "MSV" in usi_splits[1]:
        remote_link = _resolve_msv_usi(usi, force_massive=True)
        resource = "MASSIVEDATASET"
    elif "GNPS" in usi_splits[1]:
        remote_link = _resolve_gnps_usi(usi)
        resource = "GNPSTASK"
    elif "MassIVE" in usi_splits[1]: # MassIVE Task data
        remote_link = _resolve_gnps_usi(usi)
        resource = "MASSIVETASK"
    elif "MTBLS" in usi_splits[1]:
        remote_link = _resolve_mtbls_usi(usi)
        resource = "METABOLIGHTS"
    elif "GPST" in usi_splits[1]:
        remote_link = _resolve_glycopost_usi(usi)
        resource = "GLYCOPOST"
    elif "ST" in usi_splits[1]:
        remote_link = _resolve_metabolomicsworkbench_usi(usi)
        resource = "METABOLOMICSWORKBENCH"
    elif "PXD" in usi_splits[1]:
        # First lets try resolving it at MSV
        remote_link = ""
        try:
            remote_link = _resolve_msv_usi(usi)
        except:
            pass
            
        resource = "PROTEOMEXCHANGE"
        
        if len(remote_link) == 0:
            remote_link = _resolve_pxd_usi(usi)
    else:
        remote_link = ""

    return remote_link, resource

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
        # TODO: Update this so it works
        msv_url = _resolve_msv_usi(usi)
        msv_url = msv_url.replace("ftp://massive.ucsd.edu/", "")
        msv_url = msv_url.replace("https://massive.ucsd.edu/ProteoSAFe/DownloadResultFile?forceDownload=true&file=", "")

        return "f.{}".format(msv_url)

    if "GNPS" in usi_splits[1]:
        if "TASK-" in usi_splits[2]:
            return "-".join(usi_splits[2].split("-")[2:])
        elif "QUICKSTART-" in usi_splits[2]:
            return None
        elif "GNPS" in usi_splits[2] and "accession" in usi_splits[3]:
            return None

    if "MTBLS" in usi_splits[1]:
        return None

    if "ST" in usi_splits[1]:
        st_url = _resolve_metabolomicsworkbench_usi(usi)
        st_url = st_url.replace("ftp://massive.ucsd.edu/", "")
        st_url = st_url.replace("https://massive.ucsd.edu/ProteoSAFe/DownloadResultFile?forceDownload=true&file=", "")

        return "f.{}".format(st_url)

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
def _resolve_usi(usi, temp_folder="temp", cleanup=True):
    """
    This code attempts to resolve the USI and make sure the files are converted to open formats

    Args:
        usi ([type]): [description]
        temp_folder (str, optional): [description]. Defaults to "temp".
        cleanup (bool, optional): [description]. Defaults to True.

    Returns:
        string: remote_link to refer where the file came from
        string: local path of the converted filename
    """    

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
            if file_extension.lower() == ".cdf":
                _convert_cdf_to_mzML(local_filename, temp_filename)
            elif file_extension.lower() == ".raw":
                _convert_raw_to_mzML(local_filename, temp_filename)
            else:
                _convert_mzML(local_filename, temp_filename)

            os.rename(temp_filename, converted_local_filename)

            # Cleanup
            try:
                if local_filename != converted_local_filename and cleanup:
                    os.remove(local_filename)
            except:
                pass

        return "", converted_local_filename

    remote_link, resource_name = _resolve_usi_remotelink(usi)

    # Getting Data Local, TODO: likely should serialize it
    local_filename = os.path.join(temp_folder, "temp_" + str(uuid.uuid4()) + "_" + werkzeug.utils.secure_filename(remote_link)[-150:])
    filename, file_extension = os.path.splitext(local_filename)

    temp_filename = os.path.join(temp_folder, str(uuid.uuid4()) + file_extension)
    
    if resource_name == "GLYCOPOST":
        wget_cmd = "wget '{}' --referer '{}' -O {} --no-check-certificate 2> /dev/null".format(remote_link, remote_link, temp_filename)
    elif "https://ftp.pride.ebi.ac.uk/" in remote_link:
        # We are getting it from PRIDE, so lets try to do it in parallel
        wget_cmd = "lftp -e 'pget -n 15 -c \"{}\" -o {};; exit'".format(remote_link, temp_filename)
    else:
        wget_cmd = "wget '{}' --referer '{}' -O {} 2> /dev/null".format(remote_link, remote_link, temp_filename)
    
    # DEBUG COMMAND
    print("DOWNLOAD WGET CMD", wget_cmd, file=sys.stderr, flush=True)
    
    os.system(wget_cmd)
    os.rename(temp_filename, local_filename)

    temp_filename = os.path.join(temp_folder, str(uuid.uuid4()) + ".mzML")
    # Lets do a conversion
    # TODO: Setting timeouts to kill child processes
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
        if local_filename != converted_local_filename and cleanup:
            os.remove(local_filename)
    except:
        pass

    return remote_link, converted_local_filename


def _convert_raw_to_mzML(input_raw, output_mzML, cleanup=True):
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

    # Cleaning up
    if thermo_converted_filename != output_mzML and cleanup:
        os.remove(thermo_converted_filename)


# First try msconvert, if the output fails, then we will do pyteomics to mzML and then msconvert
def _convert_mzML(input_mzXML, output_mzML):
    """
    This will convert mzXML and mzML to mzML
    """

    # These are old versions of the convert
    #conversion_cmd = "export LC_ALL=C && ./bin/msconvert {} --mzML --32 --outfile {} --outdir {} --filter 'threshold count 500 most-intense' --filter 'msLevel 1' --filter 'MS2Denoise 0 4000'".format(input_mzXML, output_mzML, os.path.dirname(output_mzML))
    #conversion_cmd = "export LC_ALL=C && ./bin/msconvert {} --mzML --32 --outfile {} --outdir {} --filter 'threshold count 500 most-intense' --filter 'MS2Denoise 0 4000'".format(input_mzXML, output_mzML, os.path.dirname(output_mzML))
    #conversion_cmd = "export LC_ALL=C && ./bin/msconvert {} --mzML --32 --outfile {} --outdir {} --filter 'threshold count 500 most-intense'".format(input_mzXML, output_mzML, os.path.dirname(output_mzML))
    #conversion_cmd = "export LC_ALL=C && ./bin/msconvert {} --mzML --32 --outfile {} --outdir {}".format(input_mzXML, output_mzML, os.path.dirname(output_mzML))

    conversion_cmd = "export LC_ALL=C && ./bin/msconvert {} --mzML --32 --outfile {} --outdir {} --filter 'threshold absolute 1 most-intense' --filter 'msLevel 1-4'".format(input_mzXML, output_mzML, os.path.dirname(output_mzML))

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
    scan_indcs = list(zip(scan_values, scan_end_values))

    # Writing everything out
    with MzMLWriter(open(temp_filename, 'wb')) as out:
        out.controlled_vocabularies()
        with out.run(id="my_analysis"):
            with out.spectrum_list(count=len(scan_indcs)):
                # Iterating through all scans in the reader
                try:
                    # reading through scans
                    for i, scan_range in enumerate(scan_indcs):
                        time_min_rt = time_values[i] / 60

                        _mz_array = np.array(mass_values[scan_range[0]:scan_range[1]])
                        _i_array = np.array(intensity_values[scan_range[0]:scan_range[1]])
                        
                        out.write_spectrum(
                            _mz_array, _i_array,
                            id="scan={}".format(i), params=[
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

