import requests
import os
import sys
import shutil
from remotezip import RemoteZip

def _resolve_zenodo_usi(usi):
    """

    Args:
        usi ([type]): [description]
    Returns:
        [type]: [description]
    """

    usi_splits = usi.split(':')

    zenodo_id = usi_splits[1].replace("ZENODO", "").replace("-", "")
    
    zenodo_id = usi.split(":")[1].split("-")[-1]
    zip_filename = usi.split(":")[2].split("-")[1]
    ms_filename = usi.split(":")[2].split("-")[2]

    # Figuring out download path
    zenodo_url = "https://zenodo.org/api/records/{}".format(zenodo_id)
    r = requests.get(zenodo_url)
    all_files = r.json()['files']
    for file in all_files:
        #print(file['key'], zip_filename)
        if file['type'] == 'zip' and file['key'] == zip_filename:
            url = file['links']['self']
            with RemoteZip(url) as zip:
                for zip_info in zip.infolist():
                    actual_filename = zip_info.filename
                    #print(actual_filename, ms_filename)
                    if actual_filename == ms_filename:
                        with zip.open(actual_filename) as zf, open(output_filename, 'wb') as f:
                            shutil.copyfileobj(zf, f)

    return remote_link