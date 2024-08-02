from psims.mzml.writer import MzMLWriter
import pymzml
from tqdm import tqdm

def _convert_mzml_to_mzml_bruteforce(input_mzML, output_mzML):
    run = pymzml.run.Reader(input_mzML)

    with MzMLWriter(open(output_mzML, 'wb')) as out:
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

