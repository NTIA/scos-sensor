NTIA/ITS SCOS Sensor
====================

The SCOS sensor is a RESTful API for any sensor that can be controlled via python.

It provides:
  - ready-made containers for x86 and arm32v7 hardware
  - TODO
  
Browsable API
-------------
The API provides a browsable front-end through which all valid requests can be made,
and all operations performed. 

All endpoints are easily discoverable, and it's simple
to navigate from function to function:

![Browsable API Root](/docs/img/browsable_api_root.png?raw=true)

Scheduling an action is as simple as filling out a short form:

![Browsable API Submission](/docs/img/browsable_api_submit.png?raw=true)

Actions that have been scheduled show up in the schedule list:

![Browsable API Schedule List](/docs/img/browsable_api_schedule_list.png?raw=true)

See the [API Documentation](xxx) for more information on the features and functions
of each endpoint.

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
# now, to run a Dockerized production-grade stack:
$ ./scripts/run.sh          # this make take a while the first time
# or, for a local development server:
$ ./src/manage.py runsslserver

```

REST API Reference
------------------

 - [View on Github](docs/api/openapi.adoc)
   - [Overview](docs/api/openapi.adoc#_overview)
   - [Paths](docs/api/openapi.adoc#paths)
   - [Definitions](docs/api/openapi.adoc#definitions)
   - [Security](docs/api/openapi.adoc#_securityscheme)

 - [Download PDF](https://github.com/NTIA/scos-sensor/raw/master/docs/api/openapi.pdf)
 
 License
 -------
 See [LICENSE.md](LICENSE.md).
