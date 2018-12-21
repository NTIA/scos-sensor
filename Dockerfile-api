FROM ubuntu

# Copy just the necessities from our PY3-enabled UHD container
COPY --from=smsntia/uhd_b2xx_py3:3.13.1.0-rc1 /usr/local/lib/libuhd.so* /usr/local/lib/
COPY --from=smsntia/uhd_b2xx_py3:3.13.1.0-rc1 /usr/local/lib/uhd/ /usr/local/lib/uhd/
COPY --from=smsntia/uhd_b2xx_py3:3.13.1.0-rc1 /usr/lib/python3/dist-packages/uhd/ /usr/lib/python3/dist-packages/uhd/
COPY --from=smsntia/uhd_b2xx_py3:3.13.1.0-rc1 /usr/local/include/uhd.h /usr/local/include/
COPY --from=smsntia/uhd_b2xx_py3:3.13.1.0-rc1 /usr/local/include/uhd/  /usr/local/include/uhd/
COPY --from=smsntia/uhd_b2xx_py3:3.13.1.0-rc1 /usr/local/bin/uhd_* /usr/local/bin/
COPY --from=smsntia/uhd_b2xx_py3:3.13.1.0-rc1 /usr/local/share/uhd/images/usrp_b2* /usr/local/share/uhd/images/

RUN apt-get update -q && \
    DEBIAN_FRONTEND=noninteractive \
                   apt-get install -qy --no-install-recommends \
                   libboost-date-time1.65.1 libboost-filesystem1.65.1 \
                   libboost-python1.65.1 libboost-regex1.65.1 \
                   libboost-serialization1.65.1 libboost-system1.65.1 \
                   libboost-thread1.65.1 libusb-1.0-0 libpython3.6 \
                   libboost-program-options1.65.1 \
                   git python3-setuptools python3-pip python3-numpy && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED 1
RUN mkdir -p /src
WORKDIR /src
COPY ./src/requirements.txt /src
RUN pip3 install --no-cache-dir -r requirements.txt

COPY ./src /src
COPY ./gunicorn /gunicorn

RUN mkdir -p /entrypoints
COPY ./entrypoints/api_entrypoint.sh /entrypoints

RUN mkdir -p /scripts
COPY ./scripts/create_superuser.py /scripts

RUN chmod +x /entrypoints/api_entrypoint.sh

COPY ./scale_factors_schema.json /scale_factors_schema.json
COPY ./scale_factors.json /scale_factors.json

# Args are passed in via docker-compose during build time
ARG DEBUG
ARG DOMAINS
ARG IPS
ARG SECRET_KEY
