
import sys
sys.path.insert(0, "..")
import xic
import lcms_map
import pandas as pd
import utils
import tic
import ms2 
import download

import datashader as ds


# def test_scan_in_usi():
#     usi = "mzspec:PXD023650:03552_GA1_P_041575_P00_A00_30min_R1.raw"
#     remote_link = download._resolve_usi_remotelink(usi)
#     print(remote_link)

#     remote_link, local_filename = download._resolve_usi(usi, cleanup=False)
#     print(remote_link, local_filename)

def test():
    usi = "mzspec:MSV000085852:QC_0:scan:3548"
    remote_link, local_filename = download._resolve_usi(usi)

    all_xic_values = [["278.1902", 278.1902]]
    xic_tolerance = 0.5
    xic_ppm_tolerance = 10
    xic_tolerance_unit = "Da"
    rt_min = 2
    rt_max = 8
    polarity_filter = "Positive"

    xic_df, ms2_data = xic._xic_file_slow(local_filename, all_xic_values, xic_tolerance, xic_ppm_tolerance, xic_tolerance_unit, rt_min, rt_max, polarity_filter)
    xic_df["i"] = xic_df["XIC 278.1902"]
    xic_df["USI"] = 1
    
    cvs = ds.Canvas(plot_width=100, plot_height=1)
    agg = cvs.points(xic_df,'rt','USI', agg=ds.sum("i"))

    import plotly.express as px

    fig = px.imshow(agg, origin='lower', y=[usi], labels={'color':'Log10(abundance)'}, height=600, template="plotly_white")
    fig.write_image("test.png")
    #print(agg.to_dict())


def test_agilent():
    remote_link, local_filename = download._resolve_usi("mzspec:MSV000084060:KM0001")
    agg_dict, msn_results = lcms_map._aggregate_lcms_map(local_filename, 0, 300, 0, 2000)
    lcms_map._create_map_fig(agg_dict, msn_results)
    
def test_cdf():
    remote_link, local_filename = download._resolve_usi("mzspec:MSV000086834:raw/20210210 GNPS LMCS/PA1MeOH1.aia.CDF")
    agg_dict, msn_results = lcms_map._aggregate_lcms_map(local_filename, 0, 100000, 0, 2000)
    lcms_map._create_map_fig(agg_dict, msn_results)
    print(local_filename)