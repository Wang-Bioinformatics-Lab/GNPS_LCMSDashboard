import sys
sys.path.insert(0, "..")
import xic
import pandas as pd
import ms2 
import download


def test_ms2_spectrum():
    usi = "mzspec:MSV000085852:QC_0:scan:1"
    remote_link, local_filename = download._resolve_usi(usi)
    peaks, mz, spectrum_details_string = ms2._get_ms2_peaks(usi, local_filename, 1)

    assert(len(peaks) > 10)

    usi = "mzspec:MSV000086709:peak/27_Walterinnesia_egyptia_Liverpool_unkown_red_2.mzXML"
    remote_link, local_filename = download._resolve_usi(usi)
    peaks, mz, spectrum_details_string = ms2._get_ms2_peaks(usi, local_filename, 1729)

    assert(len(peaks) > 10)

    # Currently Doesnt work, but will need to. TODO: Fix
    # usi = "mzspec:GNPS:TASK-f32283142ac34080ae737f3b2f1fa1c6-f.monicathukral/201204/P australis.mzXML:scan:501217"
    # remote_link, local_filename = download._resolve_usi(usi)
    # peaks, mz = ms2._get_ms2_peaks(usi, local_filename, 501217)

    # assert(len(peaks) > 10)