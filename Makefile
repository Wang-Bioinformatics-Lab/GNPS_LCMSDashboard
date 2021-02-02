server-compose-build-nocache:
	docker-compose build --no-cache

server-compose-interactive:
	docker-compose build
	docker-compose up

server-compose:
	docker-compose build
	docker-compose up -d

attach:
	docker exec -i -t gnpslcms-dash /bin/bash


clear-cache:
	sudo rm temp/flask-cache/*
	sudo rm temp/memory-cache/*
	sudo rm temp/image_previews/*.png