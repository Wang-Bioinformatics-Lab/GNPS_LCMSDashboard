import pandas as pd
import requests
import uuid
import werkzeug
from scipy import integrate
import os
import sys
import pymzml

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

            remote_link = "http://gnps.ucsd.edu/ProteoSAFe/DownloadResultFile?task={}&block=main&file={}".format(task, filename)
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
        conversion_cmd = "export LC_ALL=C && ./bin/msconvert {} --mzML --32 --outfile {} --outdir {} --filter 'threshold count 500 most-intense'".format(local_filename, temp_filename, os.path.dirname(temp_filename))
        os.system(conversion_cmd)

        os.rename(temp_filename, converted_local_filename)

        local_filename = converted_local_filename

    return remote_link, converted_local_filename

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

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        out = proc.communicate()[0]

        all_lines = str(out).replace("\\t", "\t").split("\\n")
        all_lines = [line for line in all_lines if len(line) > 10 ]
        updated_version = "\n".join(all_lines)
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
        raise

    
    return response_dict