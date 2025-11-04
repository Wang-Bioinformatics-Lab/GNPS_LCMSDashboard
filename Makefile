server-compose-build-nocache:
	docker compose --compatibility build --no-cache

server-compose-build:
	docker compose --compatibility build

server-compose-dev:
	docker compose --compatibility build
	docker compose -f docker-compose.yml -f docker-compose-dev.yml --compatibility up

server-compose-interactive:
	docker compose --compatibility build
	docker compose --compatibility up

server-compose:
	docker compose --compatibility build
	docker compose --compatibility up -d

server-compose-production:
	docker compose --compatibility build
	docker compose --compatibility up -d

server-compose-privileged-server:
	docker-compose -f docker-compose.yml -f docker-compose-privileged.yml --compatibility up -d

clear-cache:
	sudo rm temp/* || true
	sudo rm temp/flask-cache/* || true
	sudo rm temp/memory-cache/joblib/ -rf || true
	sudo rm temp/image_previews/*.png || true
	sudo rm temp/dash-uploader/* -rf || true

clear-flaskcache:
	sudo rm temp/flask-cache/*

clear-memorycache:
	sudo rm temp/memory-cache/joblib/ -rf || true

attach:
	docker exec -i -t gnpslcms-dash /bin/bash

attach-conversion:
	docker exec -i -t gnpslcms-worker-conversion /bin/bash

##### For image deployment
