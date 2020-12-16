import sys
sys.path.insert(0, "..")
import xic
import lcms_map
import pandas as pd
import utils
import tic
import ms2 




def test_tic():
    df = pd.read_csv("usi_list.tsv", sep='\t')
    for record in df.to_dict(orient="records"):
        print(record["usi"])
        remote_link, local_filename = utils._resolve_usi(record["usi"])
        tic._tic_file_slow(local_filename)

def test_url_parsing():
    params_string = '?xicmz=271.0315%3B278.1902%3B279.0909%3B285.0205%3B311.0805%3B314.1381&xic_formula=&xic_peptide=&xic_tolerance=0.5&xic_ppm_tolerance=10&xic_tolerance_unit=Da&xic_rt_window=&xic_norm=False&xic_file_grouping=FILE&xic_integration_type=AUC&show_ms2_markers=True&ms2_identifier=None&show_lcms_2nd_map=False&map_plot_zoom=%7B%22xaxis.range%5B0%5D%22%3A+3.225196497160058%2C+%22xaxis.range%5B1%5D%22%3A+3.4834247492797554%2C+%22yaxis.range%5B0%5D%22%3A+521.8432333663449%2C+%22yaxis.range%5B1%5D%22%3A+615.6041749343235%7D&polarity_filtering=None&polarity_filtering2=None&tic_option=TIC&overlay_usi=None&overlay_mz=row+m%2Fz&overlay_rt=row+retention+time&overlay_color=&overlay_size=&feature_finding_type=Off'

    param_value = utils._get_param_from_url(params_string, "#", "map_plot_zoom", "{}")
    print(param_value)

    current_map_selection, highlight_box = utils._resolve_map_plot_selection(params_string, "")
    print(current_map_selection)


def test_scan_in_usi():
    usi = "mzspec:MSV000085852:QC_0:scan:3548"
    remote_link, local_filename = utils._resolve_usi(usi)
    current_map_selection, highlight_box = utils._resolve_map_plot_selection(None, usi)

    import sys
    print(current_map_selection, highlight_box, file=sys.stderr)

def test_ms2_spectrum():
    usi = "mzspec:MSV000085852:QC_0:scan:1"
    remote_link, local_filename = utils._resolve_usi(usi)
    peaks, mz = ms2._get_ms2_peaks(usi, 1)

    assert(len(peaks) > 10)

    usi = "mzspec:GNPS:TASK-f32283142ac34080ae737f3b2f1fa1c6-f.monicathukral/201204/P australis.mzXML:scan:501217"
    remote_link, local_filename = utils._resolve_usi(usi)
    peaks, mz = ms2._get_ms2_peaks(usi, 501217)

    assert(len(peaks) > 10)
