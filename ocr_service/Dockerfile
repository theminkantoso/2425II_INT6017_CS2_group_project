#
FROM ubuntu:22.04 as base
FROM python:3.11-slim as python-base

# https://python-poetry.org/docs#ci-recommendations
ENV POETRY_VERSION=1.8.5
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VENV=/opt/poetry-venv

# Tell Poetry where to place its cache and virtual environment
ENV POETRY_CACHE_DIR=/opt/.cache

# Create stage for Poetry installation
FROM python-base as poetry-base

# Creating a virtual environment just for poetry and install it with pip
RUN python3 -m venv $POETRY_VENV \
	&& $POETRY_VENV/bin/pip install -U pip setuptools \
	&& $POETRY_VENV/bin/pip install poetry==${POETRY_VERSION}

# Create a new stage from the base python image
FROM python-base as example-app

# Copy Poetry to app image
COPY --from=poetry-base ${POETRY_VENV} ${POETRY_VENV}

# Add Poetry to PATH
ENV PATH="${PATH}:${POETRY_VENV}/bin"

# Install tesseract
RUN apt-get update
RUN apt-get -y install tesseract-ocr
RUN apt-get -y install libtesseract-dev

WORKDIR /app

# Copy Dependencies
COPY pyproject.toml ./

# [OPTIONAL] Validate the project is properly configured
RUN poetry check

# Install Dependencies
RUN poetry install --no-interaction --no-cache --without dev

# Copy Application
COPY . /app

# Run Application
EXPOSE 5001

#
CMD ["poetry", "run", "python", "./main/run.py"]