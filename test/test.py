import sys
sys.path.insert(0, "..")
import xic
import lcms_map
import pandas as pd
import utils

def test_slow():
    all_xic_values = [["278.1902", 278.1902]]
    xic_tolerance = 0.5
    xic_ppm_tolerance = 10
    xic_tolerance_unit = "Da"
    rt_min = 5
    rt_max = 6
    polarity_filter = "Positive"

    xic._xic_file_slow("QC_0.mzML", all_xic_values, xic_tolerance, xic_ppm_tolerance, xic_tolerance_unit, rt_min, rt_max, polarity_filter)
    
def test_fast():
    all_xic_values = [["278.1902", 278.1902]]
    xic_tolerance = 0.5
    xic_ppm_tolerance = 10
    xic_tolerance_unit = "Da"
    rt_min = 5
    rt_max = 6
    polarity_filter = "Positive"

    xic._xic_file_fast("QC_0.mzML", all_xic_values, xic_tolerance, xic_ppm_tolerance, xic_tolerance_unit, rt_min, rt_max, polarity_filter)

def test_2d_mapping():
    lcms_map._create_map_fig("QC_0.mzML")

def test_scan_in_usi():
    usi = "mzspec:MSV000085852:QC_0:scan:3548"
    remote_link, local_filename = utils._resolve_usi(usi)
    current_map_selection, highlight_box = utils._resolve_map_plot_selection(None, usi)

    import sys
    print(current_map_selection, highlight_box, file=sys.stderr)

def test_resolve():
    df = pd.read_csv("usi_list.tsv", sep='\t')
    for record in df.to_dict(orient="records"):
        utils._resolve_usi(record["usi"])