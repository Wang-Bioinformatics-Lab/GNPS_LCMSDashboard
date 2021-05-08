import sys
sys.path.insert(0, "..")
import pandas as pd
import utils

def test_overlay():
    udi = "mzspec:GNPS:TASK-ddd650381cef4bcfad4b068e9400c8d7-quantification_table_reformatted/"
    overlay_mz = ""
    overlay_rt = ""
    overlay_filter_column = ""
    overlay_filter_value = ""
    overlay_size = ""
    overlay_color = ""
    overlay_hover = ""
    overlay_df = utils._resolve_overlay(udi, overlay_mz, overlay_rt, overlay_filter_column, overlay_filter_value, overlay_size, overlay_color, overlay_hover)
    
    assert(len(overlay_df) > 100)
