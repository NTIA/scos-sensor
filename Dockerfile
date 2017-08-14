FROM ubuntu:latest

# Install GNURadio and UHD
RUN apt-get update && \
    apt-get install -y --no-install-recommends gnuradio uhd-host && \
    rm -rf /var/lib/apt/lists/*

# Install pip
RUN apt-get update && \
    apt-get install -y --no-install-recommends python-pip && \
    rm -rf /var/lib/apt/lists/*

# Copied from python:onbuild
ENV PYTHONUNBUFFERED 1
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
COPY ./src/requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt
COPY ./src/ /usr/src/app
