import sys
sys.path.insert(0, "..")
sys.path.insert(0, ".")
import pandas as pd
import utils_progressbar
import json

def test_progress():
    usi = "mzspec:MSV000084494:GNPS00002_A3_p\nmzspec:MSV000084951:AH22\nmzspec:MSV000086206:ccms_peak/raw/S_N1.mzML"
    status = utils_progressbar.determine_usi_progress(usi)

    print(json.dumps(status, indent=2))

    # creating progress bar
    html_progress = utils_progressbar.generate_html_progress(status)

    print(html_progress)

def main():
    test_progress()

if __name__ == "__main__":
    main()