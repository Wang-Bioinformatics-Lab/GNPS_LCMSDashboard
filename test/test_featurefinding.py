import os
import sys
import tidyms as ms
from pyopenms import *

# def test_mzmine():
#     sys.path.insert(0, "..")
#     import feature_finding
#     feature_finding._mzmine_feature_finding("QC_0.mzML")


# def test_featurefinding():
#     ms_data = ms.MSData("QC_0.mzML",
#                      ms_mode="centroid",
#                      instrument="orbitrap",
#                      separation="uplc")
    
#     roi, feature_data = ms_data.detect_features()

#     print(feature_data)

# def test_pyopenms():

    # Prepare data loading (save memory by only
    # loading MS1 spectra into memory)
    # options = PeakFileOptions()
    # options.setMSLevels([1])
    # fh = MzMLFile()
    # fh.setOptions(options)

    # # Load data
    # input_map = MSExperiment()
    # fh.load("QC_0.mzML", input_map)
    # input_map.updateRanges()

    # ff = FeatureFinderMetabo()
    # ff.setLogType(LogType.CMD)

    # ff.run()

    # # Run the feature finder
    # name = "centroided"
    # features = FeatureMap()
    # seeds = FeatureMap()
    # params = FeatureFinderMetabo().getParameters(name)
    # ff.run(name, input_map, features, params, seeds)

    # features.setUniqueIds()
    # fh = FeatureXMLFile()
    # fh.store("output.featureXML", features)
    # print("Found", features.size(), "features")