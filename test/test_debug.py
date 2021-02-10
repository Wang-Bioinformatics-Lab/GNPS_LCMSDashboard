
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
    usi = "mzspec:MSV000086838:peak/ST001652/10_D6_CT1.mzXML"
    remote_link, local_filename = download._resolve_usi(usi, cleanup=False)

    print(remote_link, local_filename)