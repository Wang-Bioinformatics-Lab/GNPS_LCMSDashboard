import sys
sys.path.insert(0, "..")
import xic
import lcms_map
import pandas as pd
import download


def test_2d_mapping():
    remote_link, local_filename = download._resolve_usi("mzspec:MSV000085852:QC_0")
    agg_dict, msn_results = lcms_map._aggregate_lcms_map(local_filename, 3, 7, 300, 500)
    lcms_map._create_map_fig(agg_dict, msn_results)

def test_2d_mapping_no_ms2():
    remote_link, local_filename = download._resolve_usi("mzspec:MSV000085852:QC_0")
    agg_dict, msn_results = lcms_map._aggregate_lcms_map(local_filename, 1, 2, 300, 500)
    lcms_map._create_map_fig(agg_dict, msn_results)

def test_2d_mapping_many():
    df = pd.read_csv("usi_list.tsv", sep='\t')
    for record in df.to_dict(orient="records"):
        print(record["usi"])
        remote_link, local_filename = download._resolve_usi(record["usi"])
        agg_dict, msn_results = lcms_map._aggregate_lcms_map(local_filename, 0, 300, 0, 2000)
        lcms_map._create_map_fig(agg_dict, msn_results)