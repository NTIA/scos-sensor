FROM ubuntu

# Update Ubuntu image
RUN apt-get update && \
    apt-get dist-upgrade -y && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install python prerequisites
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
            python-setuptools python-pip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install numpy build requirements
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
            python-all-dev libblas-dev liblapack-dev libatlas-base-dev gfortran && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install GNURadio and UHD
RUN apt-get update && \
    apt-get install -y --no-install-recommends gnuradio uhd-host && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN /usr/lib/uhd/utils/uhd_images_downloader.py

ENV PYTHONUNBUFFERED 1
RUN mkdir -p /src
WORKDIR /src
COPY ./src/requirements.txt /src
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src /src
COPY ./gunicorn /gunicorn
COPY ./config /config

RUN mkdir -p /entrypoints
COPY ./entrypoints/api_entrypoint.sh /entrypoints
COPY ./entrypoints/testing_entrypoint.sh /entrypoints

RUN mkdir -p /scripts
COPY ./scripts/create_superuser.py /scripts

RUN chmod +x /entrypoints/api_entrypoint.sh
RUN chmod +x /entrypoints/testing_entrypoint.sh # for jenkins CI

# Args are passed in via docker-compose during build time
ARG DEBUG
ARG DOMAINS
ARG IPS
ARG SECRET_KEY
