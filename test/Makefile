benchmark:
	pytest --durations=0 -n 4 speed_test.py -v

specific_test:
	#pytest --durations=0 speed_test.py::test_xic_proteomics_fast -v --capture=tee-sys
	pytest --durations=0 speed_test.py::test_2dmap_metabolomics -v --capture=tee-sys
	#pytest --durations=0 speed_test.py::test_2dmap_metabolomics_zoomed -v --capture=tee-sys