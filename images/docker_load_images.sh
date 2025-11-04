gunzip -c gnps_lcmsdashboard_gnpslcms-worker-featurefinding.tar.gz | docker load
gunzip -c gnps_lcmsdashboard_gnpslcms-worker-sync.tar.gz | docker load
gunzip -c gnps_lcmsdashboard_gnpslcms-dash.tar.gz | docker load
gunzip -c gnps_lcmsdashboard_gnpslcms-worker-compute.tar.gz | docker load
gunzip -c gnps_lcmsdashboard_gnpslcms-worker-conversion.tar.gz | docker load