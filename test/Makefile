all:
	rm temp/*
	pytest --durations=0 test_2d.py test_usi_resolution.py test_xic.py -n 8

resolve:
	pytest test_usi_resolution.py -v

benchmark:
	pytest --durations=0 -n 4 speed_test.py -v --profile-svg

specific_test:
	#pytest --durations=0 speed_test.py::test_xic_proteomics_fast -v --capture=tee-sys
	#pytest --durations=0 speed_test.py::test_2dmap_metabolomics -v --capture=tee-sys
	#pytest --durations=0 speed_test.py::test_2dmap_metabolomics_zoomed -v --capture=tee-sys
	#pytest --durations=0 speed_test.py::test_2dmap_proteomics_data -v --capture=tee-sys
	#pytest --durations=0 speed_test.py::test_2dmap_proteomics_data2 -v --capture=tee-sys
	#pytest --durations=0 speed_test.py::test_2dmap_metabolomics_zoomed -v --capture=tee-sys
	#pytest --durations=0 test_usi_resolution.py::test_raw_filename -v --capture=tee-sys
	#pytest --durations=0 test.py::test_tic_fast -v --capture=tee-sys
	#pytest --durations=0 test_featurefinding.py::test_mzmine -v --capture=tee-sys
	#pytest --durations=0 test.py::test_ms2_spectrum -v --capture=tee-sys
	#pytest --durations=0 test_2d.py::test_2d_mapping -v --capture=tee-sys
	#pytest --durations=0 test_debug.py::test_agilent -v --capture=tee-sys
	#pytest --durations=0 test_debug.py::test_cdf -v --capture=tee-sys
	pytest --durations=0 test_usi_resolution.py::test_resolve_debug -v --capture=tee-sys
	


# Testing performance with hdf5
write_compressed:
	pytest test_hdf5.py::test_write -vv --capture=tee-sys

read_mzml:
	pytest test_hdf5.py::test_load_mzml -vv --capture=tee-sys --profile --profile-svg

read_hdf5:
	pytest test_hdf5.py::test_load_h5 -vv --capture=tee-sys

read_sqlite:
	pytest test_hdf5.py::test_load_sqlite -vv --capture=tee-sys

read_pickle:
	pytest test_hdf5.py::test_load_pickle -vv --capture=tee-sys
	
read_feather:
	pytest test_hdf5.py::test_load_feather -vv --capture=tee-sys