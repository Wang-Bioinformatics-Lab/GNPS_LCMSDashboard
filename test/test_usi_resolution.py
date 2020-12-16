import sys
sys.path.insert(0, "..")
import xic
import pandas as pd
import utils

def test_resolve():
    df = pd.read_csv("usi_list.tsv", sep='\t')
    for record in df.to_dict(orient="records"):
        print(record["usi"])
        remote_link, local_filename = utils._resolve_usi(record["usi"])
        lcms_map._create_map_fig(local_filename)