import os
import pymzml
import sys
from tqdm import tqdm
from psims.mzml.writer import MzMLWriter


input_filename = sys.argv[1]
output_filename = sys.argv[2]

run = pymzml.run.Reader(input_filename)

with MzMLWriter(open(output_filename, 'wb')) as out:
    out.controlled_vocabularies()
    scan_num = 1
    previous_ms1_scan = 0
    with out.run(id="my_analysis"):
        spectrum_count = 1000

        with out.spectrum_list(count=spectrum_count):
            for spec in tqdm(run):
                if len(spec.mz) == 0:
                    continue
                
                
                if spec.ms_level == 1:
                    previous_ms1_scan = scan_num
                    out.write_spectrum(
                        spec.mz, spec.i,
                        id="scan={}".format(scan_num), params=[
                            "MS1 Spectrum",
                            {"ms level": 1},
                            {"total ion current": sum(spec.i)},
                        ],
                        scan_start_time=spec.scan_time_in_minutes())
                elif spec.ms_level == 2:
                    precursor_spectrum = spec.selected_precursors[0]
                    precursor_mz = precursor_spectrum["mz"]
                    precursor_intensity = precursor_spectrum.get("i", 0)
                    precursor_charge = precursor_spectrum.get("charge", 0)

                    out.write_spectrum(
                        spec.mz, spec.i,
                        id="scan={}".format(scan_num), params=[
                            "MSn Spectrum",
                            {"ms level": 2},
                            {"total ion current": sum(spec.i)}
                         ],
                         # Include precursor information
                         precursor_information={
                            "mz": precursor_mz,
                            "intensity": precursor_intensity,
                            "charge": precursor_charge,
                            "scan_id": "scan={}".format(previous_ms1_scan),
                            "activation": ["beam-type collisional dissociation", {"collision energy": 25}]
                         })

                scan_num += 1

            # for scan, products in scans:
            #     # Write Precursor scan
            #     out.write_spectrum(
            #         scan.mz_array, scan.intensity_array,
            #         id=scan.id, params=[
            #             "MS1 Spectrum",
            #             {"ms level": 1},
            #             {"total ion current": sum(scan.intensity_array)}
            #          ])


    
        

    
