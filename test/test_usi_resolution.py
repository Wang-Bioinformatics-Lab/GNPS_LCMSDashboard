import sys
import os
sys.path.insert(0, "..")
import pandas as pd

import xic
import download
import lcms_map

# Testing remote link calculation
def test_resolve_remote_url():
    df = pd.read_csv("usi_list.tsv", sep='\t')
    for record in df.to_dict(orient="records"):
        print(record["usi"])
        remote_link, resource_name = download._resolve_usi_remotelink(record["usi"])
        print("RESOLVED URL", remote_link, resource_name)
        assert(len(remote_link) > 0)

# Testing conversion
def test_resolve_download_convert():
    df = pd.read_csv("usi_list.tsv", sep='\t')
    for record in df.to_dict(orient="records"):
        print(record["usi"])
        remote_link, local_filename = download._resolve_usi(record["usi"])

        assert(os.path.exists(local_filename))

# Testing we can make a feather file
def test_feather_download_convert():
    df = pd.read_csv("usi_list.tsv", sep='\t')
    for record in df.to_dict(orient="records"):
        print(record["usi"])
        remote_link, local_filename = download._resolve_usi(record["usi"])
        output_ms1_filename, output_msn_filename = lcms_map._get_feather_filenames(local_filename)
        lcms_map._save_lcms_data_feather(local_filename)

        # Making sure the filename exists
        assert(os.path.exists(output_ms1_filename))

        # Making sure it includes polarity
        ms1_results = pd.read_feather(output_ms1_filename)
        assert("polarity" in ms1_results)
        

# Testing to local filenames
def test_resolve_filename():
    df = pd.read_csv("usi_list.tsv", sep='\t')
    for record in df.to_dict(orient="records"):
        converted_filename = download._usi_to_local_filename(record["usi"])
        print(record["usi"], converted_filename)

