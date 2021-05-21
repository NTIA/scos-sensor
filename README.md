# NTIA/ITS SCOS Sensor

[![Travis CI Build Status][travis-badge]][travis-link]
[![API Docs Build Status][api-docs-badge]][api-docs-link]

`scos-sensor` is a  work-in-progress reference implementation of the [IEEE 802.15.22.3
Spectrum Characterization and Occupancy Sensing][ieee-link] (SCOS) sensor developed by
[NTIA/ITS]. `scos-sensor` defines a RESTful application programming interface (API),
that allows authorized users to discover capabilities, schedule actions, and acquire
resultant data.

[NTIA/ITS]: https://its.bldrdoc.gov/
[ieee-link]: https://standards.ieee.org/standard/802_15_22_3-2020.html
[travis-link]: https://travis-ci.org/NTIA/scos-sensor
[travis-badge]: https://travis-ci.org/NTIA/scos-sensor.svg?branch=master
[api-docs-link]: https://ntia.github.io/scos-sensor/
[api-docs-badge]: https://img.shields.io/badge/docs-available-brightgreen.svg

## Table of Contents

- [Introduction](#introduction)
- [Glossary](#glossary)
- [Architecture](#architecture)
- [Overview of scos-sensor Repo Structure](#Overview-of-scos-sensor-Repo-Structure)
- [Quickstart](#quickstart)
- [Configuration](#configuration)
- [Security](#security)
- [Actions and Hardware Support](#actions-and-hardware-support)
- [Development](#development)
- [References](#references)
- [License](#license)
- [Contact](#contact)

## Introduction

`scos-sensor` was designed by NTIA/ITS with the following goals in mind:

- Easy-to-use sensor control and data retrieval via IP network
- Low-cost, open-source development resources
- Design flexibility to allow developers to evolve sensor technologies and metrics
- Hardware agnostic
- Discoverable sensor capabilities
- Task scheduling using start/stop times, interval, and/or priority
- Standardized metadata/data format that supports cooperative sensing and open data
  initiatives
- Security controls that prevent unauthorized users from accessing internal sensor
  functionality
- Easy-to-deploy with provisioned and configured OS
- Quality assurance of software via automated testing prior to release

Sensor control is accomplished through a RESTful API. The API is designed to be rich
enough that multiple heterogeneous sensors can be automated effectively while being
simple enough to still be useful for single-sensor deployments. For example, by
advertising capabilities and location, an owner of multiple sensors can easily filter
by frequency range, available actions, or geographic location. Yet, since each sensor
hosts its own Browsable API, controlling small deployments is as easy as clicking
around a website.

Opening the URL to your sensor (localhost if you followed the Quickstart) in a browser,
you will see a frontend to the API that allows you to do anything the JSON API allows.
Relationships in the API are represented by URLs which you can click to navigate from
endpoint to endpoint. The full API is *discoverable* simply by following these links:

![Browsable API Root](/docs/img/browsable_api_root.png?raw=true)

Scheduling an *action* is as simple as filling out a short form on `/schedule`:

![Browsable API Submission](/docs/img/browsable_api_submit.png?raw=true)

*Actions* that have been scheduled show up in the *schedule entry* list:

![Browsable API Schedule List](/docs/img/browsable_api_schedule_list.png?raw=true)

We have tried to remove the most common hurdles to remotely deploying a sensor while
maintaining flexibility in two key areas. First, the API itself is hardware agnostic,
and the implementation assumes different hardware will be used depending on sensing
requirements. Second, we introduce the high-level concept of "actions" which gives the
sensor owner control over what the sensor can be tasked to do. For more information see
[Actions and Hardware Support](#actions-and-hardware-support).

## Glossary

This section provides an overview of high-level concepts used by `scos-sensor`.

- *action*: A function that the sensor owner implements and exposes to the API. Actions
  are the things that the sensor owner wants the sensor to be able to *do*. Since
  actions block the scheduler while they run, they have exclusive access to the
  sensor's resources (like the signal analyzer). Currently, there are several logical
  groupings of actions, such as those that create acquisitions, or admin-only actions
  that handle administrative tasks. However, actions can theoretically do anything a
  sensor owner can implement. Some less common (but perfectly acceptable) ideas for
  actions might be to rotate an antenna, or start streaming data over a socket and only
  return when the recipient closes the connection.

- *acquisition*: The combination of data and metadata created by an action (though an
  action does not have to create an acquisition). Metadata is accessible directly
  though the API, while data is retrievable in an easy-to-use archive format with its
  associated metadata.

- *admin*: A user account that has full control over the sensor and can create schedule
  entries and view, modify, or delete any other user's schedule entries or
  acquisitions.

- *capability*: Available actions, installation specifications (e.g., mobile or
  stationary), and operational ranges of hardware components (e.g., frequency range of
  signal analyzer). These values are generally hard-coded by the sensor owner and
  rarely change.

- *plugin*: A Python package with actions designed to be integrated into scos-sensor.

- *schedule*: The collection of all schedule entries (active and inactive) on the
  sensor.

- *scheduler*: A thread responsible for executing the schedule. The scheduler reads the
  schedule at most once a second and consumes all past and present times for each
  active schedule entry until the schedule is exhausted. The latest task per schedule
  entry is then added to a priority queue, and the scheduler executes the associated
  actions and stores/POSTs task results. The scheduler operates in a simple blocking
  fashion, which significantly simplifies resource deconfliction. When executing the
  task queue, the scheduler makes a best effort to run each task at its designated
  time, but the scheduler will not cancel a running task to start another task, even
  one of higher priority.

- *schedule entry*: Describes a range of scheduler tasks. A schedule entry is at
  minimum a human readable name and an associated action. Combining different values of
  *start*, *stop*, *interval*, and *priority* allows for flexible task scheduling. If
  no start time is given, the first task is scheduled as soon as possible. If no stop
  time is given, tasks continue to be scheduled until the schedule entry is manually
  deactivated. Leaving the interval undefined results in a "one-shot" entry, where the
  scheduler deactivates the entry after a single task is scheduled. One-shot entries
  can be used with a future start time. If two tasks are scheduled to run at the same
  time, they will be run in order of *priority*. If two tasks are scheduled to run at
  the same time and have the same *priority*, execution order is
  implementation-dependent (undefined).

- *signals*: Django event driven programming framework. Actions use signals to send
  results to scos-sensor. These signals are handled by scos-sensor so that the results
  can be processed (such as storing measurement data and metadata).

- *task*: A representation of an action to be run at a specific time. When a *task*
  acquires data, that data is stored on disk, and a significant amount of metadata is
  stored in a local database. The full metadata can be read directly through the
  self-hosted website or retrieved in plain text via a single API call. Our metadata
  and data format is an extension of, and compatible with, the [SigMF](
  https://github.com/gnuradio/sigmf) specification - see [sigmf-ns-ntia](
  https://github.com/NTIA/sigmf-ns-ntia).

- *task result*: A record of the outcome of a task. A result is recorded for each task
  after the action function returns, and includes metadata such as when the task
  *started*, when it *finished*, its *duration*, the *result* (`success` or `failure`),
  and a freeform *detail* string. A `TaskResult` JSON object is also POSTed to a
  schedule entry's `callback_url`, if provided.

## Architecture

When deploying equipment remotely, the robustness and security of software is a prime
concern. `scos-sensor` sits on top of a popular open-source framework,
which provides out-of-the-box protection against cross site scripting (XSS), cross site
request forgery (CSRF), SQL injection, and clickjacking attacks, and also enforces
SSL/HTTPS (traffic encryption), host header validation, and user session security.

`scos-sensor` uses a open source software stack that should be comfortable for
developers familiar with Python.

- Persistent metadata is stored on disk in a relational database, and measurement data
  is stored in files on disk.
- A *scheduler* thread running in a [Gunicorn] worker process periodically reads the
  *schedule* from the database and performs the associated *actions*.
- A website and JSON RESTful API using [Django REST framework] is served over HTTPS via
  [NGINX], a high-performance web server. These provide easy administration over the
  sensor.

![SCOS Sensor Architecture Diagram](/docs/img/architecture_diagram.png?raw=true)

A functioning scos-sensor utilizes software from at least three different GitHub
repositories. As shown below, the scos-sensor repository integrates everything together
as a functioning scos-sensor and provides the code for the user interface, scheduling,
and the storage and retrieval of schedules and acquisitions. The [scos-actions
repository](https://github.com/ntia/scos-actions) provides the core actions API,
defines the radio interface that provides an abstraction for all signal analyzers, and
provides basic actions. Finally, using a real radio within scos-sensor requires a third
`scos-<signal analyzer>` repository that provides the signal analyzer specific
implementation of the radio interface where `<signal analyzer>` is replaced with the
name of the signal analyzer, e.g. a USRP scos-sensor utilizes the [scos-usrp
repository](https://github.com/ntia/scos-usrp). The signal analyzer specific
implementation of the radio interface may expose additional properties of the signal
analyzer to support signal analyzer specific capabilities and the repository may also
provide additional signal analyzer specific actions.

![SCOS Sensor Modules](/docs/img/scos-sensor-modules.JPG?raw=true)

[Gunicorn]: http://gunicorn.org/
[NGINX]: https://www.nginx.com/
[Django REST framework]: http://www.django-rest-framework.org/

## Overview of scos-sensor Repo Structure

- configs: This folder is used to store the sensor_definition.json file.
- docker: Contains the docker files used by scos-sensor.
- docs: Documentation including the [documentation hosted on GitHub pages](
  https://ntia.github.io/scos-sensor/) generated from the OpenAPI specification.
- entrypoints: Docker entrypoint scripts which are executed when starting a container.
- gunicorn: Gunicorn configuration file.
- nginx: Nginx configuration template and SSL certificates.
- schemas: JSON schema files.
- scripts: Various utility scripts.
- src: Contains the scos-sensor source code.
   - actions: Code to discover actions in plugins and to perform a simple logger action.
   - authentication: Code related to user authentication.
   - capabilities: Code used to generate capabilities endpoint.
   - handlers: Code to handle signals received from actions.
   - schedule: Schedule API endpoint for scheduling actions.
   - scheduler: Scheduler responsible for executing actions.
   - sensor: Core app which contains the settings, generates the API root endpoint.
   - static: Django will collect static files (JavaScript, CSS, …) from all apps to this
     location.
   - status: Status endpoint.
   - tasks: Tasks endpoint used to display upcoming and completed tasks.
   - templates: HTML templates used by the browsable API.
   - conftest.py: Used to configure pytest fixtures.
   - manage.py: Django’s command line tool for administrative tasks.
   - requirements.txt and requirements-dev.txt: Python dependencies.
   - tox.ini: Used to configure tox.
- docker-compose.yml: Used by docker-compose to create services from containers. This
  is needed to run scos-sensor.
- env.template: Template file for setting environment variables used to configure
  scos-sensor.

## Quickstart

This section describes how to spin up a production-grade sensor in just a few commands.

We currently support Ettus USRP B2xx software-defined radios out of the box, and any
Intel-based host computer should work. ARM-based single-board computers have also been
tested, but we do not prepare pre-built Docker containers for them at this time.

1) Install `git`, `Docker`, and `docker-compose`.

2) Clone the repository.

```bash
git clone https://github.com/NTIA/scos-sensor.git
cd scos-sensor
```

3) Copy the environment template file and *modify* the copy if necessary, then source
it. The settings in this file are set for running in a development environment on your
local system. For running in a production environment, many of the settings will need
to be modified. See [Configuration](#configuration) section. Also, you are strongly
encouraged to change the default `ADMIN_EMAIL` and `ADMIN_PASSWORD` before running
scos-sensor. Finally, source the file before running scos-sensor to load the settings
into your environment.

```bash
cp env.template env
source ./env
```

4) Run a Dockerized stack.

```bash
docker-compose up -d --build  # start in background
docker-compose logs --follow api  # reattach terminal

```

## Configuration

When running in a production environment or on a remote system, various settings will
need to be configured.

### Environment File

As explained in the [Quickstart](#quickstart) section, before running scos-sensor, an
environment (env) file is created from the env.template file. These settings can either
be set in the environment file or set directly in docker-compose.yml. Here are the
settings in the environment file:

- ADMIN_EMAIL: Email used to generate admin user. Change in production.
- ADMIN_PASSWORD: Password used to generate admin user. Change in production.
- BASE_IMAGE: Base docker image used to build the API container.
- CALLBACK_SSL_VERIFICATION: Set to “true” in production environment. If false, the SSL
  certificate validation will be ignored when posting results to the callback URL.
- DEBUG: Django debug mode. Set to False in production.
- DOCKER_TAG: Always set to “latest” to install newest version of docker containers.
- DOMAINS: A space separated list of domain names. Used to generate [ALLOWED_HOSTS](
  https://docs.djangoproject.com/en/3.0/ref/settings/#allowed-hosts).
- GIT_BRANCH: Current branch of scos-sensor being used.
- GUNICORN_LOG_LEVEL: Log level for Gunicorn log messages.
- IPS: A space separated list of IP addresses. Used to generate [ALLOWED_HOSTS](
  https://docs.djangoproject.com/en/3.0/ref/settings/#allowed-hosts).
- FQDN: The server’s fully qualified domain name.
- MAX_DISK_USAGE: The maximum disk usage percentage allowed before overwriting old
  results. Defaults to 85%. This disk usage detected by scos-sensor (using the Python
  `shutil.disk_usage` function) may not match the usage reported by the Linux `df`
  command.
- POSTGRES_PASSWORD: Sets password for the Postgres database for the “postgres” user.
  Change in production.
- REPO_ROOT: Root folder of the repository. Should be correctly set by default.
- SECRET_KEY: Used by Django to provide cryptographic signing. Change to a unique,
  unpredictable value. See
  <https://docs.djangoproject.com/en/3.0/ref/settings/#secret-key>.
- SSL_CERT_PATH: Path to server SSL certificate. Replace the certificate in the
  scos-sensor repository with a valid certificate in production.
- SSL_KEY_PATH: Path to server SSL private key. Use the private key for your valid
  certificate in production.

### Sensor Definition File

This file contains information on the sensor and components being used. It is used in
the SigMF metadata to identify the hardware used for the measurement. It should follow
the [sigmf-ns-ntia Sensor Object format](
https://github.com/NTIA/sigmf-ns-ntia/blob/master/ntia-sensor.sigmf-ext.md#11-sensor-object
). See an example below. Overwrite the [example
file in scos-sensor/configs](configs/sensor_definition.json) with the information
specific to the sensor you are using.

```json
{
    "id": "",
    "sensor_spec": {
        "id": "",
        "model": "greyhound"
    },
    "antenna": {
        "antenna_spec": {
            "id": "",
            "model": "L-com HG3512UP-NF"
        }
    },
    "signal_analyzer": {
        "sigan_spec": {
            "id": "",
            "model": "Ettus USRP B210"
        }
    },
    "computer_spec": {
        "id": "",
        "model": "Intel NUC"
    }
}
```

## Security

This section covers authentication, permissions, and certificates used to access the
sensor, and the authentication available for the callback URL. Two different types of
authentication are available for authenticating against the sensor and for
authenticating when using a callback URL.

### Sensor Authentication And Permissions

The sensor can be configured to authenticate using OAuth JWT access tokens from an
external authorization server or using Django Rest Framework Token Authentication.

#### Django Rest Framework Token Authentication

This is the default authentication method. To enable Django Rest Framework
Authentication, make sure `AUTHENTICATION` is set to `TOKEN` in the environment file
(this will be enabled if `AUTHENTICATION` set to anything other
than `JWT`).

A token is automatically created for each user. Django Rest Framework Token
Authentication will check that the token in the Authorization header ("Token " +
token) matches a user's token.

#### OAuth2 JWT Authentication

To enable OAuth 2 JWT Authentication, set `AUTHENTICATION` to `JWT` in the environment
file. To authenticate, the client will need to send a JWT access token in the
authorization header (using "Bearer " + access token). The token signature will be
verified using the public key from the `PATH_TO_JWT_PUBLIC_KEY` setting. The expiration
time will be checked. Only users who have an authority matching the `REQUIRED_ROLE`
setting will be authorized.

The token is expected to come from an OAuth2 authorization server. For more
information, see <https://tools.ietf.org/html/rfc6749>.

#### Certificates

This section describes how to create a self-signed root CA, SSL server certificates for
the sensor, optional client certificates, and test JWT public/private key pair.

As described below, a self-signed CA can be created for testing. **For production, make
sure to use certificates from a trusted CA.**

Below instructions adapted from
[here](https://www.golinuxcloud.com/openssl-create-client-server-certificate/#OpenSSL_create_client_certificate).

##### Sensor Certificate

This is the SSL certificate used for the scos-sensor web server and is always required.

To be able to sign server-side and client-side certificates, we need to create our own
self-signed root CA certificate first.

```bash
openssl req -x509 -sha512 -days 365 -newkey rsa:4096 -keyout scostestca.key -out scostestca.pem
```

Generate a host certificate signing request.

```bash
openssl req -new -newkey rsa:4096 -keyout sensor01.key -out sensor01.csr -subj "/C=[2 letter country code]/ST=[state or province]/L=[locality]/O=[organization]/OU=[organizational unit]/CN=[common name]"
```

Before we proceed with openssl, we need to create a configuration file -- sensor01.ext.
It'll store some additional parameters needed when signing the certificate. Adjust the
settings in the below example for your sensor:

```text
authorityKeyIdentifier=keyid,issuer:always
basicConstraints=CA:FALSE
subjectAltName = @alt_names
subjectKeyIdentifier = hash
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth, clientAuth
[alt_names]
DNS.1 = sensor01.domain
DNS.2 = localhost
IP.1 = xxx.xxx.xxx.xxx
IP.2 = 127.0.0.1
```

Sign the host certificate.

```bash
openssl x509 -req -CA scostestca.pem -CAkey scostestca.key -in sensor01.csr -out sensor01.pem -days 365 -sha256 -CAcreateserial -extfile sensor01.ext
```

If the sensor private key is encrypted, decrypt it using the following command:

```bash
openssl rsa -in sensor01.key -out sensor01_decrypted.key
```

Combine the sensor certificate and private key into one file:

```bash
cat sensor01_decrypted.key sensor01.pem > sensor01_combined.pem
```

##### Client Certificate

This certificate is required for using the sensor with mutual TLS which is required if
OAuth authentication is enabled.

Replace the brackets with the information specific to your user and organization.

```bash
openssl req -new -newkey rsa:4096 -keyout client.key -out client.csr -subj "/C=[2 letter country code]/ST=[state or province]/L=[locality]/O=[organization]/OU=[organizational unit]/CN=[common name]"
```

Create client.ext with the following:

```text
basicConstraints = CA:FALSE
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid,issuer
keyUsage = digitalSignature
extendedKeyUsage = clientAuth
```

Sign the client certificate.

```bash
openssl x509 -req -CA scostestca.pem -CAkey scostestca.key -in client.csr -out client.pem -days 365 -sha256 -CAcreateserial -extfile client.ext
```

Convert pem to pkcs12:

```bash
openssl pkcs12 -export -out client.pfx -inkey client.key -in client.pem -certfile scostestca.pem
```

Import client.pfx into web browser for use with the browsable API or use the client.pem
or client.pfx when communicating with the API programmatically.

##### Generating JWT Public/Private Key

The JWT public key must correspond to the private key of the JWT issuer (OAuth
authorization server). For manual testing, the instructions below could be used to
create a public/private key pair for creating JWTs without an authorization
server.

###### Step 1: Create public/private key pair

```bash
openssl genrsa -out jwt.pem 4096
```

###### Step 2: Extract Public Key

```bash
openssl rsa -in jwt.pem -outform PEM -pubout -out jwt_public_key.pem
```

###### Step 3: Extract Private Key

```bash
openssl pkey -inform PEM -outform PEM -in jwt.pem -out jwt_private_key.pem
```

###### Configure scos-sensor

The Nginx web server can be set to require client certificates (mutual TLS). This can
optionally be enabled. To require client certificates, uncomment
`ssl_verify_client on;` in the [Nginx configuration file](nginx/conf.template). If you
use OCSP, also uncomment `ssl_ocsp on;`. Additional configuration may be needed for
Nginx to check certificate revocation lists (CRL).

Copy the server certificate and server private key (sensor01_combined.pem) to
`scos-sensor/configs/certs`. Then set `SSL_CERT_PATH` and `SSL_KEY_PATH` (in the
environment file) to the path of the sensor01_combined.pem relative to configs/certs
(for file at `scos-sensor/configs/certs/sensor01_combined.pem`, set
`SSL_CERT_PATH=sensor01_combined.pem` and `SSL_KEY_PATH=sensor01_combined.pem`). For
mutual TLS, also copy the CA certificate to the same directory. Then, set
`SSL_CA_PATH` to the path of the CA certificate relative to `configs/certs`.

If you are using JWT authentication, set `PATH_TO_JWT_PUBLIC_KEY` to the path of the
JWT public key relative to configs/certs. This public key file should correspond to the
private key used to sign the JWT. Alternatively, the JWT private key
created above could be used to manually sign a JWT token for testing if
`PATH_TO_JWT_PUBLIC_KEY` is set to the JWT public key created above.

If you are using client certificates, use client.pfx to connect to the browsable API by
importing this certificate into your browser.

For callback functionality with an OAuth authorized callback URL, set
`PATH_TO_CLIENT_CERT` and `PATH_TO_VERIFY_CERT`, both relative to configs/certs.
Depending on the configuration of the callback URL server and the authorization server,
the sensor server certificate could be used as a client certificate by setting
`PATH_TO_CLIENT_CERT` to the path of sensor01_combined.pem relative to configs/certs.
Also the CA used to verify the client certificate could potentially be used to verify
the callback URL server certificate by setting `PATH_TO_VERIFY_CERT` to the same file
as used for `SSL_CA_PATH` (scostestca.pem).

#### Permissions and Users

The API requires the user to either have an authority in the JWT token matching the the
`REQUIRED_ROLE` setting or that the user be a superuser. New users created using the
API initially do not have superuser access. However, an admin can mark a user as a
superuser in the Sensor Configuration Portal. When using JWT tokens, the user does not
have to be pre-created using the sensor's API. The API will accept any user using a
JWT token if they have an authority matching the required role setting.

### Callback URL Authentication

OAuth and Token authentication are supported for authenticating against the server
pointed to by the callback URL. Callback SSL verification can be enabled
or disabled using `CALLBACK_SSL_VERIFICATION` in the environment file.

#### Token

A simple form of token authentication is supported for the callback URL. The sensor
will send the user's (user who created the schedule) token in the authorization header
("Token " + token) when posting results to callback URL. The server can then verify
the token against what it originally sent to the sensor when creating the schedule.
This method of authentication for the callback URL is enabled by default. To verify it
is enabled, set `CALLBACK_AUTHENTICATION` to `TOKEN` in the environment file (this will
be enabled if `CALLBACK_AUTHENTICATION` set to anything other than `OAUTH`).
`PATH_TO_VERIFY_CERT`, in the environment file, can used to set a CA certificate to
verify the callback URL server SSL certificate. If this is unset and
`CALLBACK_SSL_VERIFICATION` is set to true, [standard trusted CAs](
    https://requests.readthedocs.io/en/master/user/advanced/#ca-certificates) will be
used.

#### OAuth

The OAuth 2 password flow is supported for callback URL authentication. The following
settings in the environment file are used to configure the OAuth 2 password flow
authentication.

- `CALLBACK_AUTHENTICATION` - set to `OAUTH`.
- `CLIENT_ID` - client ID used to authorize the client (the sensor) against the
  authorization server.
- `CLIENT_SECRET` - client secret used to authorize the client (the sensor) against the
  authorization server.
- `OAUTH_TOKEN_URL` - URL to get the access token.
- `PATH_TO_CLIENT_CERT` - client certificate used to authenticate against the
  authorization server.
- `PATH_TO_VERIFY_CERT` - CA certificate to verify the authorization server and
  callback URL server SSL certificate. If this is unset and `CALLBACK_SSL_VERIFICATION`
  is set to true, [standard trusted CAs](
    https://requests.readthedocs.io/en/master/user/advanced/#ca-certificates) will be
  used.

In src/sensor/settings.py, the OAuth `USER_NAME` and `PASSWORD` are set to be the same
as `CLIENT_ID` and `CLIENT_SECRET`. This may need to change depending on your
authorization server.

## Actions and Hardware Support

"Actions" are one of the main concepts used by scos-sensor. At a high level, they are
the things that the sensor owner wants the sensor to be able to do. At a lower level,
they are simply Python classes with a special method `__call__`. Actions are designed
to be discovered programmatically in installed plugins. Plugins are Python packages
that are designed to be integrated into scos-sensor. The reason for using plugins to
install actions is that different actions can be offered depending on the hardware
being used. Rather than requiring a modification to scos-sensor repository, plugins
allow anyone to add additional hardware support to scos-sensor by offering new or
existing actions that use the new hardware.

Common action classes can still be re-used by plugins through the scos-actions
repository. The scos-actions repository is intended to be a dependency for every plugin
as it contains the actions base class and signals needed to interface with scos-sensor.
These actions use a common but flexible radio interface that can be implemented for new
types of hardware. This allows for action re-use by passing the radio interface and the
required hardware and measurement parameters to the constructor of these actions.
Alternatively, custom actions that support unique hardware functionality can be added
to the plugin.

The scos-actions repository can also be installed as a plugin which uses a mock signal
analyzer.

scos-sensor uses the following convention to discover actions offered by plugins: if
any Python package begins with "scos_", and contains a dictionary of actions at the
Python path `package_name.discover.actions`, these actions will automatically be
available for scheduling.

The scos-usrp plugin adds support for the Ettus B2xx line of software-defined radios.
It can also be used as an example of a plugin which adds new hardware support and
re-uses the common actions in scos-actions.

For more information on adding actions and hardware support, see [scos-actions](
https://github.com/ntia/scos-actions#development).

## Development

### Running the Sensor in Development

The following techniques can be used to make local modifications. Sections are in
order, so "Running Tests" assumes you've done the setup steps in “Requirements and
Configuration”.

#### Requirements and Configuration

It is highly recommended that you first initialize a virtual development environment
using a tool such a conda or venv. The following commands create a virtual environment
using venv and install the required dependencies for development and testing.

```python
python3 -m venv ./venv
source venv/bin/activate
python3 -m pip install --upgrade pip # upgrade to pip>=18.1
python3 -m pip install -r src/requirements-dev.txt
```

#### Running Tests

Ideally, you should add a test that covers any new feature that you add. If you've done
that, then running the included test suite is the easiest way to check that everything
is working. In any case, all tests should be run after making any local modifications
to ensure that you haven't caused a regression.

`scos-sensor` uses [pytest](https://docs.pytest.org/en/latest/) and [pytest-django](
https://pytest-django.readthedocs.io/en/latest/) for testing. Tests are organized by
[application](
https://docs.djangoproject.com/en/dev/ref/applications/#projects-and-applications), so
tests related to the scheduler are in `./src/scheduler/tests`. [tox](
https://tox.readthedocs.io/en/latest/) is a tool that can run all available tests in a
virtual environment against all supported versions of Python. Running `pytest` directly
is faster, but running `tox` is a more thorough test.

The following commands install the sensor's development requirements. We highly
recommend you initialize a virtual development environment using a tool such a `conda`
or `venv` first.

```bash
cd src
pytest          # faster, but less thorough
tox             # tests code in clean virtualenv
tox --recreate  # if you change `requirements.txt`
tox -e coverage # check where test coverage lacks
```

#### Running Docker with Local Changes

The docker-compose file and application code look for information from the environment
when run, so it's necessary to source the following file in each shell that you intend
to launch the sensor from. (HINT: it can be useful to add the `source` command to a
post-activate file in whatever virtual environment you're using).

```bash
cp env.template env     # modify if necessary, defaults are okay for testing
source ./env
```

Then, build the API docker image locally, which will satisfy the `smsntia/scos-sensor`
and `smsntia/autoheal` images in the Docker compose file and bring up the sensor.

```bash
docker-compose down
docker-compose build
docker-compose up -d
docker-compose logs --follow api
```

#### Running Development Server (Not Recommended)

Running the sensor API outside of Docker is possible but not recommended, since Django
is being asked to run without several security features it expects. See
[Common Issues](#common-issues) for some hints when running the sensor in this way. The
following steps assume you've already set up some kind of virtual environment and
installed python dev requirements from [Requirements and Configuration](
    #requirements-and-configuration).

```bash
docker-compose up -d db
cd src
./manage.py makemigrations
./manage.py migrate
./manage.py createsuperuser
./manage.py runserver
```

##### Common Issues

- The development server serves on localhost:8000, not :80
- If you get a Forbidden (403) error, close any tabs and clear any cache and cookies
  related to SCOS Sensor and try again
- If you're using a virtual environment and your signal analyzer driver is installed
  outside of it, you may need to allow access to system sitepackages. For example, if
  you're using a virtualenv called `scos-sensor`, you can remove the following text
  file: `rm -f ~/.virtualenvs/scos-sensor/lib/python3.6/no-global-site-packages.txt`,
  and thereafter use the ignore-installed flag to pip: `pip install -I -r
  requirements.txt.` This should let the devserver fall back to system sitepackages for
  the signal analyzer driver only.

### Committing

Besides running the test suite and ensuring that all tests are passed, we also expect
all Python code that's checked in to have been run through an auto-formatter.

This project uses a Python auto-formatter called Black. You probably won't like every
decision it makes, but our continuous integration test-runner will reject your commit
if it's not properly formatted.

Additionally, import statement sorting is handled by isort.

The continuous integration test-runner verifies the code is auto-formatted by checking
that neither isort nor Black would recommend any changes to the code. Occasionally,
this can fail if these two autoformatters disagree. The only time I've seen this happen
is with a commented-out import statement, which isort parses, and Black treats as a
comment. Solution: don't leave commented-out import statements in the code.

There are several ways to autoformat your code before committing. First, IDE
integration with on-save hooks is very useful. Second, there is a script,
`scripts/autoformat_python.sh`, that will run both isort and Black over the codebase.
Lastly, if you've already pip-installed the dev requirements from the section above,
you already have a utility called `pre-commit` installed that will automate setting up
this project's git pre-commit hooks. Simply type the following *once*, and each time
you make a commit, it will be appropriately autoformatted.

```bash
pre-commit install
```

You can manually run the pre-commit hooks using the following command.

```bash
pre-commit run --all-files
```

## References

- [SCOS Control Plane API Reference](<https://ntia.github.io/scos-sensor/>)
- [SCOS Data Transfer Specification](<https://github.com/NTIA/sigmf-ns-ntia>)
- [SCOS Actions](<https://github.com/NTIA/scos-actions>)
- [SCOS USRP](<https://github.com/NTIA/scos-usrp>)

## License

See [LICENSE](LICENSE.md).

## Contact

For technical questions about scos-sensor, contact Justin Haze, <jhaze@ntia.gov>
