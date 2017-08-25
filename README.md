NTIA/ITS SCOS Sensor
====================

The SCOS sensor is a remote API for any sensor that can be controlled via python.

It provides:
  - ready-made containers for x86 and arm32v7 hardware
  - TODO

![Browsable API Screenshot](docs/api_root.png)

Quickstart
----------

(See [INSTALL](INSTALL.md) for step-by-step instructions)

  - Install `git`, `Docker`, `docker-compose`, and `virtualenvwrapper` (optional)

```bash
$ git clone https://github.com/NTIA/scos-sensor
$ cd scos-sensor
$ mkvirtualenv scos-sensor  # `workon scos-sensor` hereafter
$ cp env.template env       # modify env
$ source ./env
$ ./scripts/deploy.sh       # `deploy.sh` uses `env` to modify other templates
$ pip install -r ./src/requirements-dev.txt
$ python ./src/manage.py makemigrations && ./src/manage.py migrate
$ python ./src/manage.py createsuperuser
# now, to run a production-grade stack:
$ ./scripts/run.sh          # this make take a while the first time
# or, for development:
$ ./src/manage.py runserver

```

REST API Reference
------------------

 - [View PDF](docs/api/openapi.pdf)
 - [View HTML](https://rawgit.com/NTIA/scos-sensor/master/docs/api/openapi.html)
