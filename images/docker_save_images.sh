mkdir -p images

docker save gnps_lcmsdashboard_gnpslcms-worker-featurefinding:latest | pigz > images/gnps_lcmsdashboard_gnpslcms-worker-featurefinding.tar.gz
docker save gnps_lcmsdashboard_gnpslcms-worker-sync:latest | pigz > images/gnps_lcmsdashboard_gnpslcms-worker-sync.tar.gz
docker save gnps_lcmsdashboard_gnpslcms-dash:latest | pigz > images/gnps_lcmsdashboard_gnpslcms-dash.tar.gz
docker save gnps_lcmsdashboard_gnpslcms-worker-compute:latest | pigz > images/gnps_lcmsdashboard_gnpslcms-worker-compute.tar.gz
docker save gnps_lcmsdashboard_gnpslcms-worker-conversion:latest | pigz > images/gnps_lcmsdashboard_gnpslcms-worker-conversion.tar.gz

