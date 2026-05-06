import requests
import os
import sys
from urllib.parse import quote, quote_plus


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
    
    # Pass id via params= so requests URL-encodes special chars (e.g. '+' → '%2B').
    # Interpolating raw lets MassIVE's tomcat decode '+' as space and silently mismatch.
    lookup_request = requests.get(
        'https://massive.ucsd.edu/ProteoSAFe/QuerySpectrum',
        params={'id': msv_usi},
        verify=False,  # massive frequently has TLS issues
    )

    try:
        resolution_json = lookup_request.json()

        remote_path = None

        potential_resolutions = [resolution for resolution in resolution_json["row_data"]]

        # Prefer the resolution whose file_descriptor matches the requested USI path —
        # MassIVE sometimes returns unrelated rows when the exact match fails.
        requested_path = usi_splits[2] if len(usi_splits) >= 3 else ""

        def _pick(resolutions):
            if not resolutions:
                return None
            for r in resolutions:
                fd = r.get("file_descriptor", "")
                if requested_path and fd.endswith("/" + requested_path):
                    return fd
            return resolutions[0]["file_descriptor"]

        mzML_resolutions = [resolution for resolution in potential_resolutions if os.path.splitext(resolution["file_descriptor"])[1] == ".mzML"]
        mzXML_resolutions = [resolution for resolution in potential_resolutions if os.path.splitext(resolution["file_descriptor"])[1] == ".mzXML"]
        raw_resolutions = [resolution for resolution in potential_resolutions if os.path.splitext(resolution["file_descriptor"])[1].lower() == ".raw"]

        if len(mzML_resolutions) > 0:
            remote_path = _pick(mzML_resolutions)
        elif len(mzXML_resolutions) > 0:
            remote_path = _pick(mzXML_resolutions)
        elif len(raw_resolutions) > 0:
            remote_path = _pick(raw_resolutions)

        # Format into FTP link, we are deprecating FTP
        # remote_link = f"ftp://massive.ucsd.edu/{remote_path[2:]}"

        # Format into HTTPS
        fileparameter = quote(remote_path)
        #remote_link = f"https://massive.ucsd.edu/ProteoSAFe/DownloadResultFile?forceDownload=true&file={fileparameter}"

        # We will use the massive proxy when downloading via HTTPS
        remote_link = f"https://massiveproxy.gnps2.org/massiveproxy/{fileparameter[2:]}"
    except:
        # We did not successfully look it up, this is the fallback try
        if force_massive:
            #return f"ftp://massive.ucsd.edu/{usi_splits[1]}/{usi_splits[2]}"
            fileparameter = quote(f"f.{usi_splits[1]}/{usi_splits[2]}")
            #remote_link = f"https://massive.ucsd.edu/ProteoSAFe/DownloadResultFile?forceDownload=true&file={fileparameter}"

            # We will use the massive proxy when downloading via HTTPS
            remote_link = f"https://massiveproxy.gnps2.org/massiveproxy/{fileparameter[2:]}"
        else:
            raise

    print(remote_link)
    return remote_link