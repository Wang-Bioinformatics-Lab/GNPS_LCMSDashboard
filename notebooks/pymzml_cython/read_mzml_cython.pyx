import pymzml
import numpy as np
cimport numpy as np
#DTYPE = np.float64


def read_pymzml_cython(filename):
    run = pymzml.run.Reader(filename)

    for spec in run:
        if spec.ms_level == 1:
            rt = spec.scan_time_in_minutes()
            #peaks = spec.reduce(mz_range=(0, 2000))

            # Sorting by intensity
            #peaks = peaks[peaks[:,1].argsort()]
            #peaks = peaks[-100:]

            #mz, intensity = zip(*peaks)