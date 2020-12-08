import pandas as pd
from utils import _spectrum_generator
from utils import _get_scan_polarity

def perform_feature_finding(filename, params):
    """
    Do stuff for feature finding
    """

    if params["type"] == "Test":
        return _test_feature_finding(filename)

    if params["type"] == "Trivial":
        return _trivial_feature_finding(filename)

    if params["type"] == "TidyMS":
        return _tidyms_feature_finding(filename)
    

def _test_feature_finding(filename):
    features_df = pd.DataFrame()
    features_df["mz"] = [100]
    features_df["rt"] = [0.2]
    features_df["i"] = [1000]

    return features_df

def _trivial_feature_finding(filename):
    min_rt = 0
    max_rt = 1000000
    min_mz = 0
    max_mz = 2000

    all_mz = []
    all_i = []
    all_rt = []

    for spec in _spectrum_generator(filename, min_rt, max_rt):
        scan_polarity = _get_scan_polarity(spec)

        if spec.ms_level == 1:
            rt = spec.scan_time_in_minutes()

            try:
                # Filtering peaks by mz
                peaks = spec.reduce(mz_range=(min_mz, max_mz))

                # Sorting by intensity
                peaks = peaks[peaks[:,1].argsort()]
                peaks = peaks[-2:]

                mz, intensity = zip(*peaks)

                all_mz += list(mz)
                all_i += list(intensity)
                all_rt += len(mz) * [rt]
            except:
                raise
                pass

    features_df = pd.DataFrame()
    features_df['mz'] = all_mz
    features_df['i'] = all_i
    features_df['rt'] = all_rt

    features_df = features_df.sort_values(by=['i'])
    features_df = features_df.head(50)

    return features_df

# TODO: 
def _tidyms_feature_finding(filename):
    import tidyms as ms

    ms_data = ms.MSData(filename,
                     ms_mode="centroid",
                     instrument="orbitrap",
                     separation="uplc")
    
    roi, feature_data = ms_data.detect_features()

    print(feature_data)

    features_df = pd.DataFrame()
    features_df['mz'] = feature_data['mz']
    features_df['i'] = feature_data['area']
    features_df['rt'] = feature_data['rt'] / 60

    print(features_df)

    return features_df

# TODO: 
def _mzmine_feature_finding(filename):
    return None

# TODO: 
def _openms_feature_finding(filename):
    return None

