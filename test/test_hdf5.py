import h5py
import pandas as pd
import pymzml
import sys
from tqdm import tqdm
import datashader as ds
import numpy as np
from dask import dataframe as dd

sys.path.insert(0, "..")
import lcms_map
from utils import _get_scan_polarity

FILENAME_PREFIX = "QC_0"
#FILENAME_PREFIX = "01308_H02_P013387_B00_N16_R1"

def test_write():
    print("X")

    # Converting mzML to our version of hdf5 with pandas
    all_mz = []
    all_rt = []
    all_i = []
    all_scan = []
    all_index = []
    all_polarity = []
    spectrum_index = 0
    number_spectra = 0

    all_ms2_mz = []
    all_ms2_rt = []
    all_ms2_scan = []

    all_ms3_mz = []
    all_ms3_rt = []
    all_ms3_scan = []

    run = pymzml.run.Reader("{}.mzML".format(FILENAME_PREFIX))

    # Iterating through all data with a custom scan iterator
    min_mz = 0
    max_mz = 2000
    import numpy as np

    for spec in tqdm(run):
        scan_polarity = _get_scan_polarity(spec)
        
        if spec.ms_level == 1:
            spectrum_index += 1

            number_spectra += 1
            rt = spec.scan_time_in_minutes()

            try:
                # Filtering peaks by mz
                if min_mz <= 0 and max_mz >= 2000:
                    peaks = spec.peaks("raw")
                else:
                    peaks = spec.reduce(mz_range=(min_mz, max_mz))

                # Filtering out zero rows
                peaks = peaks[~np.any(peaks < 1.0, axis=1)]

                # Sorting by intensity
                peaks = peaks[peaks[:,1].argsort()]

                mz, intensity = zip(*peaks)

                all_mz += list(mz)
                all_i += list(intensity)
                all_rt += len(mz) * [rt]
                all_scan += len(mz) * [spec.ID]
                all_index += len(mz) * [number_spectra]
                all_polarity += len(mz) * [scan_polarity]
            except:
                pass

    print(len(all_polarity))


    ms1_df = pd.DataFrame()
    ms1_df["ms1_mz"] = all_mz
    ms1_df["ms1_i"] = all_i
    ms1_df["ms1_rt"] = all_rt
    ms1_df["ms1_scan"] = all_scan 
    ms1_df["ms1_polarity"] = all_polarity

    ms1_df["ms1_mz"] = ms1_df["ms1_mz"].astype(np.dtype("float32"))
    ms1_df["ms1_i"] = ms1_df["ms1_i"].astype(np.dtype("float32"))
    ms1_df["ms1_rt"] = ms1_df["ms1_rt"].astype(np.dtype("float32"))
    ms1_df["ms1_scan"] = ms1_df["ms1_scan"].astype(np.dtype("int32"))

    print(ms1_df.dtypes)

    ms1_df.to_hdf("{}.h5".format(FILENAME_PREFIX), "ms1_df", format="table", data_columns=True)

    # Saving sqlite3
    import sqlite3
    db = sqlite3.connect("{}.sqlite".format(FILENAME_PREFIX))
    ms1_df.to_sql("ms1_df", db, if_exists="append")
    db.execute("CREATE INDEX mz_rt ON ms1_df(ms1_mz, ms1_rt)")
    db.execute("CREATE INDEX mz_rt_polarity ON ms1_df(ms1_mz, ms1_rt, ms1_polarity)") 
    
    #db.execute("CREATE INDEX ms1_rt ON ms1_df(ms1_rt)") 
    #db.execute("CREATE INDEX ms1_scan ON ms1_df(ms1_scan)") 
    #db.execute("CREATE INDEX ms1_polarity ON ms1_df(ms1_polarity)") 
    db.close()

    # with h5py.File('QC_0.mz5','r') as hf:
    #     Datasetnames=hf.keys()
    #     print(Datasetnames)
    #     print(hf["SpectrumMetaData"])
    # df = pd.read_hdf('QC_0.mz5', key="SpectrumMZ")
    # print(df.head())


def test_load_mzml():
    ms1_results, ms2_results, ms3_results = lcms_map._gather_lcms_data("{}.mzML".format(FILENAME_PREFIX), 1.0, 1.5, 300, 500, polarity_filter="Positive")

    ms1_df = pd.DataFrame(ms1_results)

    # width = 500
    # height = 500
    # cvs = ds.Canvas(plot_width=width, plot_height=height)
    # agg = cvs.points(ms1_df,'rt','mz', agg=ds.sum("i"))

    print(ms1_df)

def test_load_h5():
    ms1_df = pd.read_hdf("{}.h5".format(FILENAME_PREFIX), key="ms1_df", where=['ms1_rt>1.0', 'ms1_rt<1.5', 'ms1_mz<500', 'ms1_mz>300', 'ms1_polarity=Positive'], columns=["ms1_rt", "ms1_mz", "ms1_i"])
    #ms1_df = pd.read_hdf("{}.h5".format(FILENAME_PREFIX), "ms1_df", columns=["ms1_rt", "ms1_mz", "ms1_i"])

    #ms1_df = dd.from_pandas(ms1_df, npartitions=4)
    #ms1_df.persist()


    width = 500
    height = 500
    cvs = ds.Canvas(plot_width=width, plot_height=height)
    agg = cvs.points(ms1_df,'ms1_rt','ms1_mz', agg=ds.sum("ms1_i"))

    print(ms1_df)

def test_load_sqlite():
    import sqlite3
    db = sqlite3.connect("{}.sqlite".format(FILENAME_PREFIX))

    ms1_df = pd.read_sql("SELECT * FROM ms1_df WHERE ms1_rt > 1.0 AND ms1_rt < 1.5 AND ms1_mz < 500 AND ms1_mz > 300 AND ms1_polarity='Positive'", db)
    #ms1_df = pd.read_sql("SELECT * FROM ms1_df", db)

    # width = 500
    # height = 500
    # cvs = ds.Canvas(plot_width=width, plot_height=height)
    # agg = cvs.points(ms1_df,'ms1_rt','ms1_mz', agg=ds.sum("ms1_i"))

    print(ms1_df)