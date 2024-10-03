FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

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

WORKDIR /opt/twio_web

RUN apt update && \
    apt upgrade -y && \
    apt install -y \
      g++ \
      default-libmysqlclient-dev \
      pkg-config

# Install dependencies
COPY uv.lock manage.py pyproject.toml .
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
RUN uv sync --frozen --no-dev
RUN uv pip install gunicorn

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
RUN uv run manage.py compress --force
COPY docker-config/start-server.sh ./start.sh

# Place executables in the environment at the front of the path
ENV PATH="/opt/twio_web/.venv/bin:$PATH"

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

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
