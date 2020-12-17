import sys
sys.path.insert(0, "..")
import xic
import lcms_map
import pandas as pd
import download


def test_2d_mapping():
    remote_link, local_filename = download._resolve_usi("mzspec:MSV000085852:QC_0")
    lcms_map._create_map_fig(local_filename)

def test_resolve():
    df = pd.read_csv("usi_list.tsv", sep='\t')
    for record in df.to_dict(orient="records"):
        print(record["usi"])
        remote_link, local_filename = download._resolve_usi(record["usi"])
        lcms_map._create_map_fig(local_filename)