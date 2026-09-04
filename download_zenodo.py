def _resolve_zenodo_usi(usi):
    usi_splits = usi.split(':')
    # Example: mzspec:ZENODO-4989929:T2.zip-T2/T2_lysate_ETHCD_1D_2.raw

    dataset_accession = usi_splits[1]
    dataset_accession = dataset_accession.replace("ZENODO-", "")
    filename = usi_splits[2]

    if ".zip-" in filename:
        # The file lives inside a zip; the resolvable resource is the zip itself.
        filename = filename.split(".zip-")[0] + ".zip"

    return "https://zenodo.org/api/records/{}/files/{}/content".format(dataset_accession, filename)
