import sys
import os

sys.path.insert(0, "peakonly-master")
sys.path.insert(0, "peakonly-master/processing_utils")

import torch

from processing_utils.runner import FilesRunner
from models.rcnn import RecurrentCNN
from models.cnn_classifier import Classifier
from models.cnn_segmentator import Segmentator

import pandas as pd

device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')

import argparse

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('input_mzML', help='input_mzML')
parser.add_argument('output_features', help='output_features')

args = parser.parse_args()

# to do: device should be customizable parameter

delta_mz = 0.05
required_points = 4
dropped_points = 1
minimum_peak_points = 3

#path2mzml = ["../../temp/ftp_massive.ucsd.edu_MSV000085852_ccms_peak_QC_raw_QC_0.mzML"]
#path2mzml = ["../../temp/ftp_massive.ucsd.edu_MSV000084494_ccms_peak_raw_GNPS00002_A3_p.mzML"]
path2mzml = [args.input_mzML]

mode = 'sequential'
classifier = Classifier().to(device)
path2classifier_weights = 'Classifier.pt'
classifier.load_state_dict(torch.load(path2classifier_weights, map_location=device))
classifier.eval()

segmentator = Segmentator().to(device)
path2segmentator_weights = 'Segmentator.pt'
segmentator.load_state_dict(torch.load(path2segmentator_weights, map_location=device))
segmentator.eval()

models = [classifier, segmentator]

runner = FilesRunner(mode, models, delta_mz,
                        required_points, dropped_points,
                        minimum_peak_points, device)

feature_list, params = runner.__call__(path2mzml)

output_list = []

for feature in feature_list:
    feature_dict = {}
    feature_dict["mz"] = feature.mz
    feature_dict["rt"] = (feature.rtmin + feature.rtmax) / 2
    feature_dict["i"] = feature.intensities[0]

    output_list.append(feature_dict)

pd.DataFrame(output_list).to_csv(args.output_features, index=False, sep='\t')
