NTIA/ITS SCOS Sensor
====================

`scos-sensor` is a platform for operating a sensor, such as a software-defined
radio (SDR), over a network. It's developed by [NTIA/ITS] Spectrum Monitoring
group to help us better understand how radio spectrum is being used, so that
next-generation technologies can be introduced without interfering with the
existing system that we all rely on. `scos-sensor` is open source and automates
the boring parts of performing some action with a sensor over the Internet,
while keeping the concepts of "action" and "sensor" loose enough to be broadly
useful. Just add an "adapter" for your desired sensor, implement one or more
"actions" to expose to the API, and get a robust (over 180 automated tests;
self-healing architecture), secure (user authentication; traffic encryption on
by default) remote spectrum monitoring solution.


## Features:

 - Easy sensor control over RESTful API or [Browsable API](#browsable-api) website
 - Flexible, extensible, and open data format
 - Common open source software stack
 - Pre-built Docker containers
 - Task scheduling
 - User authentication
 - Hardware agnostic (see [Supporting a Different
   SDR](DEVELOPING.md#supporting-a-different-sdr))
 - Flexible concept of "actions" (see [Writing Custom
   Actions](DEVELOPING.md#writing-custom-actions))


[NTIA/ITS]: https://its.bldrdoc.gov/


Table of Contents
-----------------

 - [Introduction](#introduction)
 - [Browsable API](#browsable-api)
 - [Quickstart](#quickstart)
 - [Large Deployments](#large-deployments)
 - [Architecture](#architecture)
 - [Glossary](#glossary)
 - [References](#references)
 - [License](#license)


Introduction
------------

`scos-sensor` is [NTIA/ITS] [Spectrum Monitoring] group's work-in-progress
reference implementation of the [IEEE 802.22.3 Spectrum Characterization and
Occupancy Sensing][ieee-link] (SCOS) sensor.

# TODO: better technical introduction here.


[NTIA/ITS]: https://its.bldrdoc.gov/
[Spectrum Monitoring]: https://www.its.bldrdoc.gov/programs/cac/spectrum-monitoring.aspx
[ieee-link]: http://www.ieee802.org/22/P802_22_3_PAR_Detail_Approved.pdf


Browsable API
-------------

Opening the URL to your sensor (`localhost` if you followed the Quickstart) in
a browser, you will see a frontend to the API that allows you to do anything
the JSON API allows.

Relationships in the API are represented by URLs which you can click to
navigate front endpoint to endpoint. The full API is _discoverable_ simply by
following these links:

![Browsable API Root](/docs/img/browsable_api_root.png?raw=true)

Scheduling an action is as simple as filling out a short form:

![Browsable API Submission](/docs/img/browsable_api_submit.png?raw=true)

Actions that have been scheduled show up in the schedule entry list:

![Browsable API Schedule List](/docs/img/browsable_api_schedule_list.png?raw=true)


Quickstart
----------

 - Install `git`, `Docker`, and `docker-compose`.

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


Large Deployments
-----------------

The best way to manage multiple SCOS Sensors is via Foreman and Puppet. For
detailed instructions, see [the Foreman and Puppet
README](puppet/README.md).


Architecture
------------

`scos-sensor` uses a open source software stack that should be comfortable for
developers familiar with Python.

 - Persistent data is stored on disk in a file-based SQL database. If this
   simple database doesn't meet your needs, a heavier-duty SQL database like
   PostgreSQL or MariaDB can be dropped in with very little effort.
 - A scheduler thread running in a [Gunicorn] worker process periodically reads
   the schedule from the database and performs the associated actions.
 - A website and JSON RESTful API is served over HTTPS via [NGINX], a
   high-performance web server. These provide easy administration over the
   sensor.


![SCOS Sensor Architecture Diagram](/docs/img/architecture_diagram.png?raw=true)

[Gunicorn]: http://gunicorn.org/
[NGINX]: https://www.nginx.com/


Glossary
--------

In this section, we'll go over the high-level concepts used throughout this
repository. Many of these concepts map to endpoints detailed in the [API
Reference](#api-reference).

 - *action*: A function that the sensor owner implements and exposes to the
   API. Actions are one of the main concepts used by `scos-sensor`. At a high
   level, they are the things that the sensor owner wants the sensor to be able
   to *do*. Since actions block the scheduler while they run, they have
   exclusive access to the sensor's resources (like the SDR). Currently, there
   are several logical groupings of actions, such as those that create
   acquisitions, or admin-only actions that handle administrative tasks.
   However, actions can theoretically do anything a sensor owner can implement.
   Some less common (but perfectly acceptable) ideas for actions might be to
   rotate an antenna, or start streaming data over a socket and only return
   when the recipient closes the connection.

 - *acquisition*: Some combination of data and metadata created by an action
   (though an action does not have to create an acquisition). Metadata is
   accessible directly though the API, while data is retrievable in an
   easy-to-use archive format with its associated metadata.

 - *admin*: A user account that has full control over the sensor and can create
   schedule entries and view, modify, or delete any other user's schedule
   entries or acquisitions. Admins can create non-priveleged *user* accounts.
   Admins can mark a schedule entry as private from unpriveleged users.

 - *capability*: A fact about some ability or limitation that the sensor has.
   For example, is the sensor mobile or stationary? What is the frequency range
   of the attached SDR? These values are generally hard-coded by the sensor
   owner and rarely change. The actions registered on a sensor are considered
   part of its capabilities.

 - *schedule*: The collection of all schedule entries (active and inactive) on
   the sensor.

 - *scheduler*: A thread that consumes times from active entries and executes
   the requested action. The scheduler reads the schedule at most once a second
   and *consumes* all past and present times for each active entry in the
   schedule. The latest task per entry is then added to a priority queue, and
   the scheduler executes the associated actions and stores/POSTs tasks
   results. The scheduler operates in a simple blocking fashion, which
   significantly simplifies resources deconfliction, but means that it cannot
   guarantee a task is run at the requested time.

 - *schedule entry*: Describes a series of scheduler tasks. A schedule entry is
   at minimum a human readable name and an associated action. Combining
   different values of *start*, *stop*, *interval*, and *priority* allows for
   flexible task scheduling. If no start time is given, the first task is
   scheduled as soon as possible. If no stop time is given, tasks continue to
   be scheduled until the schedule entry is manually deactivated. Leaving the
   interval undefined results in a "one-shot" entry, where the scheduler
   deactivates the entry after a single task is scheduled. One-shot entries can
   be used with a future start time.

 - *task*: A representation of an action to be run at a specific time. A
   schedule entry represents a range of tasks. The scheduler continues
   populating its task queue with tasks until the schedule is exhausted. When
   executing the task queue, the scheduler makes a best effort to run each task
   at its designated time, but the scheduler will not cancel a running task to
   start another task, even of higher priority. *priority* is used to
   disambiguate two or more tasks that are schedule to start at the same time.

 - *task result*: A record of the outcome of a task. A result is recorded for
   each task after the action function returns, and includes metadata such as
   when the task *started*, when it *finished*, its *duration*, the *result*
   (`success` or `failure`), and a freeform *detail* string. A `TaskResult`
   JSON object is also POSTed to a schedule entry's `callback_url`, if
   provided.

 - *user*: An unpriveleged account type which can create schedule entries and
   view, modify, and delete things they own, but which cannot modify or delete
   things they don't own. Actions marked `admin_only` are not schedulable, and
   schedule entries marked private by an admin (along with their results and
   acquisitions) are not visible to users.


References
----------

 - [SCOS Control Plane API Reference](https://ntia.github.io/scos-sensor/)
 - [SCOS Data Transfer Specification](https://github.com/NTIA/SCOS-Transfer-Spec)


License
-------

See [LICENSE](LICENSE.md).
