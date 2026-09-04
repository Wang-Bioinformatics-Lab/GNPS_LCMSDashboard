FROM python:3.10-slim

# No conda, no ProteoWizard, no system packages: this image resolves USIs to URLs
# and redirects. Anything that needed a compiler or a converter binary went away
# with the dashboard.

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py download.py download_msv.py download_workbench.py download_norman.py download_zenodo.py run_server.sh ./

RUN chmod +x run_server.sh && useradd --create-home --shell /usr/sbin/nologin gnps
USER gnps

EXPOSE 5000

CMD ["./run_server.sh"]
