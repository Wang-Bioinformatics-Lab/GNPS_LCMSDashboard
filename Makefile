server-compose-build-nocache:
	docker-compose build --no-cache

server-compose-build:
	docker-compose build

server-compose-dev:
	docker-compose build
	docker-compose -f docker-compose.yml -f docker-compose-dev.yml up

server-compose-interactive:
	docker-compose build
	docker-compose up

server-compose:
	docker-compose build
	docker-compose up -d

attach:
	docker exec -i -t gnpslcms-dash /bin/bash

clear-cache:
	sudo rm temp/* || true
	sudo rm temp/flask-cache/*
	sudo rm temp/memory-cache/joblib/ -rf
	sudo rm temp/image_previews/*.png

clear-flaskcache:
	sudo rm temp/flask-cache/*