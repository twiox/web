FROM continuumio/miniconda3

USER root

WORKDIR /opt/twio_web

SHELL ["/bin/bash", "-c"]

RUN apt update && \
    apt upgrade -y && \
    apt install -y \
      g++ \
      default-libmysqlclient-dev \
      pkg-config

# copy code
COPY . /opt/twio_web

RUN conda config --add channels conda-forge
RUN conda env create -f django.yml
RUN pip install gunicorn
RUN source activate django && python manage.py compress --force

COPY docker-config/start-server.sh /start.sh
CMD "/start.sh"
