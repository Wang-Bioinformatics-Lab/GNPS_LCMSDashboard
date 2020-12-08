FROM continuumio/miniconda3:latest
MAINTAINER Mingxun Wang "mwang87@gmail.com"

RUN conda install -c conda-forge datashader
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN conda install -c conda-forge openjdk


COPY . /app
WORKDIR /app

