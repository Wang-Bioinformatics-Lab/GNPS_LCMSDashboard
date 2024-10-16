
import sys
sys.path.insert(0, "..")
import xic
import pandas as pd
import download
import time
import lcms_map
import tic
import os

####################################
# XIC Tests
####################################
def test_xic_metabolomics_fast():
    remote_link, local_filename = download._resolve_usi("mzspec:MSV000085852:QC_0")

    all_xic_values = [["278.1902", 278.1902]]
    xic_tolerance = 0.5
    xic_ppm_tolerance = 10
    xic_tolerance_unit = "Da"
    rt_min = 5
    rt_max = 6
    polarity_filter = "Positive"

    xic._xic_file_fast(local_filename, all_xic_values, xic_tolerance, xic_ppm_tolerance, xic_tolerance_unit, rt_min, rt_max, polarity_filter)


def test_xic_metabolomics_slow():
    remote_link, local_filename = download._resolve_usi("mzspec:MSV000085852:QC_0")

    all_xic_values = [["278.1902", 278.1902]]
    xic_tolerance = 0.5
    xic_ppm_tolerance = 10
    xic_tolerance_unit = "Da"
    rt_min = 5
    rt_max = 6
    polarity_filter = "Positive"

    xic._xic_file_slow(local_filename, all_xic_values, xic_tolerance, xic_ppm_tolerance, xic_tolerance_unit, rt_min, rt_max, polarity_filter)

def test_xic_proteomics_fast():
    remote_link, local_filename = download._resolve_usi("mzspec:MSV000079514:Adult_CD4Tcells_bRP_Elite_28_f01")

    all_xic_values = [["1040.057006835938", 1040.057006835938]]
    xic_tolerance = 0.5
    xic_ppm_tolerance = 10
    xic_tolerance_unit = "Da"
    rt_min = 0
    rt_max = 100000
    polarity_filter = "Positive"
    
    xic._xic_file_fast(local_filename, all_xic_values, xic_tolerance, xic_ppm_tolerance, xic_tolerance_unit, rt_min, rt_max, polarity_filter)

def test_xic_proteomics_slow():
    remote_link, local_filename = download._resolve_usi("mzspec:MSV000079514:Adult_CD4Tcells_bRP_Elite_28_f01")

    all_xic_values = [["1040.057006835938", 1040.057006835938]]
    xic_tolerance = 0.5
    xic_ppm_tolerance = 10
    xic_tolerance_unit = "Da"
    rt_min = 0
    rt_max = 100000
    polarity_filter = "Positive"
    
    xic._xic_file_slow(local_filename, all_xic_values, xic_tolerance, xic_ppm_tolerance, xic_tolerance_unit, rt_min, rt_max, polarity_filter)


####################################
# TIC Tests
####################################




####################################
# 2D Map Tests
####################################
def test_2dmap_metabolomics():
    remote_link, local_filename = download._resolve_usi("mzspec:MSV000085852:QC_0")
    lcms_map._create_map_fig(local_filename)

def test_2dmap_metabolomics_data():
    remote_link, local_filename = download._resolve_usi("mzspec:MSV000085852:QC_0")
    
    min_rt = 0
    max_rt = 1000000
    min_mz = 0
    max_mz = 2000

    lcms_map._gather_lcms_data(local_filename, min_rt, max_rt, min_mz, max_mz, polarity_filter="None")

def test_2dmap_metabolomics_zoomed():
    remote_link, local_filename = download._resolve_usi("mzspec:MSV000085852:QC_0")

    map_selection = {}
    map_selection["xaxis.range[0]"] = "3"
    map_selection["xaxis.range[1]"] = "5"

    map_selection["yaxis.range[0]"] = "200"
    map_selection["yaxis.range[1]"] = "750"

    lcms_map._create_map_fig(local_filename, map_selection=map_selection)

def test_2dmap_proteomics():
    remote_link, local_filename = download._resolve_usi("mzspec:MSV000079514:Adult_CD4Tcells_bRP_Elite_28_f01")

    lcms_map._create_map_fig(local_filename)

def test_2dmap_proteomics_data():
    remote_link, local_filename = download._resolve_usi("mzspec:MSV000079514:Adult_CD4Tcells_bRP_Elite_28_f01")
    
    min_rt = 0
    max_rt = 1000000
    min_mz = 0
    max_mz = 2000

    lcms_map._gather_lcms_data(local_filename, min_rt, max_rt, min_mz, max_mz, polarity_filter="None")

def test_2dmap_proteomics_data2():
    remote_link, local_filename = download._resolve_usi("mzspec:MSV000083508:01308_H02_P013387_B00_N16_R1")
    
    min_rt = 0
    max_rt = 1000000
    min_mz = 0
    max_mz = 2000

    lcms_map._gather_lcms_data(local_filename, min_rt, max_rt, min_mz, max_mz, polarity_filter="None")

def test_2dmap_proteomics_zoomed():
    remote_link, local_filename = download._resolve_usi("mzspec:MSV000079514:Adult_CD4Tcells_bRP_Elite_28_f01")

    map_selection = {}
    map_selection["xaxis.range[0]"] = "10"
    map_selection["xaxis.range[1]"] = "15"

    map_selection["yaxis.range[0]"] = "500"
    map_selection["yaxis.range[1]"] = "1000"

    lcms_map._create_map_fig(local_filename, map_selection=map_selection)