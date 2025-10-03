import os
from remotezip import RemoteZip


def download_zenodo(usi, remote_link, output_filename):
    usi_splits = usi.split(':')
    # Example: mzspec:ZENODO-4989929:T2.zip-T2/T2_lysate_ETHCD_1D_2.raw

    dataset_accession = usi_splits[1]
    dataset_accession = dataset_accession.replace("ZENODO-", "")
    filename = usi_splits[2]

    if ".zip-" in filename:
        # we'll just get url to the zip filename
        zip_filename = filename.split(".zip-")[0] + ".zip"
        remote_link = "https://zenodo.org/api/records/{}/files/{}/content".format(dataset_accession, zip_filename)

        target_filename = filename.split(".zip-")[1]

        with RemoteZip(remote_link) as zip:
            for zip_info in zip.infolist():
                if zip_info.filename == target_filename:
                    #zip.extract(zip_info, output_filename) # not using because it makes nested folders
                    with open(output_filename, 'wb') as f:
                        file_content = zip.read(zip_info)
                        f.write(file_content)
                    break
    else:
        wget_cmd = "wget '{}' --referer '{}' -O {} --no-check-certificate 2> /dev/null".format(remote_link, remote_link, output_filename)

        os.system(wget_cmd)


def _resolve_zenodo_usi(usi):
    usi_splits = usi.split(':')
    # Example: mzspec:ZENODO-4989929:T2.zip-T2/T2_lysate_ETHCD_1D_2.raw

    dataset_accession = usi_splits[1]
    dataset_accession = dataset_accession.replace("ZENODO-", "")
    filename = usi_splits[2]

    if ".zip-" in filename:
        # we'll just get url to the zip filename
        filename = filename.split(".zip-")[0] + ".zip"

        remote_link = "https://zenodo.org/api/records/{}/files/{}/content".format(dataset_accession, filename)

    else:
        # we'll just get url to the zip filename
        remote_link = "https://zenodo.org/api/records/{}/files/{}/content".format(dataset_accession, filename)
    
    return remote_link
