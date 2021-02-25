
import sys
sys.path.insert(0, "..")
import xic
import lcms_map
import pandas as pd
import utils
import tic
import ms2 
import download


def test_scan_in_usi():
    usi = "mzspec:PXD023650:03552_GA1_P_041575_P00_A00_30min_R1.raw"
    remote_link = download._resolve_usi_remotelink(usi)
    print(remote_link)

    remote_link, local_filename = download._resolve_usi(usi, cleanup=False)
    print(remote_link, local_filename)