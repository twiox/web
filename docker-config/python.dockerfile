FROM continuumio/miniconda3

USER root

WORKDIR /opt/twio_web

RUN apt update && \
    apt upgrade -y && \
    apt install -y \
      gcc

COPY start.sh /
CMD ["/bin/bash", "-lc","/start.sh"]
