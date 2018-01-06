NTIA/ITS SCOS Sensor
====================

`scos-sensor` is [NTIA/ITS] [Spectrum Monitoring] group's work-in-progress
reference implementation of the _IEEE 802.22.3 Spectrum Characterization and
Occupancy Sensing_ sensor and control plane.

> _What?_

It's a web application that makes it easy to control a software-defined radio
over the Internet.

> _How?_

 - Common open source software stack
 - Pre-built Docker containers
 - Standards track [Browsable](#browsable-api) RESTful API
 - Flexible, extensible, and open default [data format](https://github.com/gnuradio/sigmf)
 - Task scheduling
 - User authenication
 - Loosely coupled to SDR (see [Supporting a Different
   SDR](DEVELOPING.md#supporting-a-different-sdr))
 - Flexible concept of "actions" (see [Writing Custom
   Actions](DEVELOPING.md#writing-custom-actions))

> _Why?_

`scos-sensor` was developed to automate the boring parts of performing some
action with a sensor over the Internet, while keeping the concepts of "sensor"
and "action" loose enough to be useful in a large number of scenarios.

Just setting a sensor on a bench? You'll like the easy web-based control and
data backhaul. Deploying a spectrum monitoring sensor network? You'll
appreciate the thoroughly tested codebase, on-by-default traffic encryption and
user authentication, and automatic [provisioning and
deployment](puppet#foreman-and-puppet).

[NTIA/ITS]: https://its.bldrdoc.gov/
[Spectrum Monitoring]: https://www.its.bldrdoc.gov/programs/cac/spectrum-monitoring.aspx


Table of Contents
-----------------

 - [Introduction](#introduction)
 - [Quickstart](#quickstart)
 - [Browsable API](#browsable-api)
 - [Large Deployments](#large-deployments)
 - [Architecture](#architecture)
 - [API Reference](#api-reference)
 - [License](#license)


Introduction
------------

In this section, we'll go over the high-level concepts used throughout this
repository. Many of these concepts map to endpoints detailed in the [API
Reference](#api-reference).

A sensor advertises its **capabilities**, among which are **actions** that you
can schedule on the sensor. Actions are functions that the sensor owner
implements and exposes to the API. Actions can do anything, e.g., rotate an
antenna or start streaming data over a socket and never return.

Sensor actions are scheduled by posting a **schedule entry** to the sensor's
**schedule**. The **scheduler** periodically reads the schedule and populates a
task queue in priority order.

A **task** represents an action to be run at a _specific_ time. Therefore, a
schedule entry represents a range of tasks. The scheduler continues populating
its task queue until the schedule is exhausted. When executing the task queue,
the scheduler makes a best effort to run each task at its designated time, but
the scheduler will not cancel a running task to start another task, even of
higher priority. **priority** is used to disambiguate two or more tasks that
are schedule to start at the same time.

Some actions acquire data, and those **acquisitions** are retrievable in an
easy to use archive format. Acquisitions are "owned" by the schedule entry that
created them. Schedule entries are "owned" by a specific user.

**Admin** users have full control over the sensor and can create schedule
entries and view, modify, or delete any other user's schedule entries or
acquisitions. Admins can create non-priveleged **user** accounts which can also
create schedule entries and view, modify, and delete things they own, but which
cannot modify or delete things they don't own. Admins can mark a schedule entry
as private from unpriveleged users.


Quickstart
----------

 - Install `git`, `Docker`, `docker-compose`, and `virtualenvwrapper` (optional)

It's recommended that you activate a virtual environment via `conda` or
`virtualenv`/`virtualenvwrapper` before following the instructions below.

1) Clone the repository.

```bash
$ git clone https://github.com/NTIA/scos-sensor.git
$ cd scos-sensor
```

2) Copy the environment template file and *modify* the copy if necessary, then
source it.

```bash
$ cp env.template env
$ source ./env
```

3) Run a Dockerized production-grade stack.

```bash
$ ./scripts/init_db.sh
$ docker-compose pull  # download all necessary images
$ docker-compose run api /src/manage.py createsuperuser
$ docker-compose up
```


Browsable API
-------------

The API provides a browsable front end through which all valid requests can be
made, and all operations performed.

All endpoints are easily discoverable, and it's simple to navigate from
function to function:

![Browsable API Root](/docs/img/browsable_api_root.png?raw=true)

Scheduling an action is as simple as filling out a short form:

![Browsable API Submission](/docs/img/browsable_api_submit.png?raw=true)

Actions that have been scheduled show up in the schedule list:

![Browsable API Schedule List](/docs/img/browsable_api_schedule_list.png?raw=true)

See the [API Documentation](https://ntia.github.io/scos-sensor/) for more
information on the features and functions of each endpoint.


Large Deployments
-----------------

The optimal way to manage multiple SCOS Sensors is via Foreman and Puppet.
Detailed instructions on how to do this are contained in [the Foreman and
Puppet README.md](puppet/README.md).


Architecture
------------

`scos-sensor` uses a open source software stack that should be comfortable for
developers familiar with Python.

 - Persistent data is stored on disk in a file-based SQL database. If this
   simple database doesn't meet your needs, a heavier-duty SQL database like
   PostgreSQL or MariaDB can be dropped in with very little effort.
 - A scheduler thread running in a Gunicorn worker process periodically reads
   the schedule from the database and performs the associated actions.
 - A website and JSON RESTful API is served over HTTPS via NGINX, a
   high-performance web server. These provide easy administration over the
   sensor.


![SCOS Sensor Architecture Diagram](/docs/img/architecture_diagram.png?raw=true)


API Reference
-------------

[View on Github](https://ntia.github.io/scos-sensor/#)


License
-------

See [LICENSE.md](LICENSE.md).
