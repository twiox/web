FROM continuumio/miniconda3

ARG DEBUG
ARG TO_EMAIL
ARG EMAIL_HOST
ARG EMAIL_HOST_USER
ARG EMAIL_HOST_PASSWORD
ARG DEFAULT_FROM_EMAIL
ARG GOOGLE_API_KEY
ARG DB_NAME
ARG DB_USER
ARG DB_PW
ARG DB_HOST

USER root

WORKDIR /opt/twio_web

SHELL ["/bin/bash", "-c"]
RUN apt update && \
    apt upgrade -y && \
    apt install -y \
      g++ \
      default-libmysqlclient-dev \
      pkg-config

# Install dependencies
COPY django.yml manage.py .
RUN conda config --add channels conda-forge
RUN conda env create -f django.yml
RUN source activate django && conda install -y gunicorn
# copy code and prepare build
COPY interested interested
COPY media media
COPY members members
COPY organizers organizers
COPY static static
COPY trainer trainer
COPY twio_web twio_web
COPY user_handling user_handling
COPY docker-config/settings-server.py ./twio_web/settings.py
RUN source activate django && python manage.py compress --force
COPY docker-config/start-server.sh ./start.sh

ENV DEBUG $DEBUG
ENV TO_EMAIL $TO_EMAIL
ENV EMAIL_HOST $EMAIL_HOST
ENV EMAIL_HOST_USER $EMAIL_HOST_USER
ENV EMAIL_HOST_PASSWORD $EMAIL_HOST_PASSWORD
ENV DEFAULT_FROM_EMAIL $DEFAULT_FROM_EMAIL
ENV GOOGLE_API_KEY $GOOGLE_API_KEY
ENV DB_NAME $DB_NAME
ENV DB_USER $DB_USER
ENV DB_PW $DB_PW
ENV DB_HOST $DB_HOST

CMD "/opt/twio_web/start.sh"
