
import sys
sys.path.insert(0, "..")
import xic
import lcms_map
import pandas as pd
import utils
import tic
import ms2 
import download

def test_chromatograms():
    local_filename = "std1_022721.mzML"
    chrom_list = xic.chromatograms_list(local_filename)
    xic_df = xic.get_chromatogram(local_filename, chrom_list[0])

    print(xic_df)

