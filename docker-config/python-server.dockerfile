FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

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
COPY accounts accounts
COPY media media
COPY members members
COPY public public
COPY static static
COPY trainer trainer
COPY twio_web twio_web
RUN uv run manage.py compress --force
COPY docker-config/start-server.sh ./start.sh

# Place executables in the environment at the front of the path
ENV PATH="/opt/twio_web/.venv/bin:$PATH"

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

CMD "/opt/twio_web/start.sh"
