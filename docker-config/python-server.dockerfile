FROM continuumio/miniconda3

USER root

WORKDIR /opt/twio_web

SHELL ["/bin/bash", "-c"]

RUN apt update && \
    apt upgrade -y && \
    apt install -y \
      gcc \
      default-libmysqlclient-dev

# copy code
COPY . /opt/twio_web

RUN conda env create -f django.yml && \
    source activate django && \
    pip install gunicorn && \
    python manage.py compress --force

COPY docker-config/start-server.sh /start.sh
CMD "/start.sh"
