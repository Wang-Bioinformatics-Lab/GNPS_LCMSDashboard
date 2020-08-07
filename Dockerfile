FROM continuumio/miniconda3:latest
MAINTAINER Mingxun Wang "mwang87@gmail.com"

COPY requirements.txt .
RUN pip install -r requirements.txt

# Mounting
RUN apt-get update
RUN apt-get install -y curlftpfs 
RUN mkdir /data/massive -p

COPY . /app
WORKDIR /app

