
# Modified version of: https://binx.io/2022/06/13/poetry-docker/
# with comments, and some practices from
# https://ep2020.europython.eu/media/conference/slides/CeKGczx-best-practices-for-production-ready-docker-packaging.pdf
# (not the best, but it's a good bootstrap)


FROM python:3.11-slim as python

ENV PYTHONUNBUFFERED=true

# Enables tracebacks from C code
ENV PYTHONFAULTHANDLER=1

WORKDIR /app


FROM python as poetry

ENV POETRY_HOME=/opt/poetry

# great for
ENV POETRY_VIRTUALENVS_IN_PROJECT=true
ENV PATH="$POETRY_HOME/bin:$PATH"

# this isntallation method doesn't require additional packages, which is good
RUN python -c 'from urllib.request import urlopen; print(urlopen("https://install.python-poetry.org").read().decode())' | python -

# Only copy 2 files for greater reusability of layers
COPY poetry.lock poetry.lock
COPY pyproject.toml pyproject.toml

# no need for extra groups, disable cache
RUN poetry install --no-interaction --no-ansi --no-cache -vvv --only main


FROM python as runtime

# extend path with executables from .venv
ENV PATH="/app/.venv/bin:$PATH"

# copy virtualenv
COPY --from=poetry /app/.venv/ .venv/

# copy codebase, only
COPY ./app/ /app/

# This is not needed for `worker` process on Dokku
EXPOSE 8000

# Won't work well for containers running just Telegram in polling mode
#HEALTHCHECK --interval=20s --timeout=1s --start-period=1m --retries=5 CMD ./do healthcheck

CMD ./do tgbot-polling
