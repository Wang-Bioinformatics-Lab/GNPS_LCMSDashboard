import sys
sys.path.insert(0, "..")
import xic
import pandas as pd
import download

def test_xic_slow():
    remote_link, local_filename = download._resolve_usi("mzspec:MSV000085852:QC_0")

    all_xic_values = [["278.1902", 278.1902]]
    xic_tolerance = 0.5
    xic_ppm_tolerance = 10
    xic_tolerance_unit = "Da"
    rt_min = 5
    rt_max = 6
    polarity_filter = "Positive"

    xic._xic_file_slow(local_filename, all_xic_values, xic_tolerance, xic_ppm_tolerance, xic_tolerance_unit, rt_min, rt_max, polarity_filter)
    
def test_xic_fast():
    remote_link, local_filename = download._resolve_usi("mzspec:MSV000085852:QC_0")

    all_xic_values = [["278.1902", 278.1902]]
    xic_tolerance = 0.5
    xic_ppm_tolerance = 10
    xic_tolerance_unit = "Da"
    rt_min = 5
    rt_max = 6
    polarity_filter = "Positive"

    xic._xic_file_fast(local_filename, all_xic_values, xic_tolerance, xic_ppm_tolerance, xic_tolerance_unit, rt_min, rt_max, polarity_filter)
