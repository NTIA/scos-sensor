FROM ubuntu

# Update Ubuntu image
RUN apt-get update -q && \
    DEBIAN_FRONTEND=noninteractive \
    apt-get install -qy --no-install-recommends \
            python-setuptools python-pip python-numpy \
            gnuradio uhd-host && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    /usr/lib/uhd/utils/uhd_images_downloader.py && \
    rm -f /usr/share/uhd/images/{octo,usrp{{1,2},_{x,e,n,b1}}}* && \
    rm -rf /usr/share/uhd/images/winusb_driver && \
    rm -rf /usr/lib/uhd/{examples,tests}

ENV PYTHONUNBUFFERED 1
RUN mkdir -p /src
WORKDIR /src
COPY ./src/requirements.txt /src
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src /src
COPY ./gunicorn /gunicorn

RUN mkdir -p /entrypoints
COPY ./entrypoints/api_entrypoint.sh /entrypoints

RUN mkdir -p /scripts
COPY ./scripts/create_superuser.py /scripts

RUN chmod +x /entrypoints/api_entrypoint.sh

# Args are passed in via docker-compose during build time
ARG DEBUG
ARG DOMAINS
ARG IPS
ARG SECRET_KEY
