import sys
sys.path.insert(0, "..")
import xic
import pandas as pd
import download
import os

def test_resolve():
    df = pd.read_csv("usi_list.tsv", sep='\t')
    for record in df.to_dict(orient="records"):
        print(record["usi"])
        remote_link, local_filename = download._resolve_usi(record["usi"])

        assert(os.path.exists(local_filename))
        

def test_resolve_filename():
    df = pd.read_csv("usi_list.tsv", sep='\t')
    for record in df.to_dict(orient="records"):
        converted_filename = download._usi_to_local_filename(record["usi"])
        print(record["usi"], converted_filename)
    