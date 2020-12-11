import pymzml
import time
import os
from tqdm import tqdm
from pymzml_cython import read_mzml_cython
import pandas as pd

FILENAME = "../temp/ftp_massive.ucsd.edu_MSV000084494_ccms_peak_raw_GNPS00002_A3_p.mzML"
#FILENAME = "../temp/ftp_massive.ucsd.edu_MSV000084951_ccms_peak_AH22.mzML"
#FILENAME = "../temp/ftp_massive.ucsd.edu_MSV000079514_ccms_peak_CD4_Tcells_LTQ-Orbitrap_Elite_28_Adult_CD4Tcells_bRP_Elite_28_f01.mzML"

def test_pymzml_read_python():
    run = pymzml.run.Reader(FILENAME)

    for spec in tqdm(run):
        if spec.ms_level == 1:
            rt = spec.scan_time_in_minutes()
            peaks = spec.reduce(mz_range=(0, 2000))

            # Sorting by intensity
            peaks = peaks[peaks[:,1].argsort()]
            peaks = peaks[-100:]

            mz, intensity = zip(*peaks)

def test_pymzml_read_cython():
    read_mzml_cython.read_pymzml_cython(FILENAME)

def test_msaccess():
    cmd = 'time ./bin/msaccess -x "slice mz=300,400 rt=120,180" --filter="msLevel 1" --filter="threshold count 100 most-intense" "{}"'.format(FILENAME)
    print(cmd)
    os.system(cmd)

def main():
    # PYTHON

    start_time = time.time()

    test_pymzml_read_python()

    end_time = time.time()

    elapsed_time = end_time-start_time
    
    print("Python", elapsed_time)


    # # CYTHON

    # start_time = time.time()

    # test_pymzml_read_cython()

    # end_time = time.time()

    # elapsed_time = end_time-start_time
    
    # print("Cython", elapsed_time)

    # CYTHON
    start_time = time.time()

    test_msaccess()

    end_time = time.time()

    elapsed_time = end_time-start_time
    
    print("MSaccess", elapsed_time)


if __name__ == '__main__':
    main()
