server-compose-build-nocache:
	docker-compose build --no-cache

server-compose-build:
	docker-compose build

server-compose-dev:
	docker-compose build
	docker-compose -f docker-compose.yml -f docker-compose-dev.yml --compatibility up

server-compose-interactive:
	docker-compose build
	docker-compose --compatibility up

server-compose:
	docker-compose build
	docker-compose --compatibility up -d

clear-cache:
	sudo rm temp/* || true
	sudo rm temp/flask-cache/*  || true
	sudo rm temp/memory-cache/joblib/ -rf
	sudo rm temp/image_previews/*.png
	sudo rm temp/temp/dash-uploader/* -rf

clear-flaskcache:
	sudo rm temp/flask-cache/*


attach:
	docker exec -i -t gnpslcms-dash /bin/bash

attach-conversion:
	docker exec -i -t gnpslcms-worker-conversion /bin/bash