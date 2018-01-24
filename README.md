NTIA/ITS SCOS Sensor
====================

`scos-sensor` is [NTIA/ITS] [Spectrum Monitoring] group's work-in-progress
reference implementation of the [IEEE 802.22.3 Spectrum Characterization and
Occupancy Sensing][ieee-link] (SCOS) sensor. It is a platform for operating a
sensor, such as a software-defined radio (SDR), over a network. The goal is to
provide a robust, flexible, and secure starting point for remote spectrum
monitoring.

[NTIA/ITS]: https://its.bldrdoc.gov/
[Spectrum Monitoring]: https://www.its.bldrdoc.gov/programs/cac/spectrum-monitoring.aspx
[ieee-link]: http://www.ieee802.org/22/P802_22_3_PAR_Detail_Approved.pdf


Table of Contents
-----------------

 - [Introduction](#introduction)
 - [Quickstart](#quickstart)
 - [Large Deployments](#large-deployments)
 - [Browsable API](#browsable-api)
 - [Architecture](#architecture)
 - [Glossary](#glossary)
 - [References](#references)
 - [License](#license)


Introduction
------------

**Note**: It may help to read the [Glossary](#glossary) first.

`scos-sensor` was designed by NTIA/ITS with the following goals in mind:

 - Easy-to-use sensor control and data retrieval via IP network
 - Low-cost, open-source development resources
 - Design flexibility to allow developers to evolve sensor technologies and
   metrics
 - Hardware agnostic
 - Discoverable sensor capabilities
 - Task scheduling using start/stop times, interval, and/or priority
 - Standardized metadata/data format that supports cooperative sensing and open
   data initiatives
 - Security controls that prevent unauthorized users from accessing internal
   sensor functionality
 - Easy-to-deploy with provisioned and configured OS
 - Quality assurance of software via automated testing prior to release

Sensor control is accomplished through a RESTful API. The API is designed to be
rich enough so that multiple sensors can be automated effectively while being
simple enough to still be useful for single-sensor deployments. For example, by
advertising capabilites and location, an owner of multiple sensors can easily
filter by frequency range, available *actions*, or geographic location. Yet,
since each sensor hosts its own [Browsable API](#browsable-api), controlling
small deployments is as easy as clicking around a website.

When a *task* acquires data, that data and a significant amount of metadata are
stored in a local database. The full metadata can be read directly through the
self-hosted website or retrieved in plain text via a single API call. Our
metadata and data format is an extension of, and compatible with, the
[SigMF](https://github.com/gnuradio/sigmf) specification. The [SCOS Data
Transfer Specification](https://github.com/NTIA/SCOS-Transfer-Spec) describes
the `scos` namespace.

When deploying equipment remotely, the robustness and security of software
becomes a prime concern. `scos-sensor` sits on top of a popular open-source
framework (see [Architecture](#architecture)), which provides out-of-the-box
protection against cross site scripting (XSS), cross site request forgery
(CSRF), SQL injection, and clickjacking attacks, and also enforces SSL/HTTPS
(traffic encryption), host header validation, and user session security. In
addition to these, we have implemented an unprivileged *user* type so that the
sensor owner can allow access to other users and API consumers while
maintaining ultimate control. To minimize the chance of regressions while
developing for the sensor, we have written almost 200 unit and integration
tests. See [Developing](DEVELOPING.md) to learn how to run the test suite.

We have tried to remove the most common hurdles to remotely deploying a sensor
while maintaining flexibility in two key areas. First, the API itself is
hardware agnostic, and the implementation assumes different hardware will be
used depending on sensing requirements (see [Supporting a Different
SDR](DEVELOPING.md#supporting-a-different-sdr)). Second, we introduce the
high-level concept of "*actions*" (see [Writing Custom
Actions](DEVELOPING.md#writing-custom-actions)), which gives the sensor owner
control over what the sensor can be tasked to do.

We have many of our design and development discussions right here on GitHub. If
you find a bug or have a use-case that we don't currently support, feel free to
open an issue.


Quickstart
----------

This section describes how to spin up a production-grade sensor in just a few commands.

We currently support Ettus USRP B2xx software-defined radios out of the box,
and any Intel-based host computer should work. ARM-based single-board computers
have also been tested, but we do not prepare pre-build Docker containers at
this time.

1) Install `git`, `Docker`, and `docker-compose`.

2) Clone the repository.

```bash
$ git clone https://github.com/NTIA/scos-sensor.git
$ cd scos-sensor
```

3) Copy the environment template file and *modify* the copy if necessary, then
source it.

```bash
$ cp env.template env
$ source ./env
```

4) Run a Dockerized production-grade stack.

```bash
$ ./scripts/init_db.sh
$ docker-compose up -d                                    # start in background
$ docker-compose exec api /src/manage.py createsuperuser  # create admin user
$ docker-compose logs --follow api                        # reattach terminal
```


Large Deployments
-----------------

Large sensor deployments present unique challenges. At NTIA/ITS, we use Foreman
and Puppet to handle hardware provisioning and configuration management. While
a ground-up introduction to these tools is outside the scope of this
repository, The [Foreman and Puppet README](puppet/README.md) should be enough
to help someone familiar with these tools get up to speed.


Browsable API
-------------

Opening the URL to your sensor (`localhost` if you followed the Quickstart) in
a browser, you will see a frontend to the API that allows you to do anything
the JSON API allows.

Relationships in the API are represented by URLs which you can click to
navigate from endpoint to endpoint. The full API is _discoverable_ simply by
following these links:

![Browsable API Root](/docs/img/browsable_api_root.png?raw=true)

Scheduling an *action* is as simple as filling out a short form on `/schedule`:

![Browsable API Submission](/docs/img/browsable_api_submit.png?raw=true)

*Actions* that have been scheduled show up in the *schedule entry* list:

![Browsable API Schedule List](/docs/img/browsable_api_schedule_list.png?raw=true)


Architecture
------------

`scos-sensor` uses a open source software stack that should be comfortable for
developers familiar with Python.

 - Persistent data is stored on disk in a file-based SQL database. If this
   simple database doesn't meet your needs, a heavier-duty SQL database like
   PostgreSQL or MariaDB can be dropped in with very little effort.
 - A *scheduler* thread running in a [Gunicorn] worker process periodically reads
   the *schedule* from the database and performs the associated *actions*.
 - A website and JSON RESTful API using [Django REST framework] is served over
   HTTPS via [NGINX], a high-performance web server. These provide easy
   administration over the sensor.


![SCOS Sensor Architecture Diagram](/docs/img/architecture_diagram.png?raw=true)

[Gunicorn]: http://gunicorn.org/
[NGINX]: https://www.nginx.com/
[Django REST framework]: http://www.django-rest-framework.org/


Glossary
--------

In this section, we'll go over the high-level concepts used by `scos-sensor`.

 - *action*: A function that the sensor owner implements and exposes to the
   API. Actions are the things that the sensor owner wants the sensor to be
   able to *do*. Since actions block the scheduler while they run, they have
   exclusive access to the sensor's resources (like the SDR). Currently, there
   are several logical groupings of actions, such as those that create
   acquisitions, or admin-only actions that handle administrative tasks.
   However, actions can theoretically do anything a sensor owner can implement.
   Some less common (but perfectly acceptable) ideas for actions might be to
   rotate an antenna, or start streaming data over a socket and only return
   when the recipient closes the connection.

 - *acquisition*: The combination of data and metadata created by an action
   (though an action does not have to create an acquisition). Metadata is
   accessible directly though the API, while data is retrievable in an
   easy-to-use archive format with its associated metadata.

 - *admin*: A user account that has full control over the sensor and can create
   schedule entries and view, modify, or delete any other user's schedule
   entries or acquisitions. Admins can create non-privileged *user* accounts.
   Admins can mark a schedule entry as private from unprivileged users.

 - *capability*: Available actions, installation specifications (e.g., mobile
   or stationary), and operational ranges of hardware components (e.g.,
   frequency range of SDR). These values are generally hard-coded by the sensor
   owner and rarely change.

 - *schedule*: The collection of all schedule entries (active and inactive) on
   the sensor.

 - *scheduler*: A thread responsible for executing the schedule. The scheduler
   reads the schedule at most once a second and consumes all past and present
   times for each active schedule entry until the schedule is exhausted. The
   latest task per schedule entry is then added to a priority queue, and the
   scheduler executes the associated actions and stores/POSTs task results. The
   scheduler operates in a simple blocking fashion, which significantly
   simplifies resource deconfliction. When executing the task queue, the
   scheduler makes a best effort to run each task at its designated time, but
   the scheduler will not cancel a running task to start another task, even of
   higher priority. *priority* is used to disambiguate two or more tasks that
   are schedule to start at the same time.

 - *schedule entry*: Describes a range of scheduler tasks. A schedule entry is
   at minimum a human readable name and an associated action. Combining
   different values of *start*, *stop*, *interval*, and *priority* allows for
   flexible task scheduling. If no start time is given, the first task is
   scheduled as soon as possible. If no stop time is given, tasks continue to
   be scheduled until the schedule entry is manually deactivated. Leaving the
   interval undefined results in a "one-shot" entry, where the scheduler
   deactivates the entry after a single task is scheduled. One-shot entries can
   be used with a future start time. If two tasks are scheduled to run at the
   same time, they will be run in order of *priority*. If two tasks are
   scheduled to run at the same time and have the same *priority*, execution
   order is implmenetation-dependent (undefined).

 - *task*: A representation of an action to be run at a specific time.

 - *task result*: A record of the outcome of a task. A result is recorded for
   each task after the action function returns, and includes metadata such as
   when the task *started*, when it *finished*, its *duration*, the *result*
   (`success` or `failure`), and a freeform *detail* string. A `TaskResult`
   JSON object is also POSTed to a schedule entry's `callback_url`, if
   provided.

 - *user*: An unprivileged account type which can create schedule entries and
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
