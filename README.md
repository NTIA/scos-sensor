NTIA/ITS SCOS Sensor
====================

The SCOS sensor is a RESTful API for any sensor that can be controlled via python.

Features:
  - Ready-made containers for x86 and arm32v7 hardware
  - An easy-to-use front end that subverts the need for client code to send http requests.
  - Remote sensor deployment and administration via Foreman and Puppet.
  
  
Browsable API
-------------
The API provides a browsable front end through which all valid requests can be made,
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
  
It's recommended that you activate a virtual environment via `conda` or 
`virtualenv`/`virtualenvwrapper` before following the instructions below.

Copy the environment template file and *modify* the copy if necessary, then source 
it and run deploy.sh to properly configure the sensor code based on the machine on
which it will run.
```bash
$ cp env.template env
$ source ./env
$ ./scripts/deploy.sh       # `deploy.sh` uses `env` to modify other templates
```

Install all Python requirements, set up the database, and create an admin user.
```bash
$ pip install -r ./src/requirements-dev.txt
$ python ./src/manage.py makemigrations && ./src/manage.py migrate
$ python ./src/manage.py createsuperuser
```

To run a Dockerized production-grade stack:
```bash
$ ./scripts/run.sh          # this make take a while the first time
```

For a local development server:
```bash
$ ./src/manage.py runsslserver
```

Foreman and Puppet
------------------
The optimal way to manage individual SCOS Sensor machines in via Foreman
and Puppet. Detailed instructions on how to do this are contained in 
[the Foreman and Puppet README.md](puppet/README.md).


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
