
import sys
sys.path.insert(0, "..")
import xic
import lcms_map
import pandas as pd
import utils
import tic
import ms2 
import download


# def test_scan_in_usi():
#     usi = "mzspec:PXD023650:03552_GA1_P_041575_P00_A00_30min_R1.raw"
#     remote_link = download._resolve_usi_remotelink(usi)
#     print(remote_link)

#     remote_link, local_filename = download._resolve_usi(usi, cleanup=False)
#     print(remote_link, local_filename)

# def test_chromatograms():
#     local_filename = "std1_022721.mzML"
#     chrom_list = xic.chromatograms_list(local_filename)
#     xic_df = xic.get_chromatogram(local_filename, chrom_list[0])

#     print(xic_df)

def test_agilent():
    remote_link, local_filename = download._resolve_usi("mzspec:MSV000084060:KM0001")
    agg_dict, msn_results = lcms_map._aggregate_lcms_map(local_filename, 0, 300, 0, 2000)
    lcms_map._create_map_fig(agg_dict, msn_results)
    