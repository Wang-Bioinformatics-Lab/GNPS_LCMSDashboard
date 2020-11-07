import sys
sys.path.insert(0, "..")
import xic

def test_slow():
    all_xic_values = [["278.1902", 278.1902]]
    xic_tolerance = 0.5
    xic_ppm_tolerance = 10
    xic_tolerance_unit = "Da"
    rt_min = 0
    rt_max = 1000
    polarity_filter = "Positive"

    xic._xic_file_slow("QC_0.mzML", all_xic_values, xic_tolerance, xic_ppm_tolerance, xic_tolerance_unit, rt_min, rt_max, polarity_filter)
    
def test_fast():
    all_xic_values = [["278.1902", 278.1902]]
    xic_tolerance = 0.5
    xic_ppm_tolerance = 10
    xic_tolerance_unit = "Da"
    rt_min = 0
    rt_max = 1000
    polarity_filter = "Positive"
    
    xic._xic_file_fast("QC_0.mzML", all_xic_values, xic_tolerance, xic_ppm_tolerance, xic_tolerance_unit, rt_min, rt_max, polarity_filter)