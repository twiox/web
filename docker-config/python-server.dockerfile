FROM continuumio/miniconda3

USER root

WORKDIR /opt/twio_web

SHELL ["/bin/bash", "-c"]

RUN apt update && \
    apt upgrade -y && \
    apt install -y \
      gcc

# copy code
COPY . /opt/twio_web

# build
RUN ls /opt/twio_web && conda env create -f django.yml && \
    source activate django && \
    python3 manage.py makemigrations && \
    python3 manage.py makemigrations interested && \
    python3 manage.py migrate

COPY docker-config/start-server.sh /start.sh
CMD "/start.sh"
