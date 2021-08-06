FROM continuumio/miniconda3:4.8.2
MAINTAINER Mingxun Wang "mwang87@gmail.com"

################## METADATA ######################
LABEL base_image="mono:latest"
LABEL version="1"
LABEL software="ThermoRawFileParser"
LABEL software.version="1.0.0"
LABEL about.summary="A software to convert Thermo RAW files to mgf and mzML"
LABEL about.home="https://github.com/compomics/ThermoRawFileParser"
LABEL about.documentation="https://github.com/compomics/ThermoRawFileParser"
LABEL about.license_file="https://github.com/compomics/ThermoRawFileParser"
LABEL about.license="SPDX:Unknown"
LABEL about.tags="Proteomics"

################## INSTALLATION ######################
RUN apt-get update && apt-get install -y git

################## INSTALLATION OF MONO ######################
RUN apt-get update && apt -y install apt-transport-https dirmngr gnupg ca-certificates
RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF
RUN echo "deb https://download.mono-project.com/repo/debian stable-buster main" | tee /etc/apt/sources.list.d/mono-official-stable.list
RUN apt-get update && apt-get -y install mono-devel

WORKDIR /src
RUN git clone -b master --single-branch https://github.com/compomics/ThermoRawFileParser --branch v1.3.2 /src
RUN xbuild

# Python Package Installations
RUN conda install -c conda-forge datashader=0.12.1
RUN conda install -c conda-forge openjdk=11.0.9.1

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . /app
WORKDIR /app

