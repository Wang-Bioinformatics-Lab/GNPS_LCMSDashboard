import sys
import os

sys.path.insert(0, "peakonly-master")
sys.path.insert(0, "peakonly-master/processing_utils")

import torch

from processing_utils.runner import FilesRunner
from models.rcnn import RecurrentCNN
from models.cnn_classifier import Classifier
from models.cnn_segmentator import Segmentator



device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
# to do: device should be customizable parameter

delta_mz = 0.05
required_points = 4
dropped_points = 1
minimum_peak_points = 3

#path2mzml = ["../../temp/ftp_massive.ucsd.edu_MSV000085852_ccms_peak_QC_raw_QC_0.mzML"]
path2mzml = ["../../temp/ftp_massive.ucsd.edu_MSV000084494_ccms_peak_raw_GNPS00002_A3_p.mzML"]


# for file in self.list_of_files.selectedItems():
#     path2mzml.append(self.list_of_files.file2path[file.text()])
# if not path2mzml:
#     raise ValueError

# if self.mode == 'all in one':
#     # to do: save models as pytorch scripts
#     model = RecurrentCNN().to(device)
#     path2weights = self.weights_widget.get_file()
#     model.load_state_dict(torch.load(path2weights, map_location=device))
#     model.eval()
#     models = [model]
# elif self.mode == 'sequential':
#     classifier = Classifier().to(device)
#     path2classifier_weights = self.weights_classifier_widget.get_file()
#     classifier.load_state_dict(torch.load(path2classifier_weights, map_location=device))
#     classifier.eval()
#     segmentator = Segmentator().to(device)
#     path2segmentator_weights = self.weights_segmentator_widget.get_file()
#     segmentator.load_state_dict(torch.load(path2segmentator_weights, map_location=device))
#     segmentator.eval()
#     models = [classifier, segmentator]
# elif self.mode == 'simple':

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

features = runner.__call__(path2mzml)

feature_list = features[0]
parameters = features[1]



print(feature_list[0].mz, feature_list[0].rtmin, feature_list[0].rtmax)

#print(feature_list)
#print(parameters)

#worker = Worker(runner, path2mzml, multiple_process=True)
#worker.signals.result.connect(self.parent.set_features)

#models = ""
#peak_minimum_points = 4
#device = "cpu"
#runner.FilesRunner(models, peak_minimum_points, device)