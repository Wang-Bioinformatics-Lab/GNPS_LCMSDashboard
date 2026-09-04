"""
USI -> remote URL resolution.

Trimmed to resolution only: the download, conversion and caching helpers that
used to live here were removed along with the dashboard. Nothing in this module
touches the filesystem or spawns a subprocess - it maps a USI to the URL its
data can be fetched from and returns it.
"""

import os
import urllib.parse

import requests

from download_msv import _resolve_msv_usi
from download_workbench import _resolve_metabolomicsworkbench_usi
import download_zenodo
import download_norman

# Upstream repositories are slow and occasionally hang outright. Every lookup is
# on a request path, so bound it: (connect, read).
HTTP_TIMEOUT = (3.05, 10)

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
        r = requests.get(url, timeout=HTTP_TIMEOUT)
        spectrum_dict = r.json()
        task = spectrum_dict["spectruminfo"]["task"]
        source_file = os.path.basename(spectrum_dict["spectruminfo"]["source_file"])

        # TODO: update this to the API
        remote_link = "ftp://ccms-ftp.ucsd.edu/GNPS_Library_Provenance/{}/{}".format(task, source_file)

    return remote_link

def _resolve_gnps2_usi(usi):
    usi_splits = usi.split(':')

    if "TASK-" in usi_splits[2]:
        # Test: mzspec:GNPS:TASK-de188599f53c43c3aaad95491743c784-spec/spec-00000.mzML:scan:31
        filename = "-".join(usi_splits[2].split("-")[2:])
        task = usi_splits[2].split("-")[1]

        remote_link = "https://gnps2.org/resultfile?task={}&file={}".format(task, urllib.parse.quote(filename))

    return remote_link


def _resolve_mtbls_usi(usi):
    usi_splits = usi.split(':')

    dataset_accession = usi_splits[1]
    filename = usi_splits[2]

    # The ws/studies/<id>/download endpoint is deprecated for public data (it now
    # returns 403 with a message pointing to the FTP mirror). Public study files
    # are served from EBI's FTP mirror over HTTPS - one GET per file, no auth.
    # urllib.parse.quote keeps "/" safe by default, so path separators pass through.
    remote_link = "https://ftp.ebi.ac.uk/pub/databases/metabolights/studies/public/{}/{}".format(dataset_accession, urllib.parse.quote(filename))

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
    lookup_request = requests.get(lookup_url, timeout=HTTP_TIMEOUT)
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
    elif "GNPS" == usi_splits[1]:
        remote_link = _resolve_gnps_usi(usi)
        resource = "GNPSTASK"
    elif "GNPS2" in usi_splits[1]:
        remote_link = _resolve_gnps2_usi(usi)
        resource = "GNPS2TASK"
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
    elif "ZENODO" in usi_splits[1]:
        remote_link = download_zenodo._resolve_zenodo_usi(usi)
        resource = "ZENODO"
    elif "NORMAN" in usi_splits[1]:
        remote_link = download_norman._resolve_norman_usi(usi)
        resource = "NORMAN"
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

