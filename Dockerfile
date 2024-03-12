FROM continuumio/miniconda3:4.10.3
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
RUN apt-get update && apt-get install -y git lftp libarchive-dev

################## INSTALLATION OF MONO ######################
RUN apt-get update && apt -y install apt-transport-https dirmngr gnupg ca-certificates
RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF
RUN echo "deb https://download.mono-project.com/repo/debian stable-buster main" | tee /etc/apt/sources.list.d/mono-official-stable.list
RUN apt-get update && apt-get -y install mono-devel

WORKDIR /src
RUN git clone -b master --single-branch https://github.com/compomics/ThermoRawFileParser --branch v1.3.2 /src
RUN xbuild

# Installing Mamba
RUN conda install -c conda-forge mamba

# Python Package Installations
RUN mamba install -c conda-forge datashader=0.12.1
RUN mamba install -c conda-forge openjdk=11.0.9.1

# Installing HDF5 headers
RUN apt-get update && apt-get install libhdf5-serial-dev netcdf-bin libnetcdf-dev -y

COPY requirements.txt .
RUN pip install -r requirements.txt

# Installing MassQL
RUN pip install git+https://github.com/mwang87/MassQueryLanguage.git


# Install Aspera
# RUN wget -qO- https://ak-delivery04-mul.dhe.ibm.com/sar/CMA/OSA/0a07f/0/ibm-aspera-connect_4.1.0.46-linux_x86_64.tar.gz | tar xvz
# RUN chmod +x ibm-aspera-connect_4.1.0.46-linux_x86_64.sh
# RUN ./ibm-aspera-connect_4.1.0.46-linux_x86_64.sh


COPY . /app
WORKDIR /app

