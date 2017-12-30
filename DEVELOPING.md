This document dives into the process of developing with this codebase. It
starts with the basics of running the sensor code with local modifications,
then discusses adding support for a different sofware defined radio (SDR).
Lastly, it talks about the concept of "actions" and how to program a custom
action.

Running the Sensor
==================

The main README's Quickstart provides guidance on running the sensor in its
stock configuration. The following techniques can be used to see local
modifications. Sections are in order, so "Running Development Server" assumes
you've done the setup setups in "Running Tests", etc.

Running Tests
-------------

Ideally, you should add a test that covers any new feature that you add. If
you've done that, then running the included test suite is the easiest way to
check that everything is working. Either way, all tests should be run after
making any local modifications to ensure that you haven't caused a regression.

`scos-sensor` uses [pytest](https://docs.pytest.org/en/latest/) and
[pytest-django](https://pytest-django.readthedocs.io/en/latest/) for testing.
Tests are organized by
[application](https://docs.djangoproject.com/en/dev/ref/applications/#projects-and-applications),
so tests related to the scheduler are in `./src/scheduler/tests`, and a test
for a custom action would be added in `./src/actions/tests`.
[tox](https://tox.readthedocs.io/en/latest/) is a tool that can run all
available tests in a virtual environment against all supported version of
python. Running `pytest` directly is faster, but running `tox` is a more
thorough test.

The following commands install the sensor's development requirements. We highly
recommend you initialize a virtual development environment using a tool such a
`conda` or `virtualenv` first.

```bash
$ cd src
$ python2 -m pip install -r requirements-dev.txt
$ pytest          # faster, but less thorough
$ tox             # tests code in clean virtualenv
$ tox --recreate  # if you change `requirements.txt`
$ tox -e lint     # check that code meets widely accepted coding standards
$ tox -e coverage # check where test coverage lacks
```

Running Development Server
--------------------------

It's also useful to run a development server locally. The following steps
assume you've already setup some kind of virtual environment and installed
python dev requirements from "Running Tests".

```bash
$ ./scripts/init_db.sh
$ cd src
$ ./manage.py createsuperuser
$ ./manage.py runserver
```

Running Production Server with Local Changes
--------------------------------------------

The Docker compose file and application code look for information from the
environment when run in production mode, so it's necessary to source the
following file in each shell that you intend to launch the sensor from. (HINT:
it can be useful to add the `source` command to a post-activate file in
whatever virtual environment you're using).

```bash
$ cp env.template env     # modify if necessary, default are okay for testing
$ source ./env
```

Then, build the API docker image locally, which will satisfy the
`smsntia/scos-sensor` image in the Docker compose file and bring up the sensor.

```bash
$ ./scripts/build_api.sh
$ docker-compose up
```


Supporting a Different SDR
==========================

`scos-sensor` currently has built-in support for the Ettus B2xx line of
software-defined radios. If you want to use a different SDR that has a python
API, you should able to do so with little effort:

 - Change the `Install GNURadio and UHD` section of the
   [Dockerfile](Dockerfile) to install the required drivers.
 - Copy the [USRP adapater file](src/actions/usrp.py) and modify for your SDR.

If your SDR doesn't have a python API, you'll need a python adapater file that
calls out to your SDRs available API and reads the samples back into python.

The next step in supporting a different SDR would be to modify the
[monitor_usrp](src/actions/monitor_usrp.py) action which can be used to
periodically exercise the SDR and make signal Docker to recycle the container
if its connection is lost. Next we'll go into more depth about _actions_ and
how to write them.


Writing Custom Actions
======================

"Actions" are one of the main concepts used by `scos-sensor`. At a high level,
they are the things that the sensor owner wants to the sensor to be able to
_do_. At a lower level, they are simply python classes with a special method
`__call__`.

Start by looking at the [Action base class](src/actions/base.py). It includes
some logic to parse a description and summary out of the action class's
docstring, and a `__call__` method that must be overridden. If you pass
`admin_only=True` to this base class, the API will not make it or any data it
created available to non-admin users.

The [logger action](src/actions/logger.py) is a very simple example action and
simply logs the name of the schedule entry and task id that is running it, but
it's a good example of a complete action. Notice that you first create a
subclass of the `Action` base class, and then override the `__call__` method.
The action should not store any state locally, but it can access to database.

As a more complex example, check out the [acquire_single_freq_fft
action](src/actions/acquire_single_freq_fft.py), which uses the USRP and stores
the acquisition metadata and data in the database.

Lastly, to expose a custom action to the API and make it schedulable,
instantiate it in the `registered_actions` dict in the actions module,
[here](src/actions/__init__.py).
