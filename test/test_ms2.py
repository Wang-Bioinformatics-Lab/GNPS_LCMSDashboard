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
    usi = "mzspec:MSV000086995:updates/2021-04-01_mwang87_a4ef53e6/peak/wash_initial.mzML"
    remote_link, local_filename = download._resolve_usi(usi)
    peaks, mz, spectrum_details_string = ms2._get_ms2_peaks(usi, local_filename, 527060)
    assert(len(peaks) > 10)

def test_ms1_selection_spectrum():
    usi = "mzspec:MSV000086521:raw/ORSL13CM.CDF"
    remote_link, local_filename = download._resolve_usi(usi)
    closest_scan = ms2.determine_scan_by_rt(usi, local_filename, 12.83)

    print("closest_scan", closest_scan)

    assert(int(closest_scan) > 0)

    peaks, mz, spectrum_details_string = ms2._get_ms2_peaks(usi, local_filename, 764)

    assert(len(peaks) > 10)

    





