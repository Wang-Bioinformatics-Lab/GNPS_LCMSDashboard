# Offline: routing, redirects, input validation.
app:
	python -m pytest test_app.py -v

# Hits live upstream repositories.
resolve:
	python -m pytest test_usi_resolution.py -v

all: app resolve
