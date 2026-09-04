server-compose-build:
	docker compose --compatibility build

server-compose-interactive:
	docker compose --compatibility build
	docker compose --compatibility up

server-compose-production:
	docker compose --compatibility build
	docker compose --compatibility up -d

# Tears down the retired services (workers, redis). Run once on the host that
# used to serve the full dashboard - `up` alone will not remove them.
server-compose-down:
	docker compose --compatibility down --remove-orphans

attach:
	docker exec -i -t gnpslcms-dash /bin/bash

test:
	cd test && python -m pytest test_app.py -v
