FROM continuumio/miniconda3:4.10.3
MAINTAINER Mingxun Wang "mwang87@gmail.com"

################## INSTALLATION ######################
RUN apt-get update && apt-get install -y git lftp libarchive-dev

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

COPY . /app
WORKDIR /app

