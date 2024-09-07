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

COPY docker-config/start-server.sh /start.sh

# Install dependencies
COPY django.yml manage.py .
RUN conda config --add channels conda-forge
RUN conda env create -f django.yml
RUN pip install gunicorn
# copy code and prepare build
COPY interested interested
COPY media media
COPY members members
COPY organizers organizers
COPY static static
COPY trainer trainer
COPY twio_web twio_web
COPY user_handling user_handling
RUN source activate django && python manage.py compress --force

CMD "/start.sh"
