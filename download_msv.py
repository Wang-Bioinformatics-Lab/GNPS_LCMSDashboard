import requests
import os
import sys


def _resolve_msv_usi(usi, force_massive=False):
    """

    Args:
        usi ([type]): [description]
        force_massive (bool, optional): [description]. Defaults to False. This is to force the url in massive even is the USI resolver from MassIVE didn't return successfully, mostly the case in CDF files

    Returns:
        [type]: [description]
    """

    usi_splits = usi.split(':')

    msv_usi = usi
    if len(usi.split(":")) == 3:
        msv_usi = "{}:scan:1".format(usi)
    
    lookup_url = f'https://massive.ucsd.edu/ProteoSAFe/QuerySpectrum?id={msv_usi}'
    lookup_request = requests.get(lookup_url)

    try:
        resolution_json = lookup_request.json()

        remote_path = None

        potential_resolutions = [resolution for resolution in resolution_json["row_data"]]
        
        mzML_resolutions = [resolution for resolution in potential_resolutions if os.path.splitext(resolution["file_descriptor"])[1] == ".mzML"]
        mzXML_resolutions = [resolution for resolution in potential_resolutions if os.path.splitext(resolution["file_descriptor"])[1] == ".mzXML"]
        raw_resolutions = [resolution for resolution in potential_resolutions if os.path.splitext(resolution["file_descriptor"])[1].lower() == ".raw"]

        if len(mzML_resolutions) > 0:
            remote_path = mzML_resolutions[0]["file_descriptor"]
        elif len(mzXML_resolutions) > 0:
            remote_path = mzXML_resolutions[0]["file_descriptor"]
        elif len(raw_resolutions) > 0:
            remote_path = raw_resolutions[0]["file_descriptor"]

        # Format into FTP link, we are deprecating FTP
        # remote_link = f"ftp://massive.ucsd.edu/{remote_path[2:]}"

        # Format into HTTPS
        remote_link = f"https://massive.ucsd.edu/ProteoSAFe/DownloadResultFile?forceDownload=true&file={remote_path}"
    except:
        # We did not successfully look it up, this is the fallback try
        if force_massive:
            #return f"ftp://massive.ucsd.edu/{usi_splits[1]}/{usi_splits[2]}"
            remote_link = f"https://massive.ucsd.edu/ProteoSAFe/DownloadResultFile?forceDownload=true&file=f.{usi_splits[1]}/{usi_splits[2]}"
        else:
            raise

    print(remote_link)
    return remote_link