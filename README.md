# NTIA/ITS SCOS Sensor [![Travis CI Build Status][travis-badge]][travis-link] [![API Docs Build Status][api-docs-badge]][api-docs-link]

`scos-sensor` is [NTIA/ITS] [Spectrum Monitoring] group's work-in-progress
reference implementation of the [IEEE 802.22.3 Spectrum Characterization and
Occupancy Sensing][ieee-link] (SCOS) sensor. It is a platform for operating a
sensor, such as a software-defined radio (SDR), over a network. The goal is to
provide a robust, flexible, and secure starting point for remote spectrum
monitoring.

[NTIA/ITS]: https://its.bldrdoc.gov/
[Spectrum Monitoring]: https://www.its.bldrdoc.gov/programs/cac/spectrum-monitoring.aspx
[ieee-link]: http://www.ieee802.org/22/P802_22_3_PAR_Detail_Approved.pdf
[travis-link]: https://travis-ci.org/NTIA/scos-sensor
[travis-badge]: https://travis-ci.org/NTIA/scos-sensor.svg?branch=master
[api-docs-link]: https://ntia.github.io/scos-sensor/
[api-docs-badge]: https://img.shields.io/badge/docs-available-brightgreen.svg


## Table of Contents

- [Introduction](#introduction)
- [Quickstart](#quickstart)
- [Browsable API](#browsable-api)
- [Adding Actions](#adding-actions)
- [Architecture](#architecture)
- [Security](#security)
- [Glossary](#glossary)
- [References](#references)
- [License](#license)


## Introduction

**Note**: It may help to read the [Glossary](#glossary) first.

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
enough so that multiple sensors can be automated effectively while being simple enough
to still be useful for single-sensor deployments. For example, by advertising
capabilites and location, an owner of multiple sensors can easily filter by frequency
range, available *actions*, or geographic location. Yet, since each sensor hosts its
own [Browsable API](#browsable-api), controlling small deployments is as easy as
clicking around a website.

When a *task* acquires data, that data and a significant amount of metadata are stored
in a local database. The full metadata can be read directly through the self-hosted
website or retrieved in plain text via a single API call. Our metadata and data format
is an extension of, and compatible with, the [SigMF](https://github.com/gnuradio/sigmf)
specification. The [SCOS Data Transfer Specification](
    https://github.com/NTIA/sigmf-ns-ntia) describes the `scos` namespace.

When deploying equipment remotely, the robustness and security of software becomes a
prime concern. `scos-sensor` sits on top of a popular open-source framework (see
[Architecture](#architecture)), which provides out-of-the-box protection against cross
site scripting (XSS), cross site request forgery (CSRF), SQL injection, and
clickjacking attacks, and also enforces SSL/HTTPS (traffic encryption), host header
validation, and user session security. Two forms of user authentication are supported,
Django Rest Framework token authentication and OAuth 2 mutual TLS authentication.
`scos-sensor` requires a privileged user or service account in order to acces the
system. For more information, see [security](#security). To minimize the chance of
regressions while developing for the sensor, we have written almost 200 unit and
integration tests. See [Developing](
    DEVELOPING.md) to learn how to run the test suite.

We have tried to remove the most common hurdles to remotely deploying a sensor while
maintaining flexibility in two key areas. First, the API itself is hardware agnostic,
and the implementation assumes different hardware will be used depending on sensing
requirements (see [Supporting a Different SDR](
    DEVELOPING.md#supporting-a-different-sdr)). Second, we introduce the high-level
concept of "*actions*" (see [Writing Custom Actions](
        DEVELOPING.md#writing-custom-actions)), which gives the sensor owner control
over what the sensor can be tasked to do.

We have many of our design and development discussions right here on GitHub. If you
find a bug or have a use-case that we don't currently support, feel free to open an
issue.


## Quickstart

This section describes how to spin up a production-grade sensor in just a few commands.

We currently support Ettus USRP B2xx software-defined radios out of the box, and any
Intel-based host computer should work. ARM-based single-board computers have also been
tested, but we do not prepare pre-build Docker containers at this time.

1) Install `git`, `Docker`, and `docker-compose`.

2) Clone the repository.

```bash
$ git clone https://github.com/NTIA/scos-sensor.git
$ cd scos-sensor
```

3) Copy the environment template file and *modify* the copy if necessary, then source
it.

```bash
$ cp env.template env
$ source ./env
```

4) Run a Dockerized production-grade stack.

```bash
$ docker-compose up -d                                    # start in background
$ docker-compose exec api /src/manage.py createsuperuser  # create admin user
$ docker-compose logs --follow api                        # reattach terminal
```

## Browsable API

Opening the URL to your sensor (`localhost` if you followed the Quickstart) in a
browser, you will see a frontend to the API that allows you to do anything the JSON API
allows.

Relationships in the API are represented by URLs which you can click to navigate from
endpoint to endpoint. The full API is _discoverable_ simply by following these links:

![Browsable API Root](/docs/img/browsable_api_root.png?raw=true)

Scheduling an *action* is as simple as filling out a short form on `/schedule`:

![Browsable API Submission](/docs/img/browsable_api_submit.png?raw=true)

*Actions* that have been scheduled show up in the *schedule entry* list:

![Browsable API Schedule List](/docs/img/browsable_api_schedule_list.png?raw=true)


## Adding Actions

To expose a new action to the API, check out the available [action classes](
    src/actions). An _action class_ is a parameterized implementation of an action. If
an existing class covers your needs, you can simply add a text [config file](
    configs/actions/README.md) and restart the sensor.

If no existing action class meets your needs, see [Writing Custom Actions](
    DEVELOPING.md#writing-custom-actions).


## Architecture

`scos-sensor` uses a open source software stack that should be comfortable for
developers familiar with Python.

 - Persistent data is stored on disk in a relational database.
 - A *scheduler* thread running in a [Gunicorn] worker process periodically reads the
   *schedule* from the database and performs the associated *actions*.
 - A website and JSON RESTful API using [Django REST framework] is served over HTTPS
   via [NGINX], a high-performance web server. These provide easy administration over
   the sensor.


![SCOS Sensor Architecture Diagram](/docs/img/architecture_diagram.png?raw=true)

[Gunicorn]: http://gunicorn.org/
[NGINX]: https://www.nginx.com/
[Django REST framework]: http://www.django-rest-framework.org/

## Security
This section covers authentication, permissions, and certificates used to access the
sensor, and the authentication available for the callback URL. Two different types of
authentication are available for authenticating to the sensor and for
authenticating when using a callback URL.

### Sensor Authentication And Permissions
The sensor can be configured to authenticate using OAuth 2 with an
external authorization server or using Django Rest Framework Token Authentication.

#### Django Rest Framework Token Authentication
This is the default authentication method. To enable Django Rest Framework
Authentication, make sure `AUTHENTICATION` is set to `TOKEN` in the environment file.
Token authentication will be used if `AUTHENTICATION` set to anything other
than `OAUTH`.

A token is automatically created for each user. Django Rest Framework Token
Authentication will check that the token in the Authorization header ("Token " +
<token>) matches a user's token.

#### OAuth 2 Authentication
To enable OAuth 2 Authentication, set `AUTHENTICATION` to `OAUTH`
in the environment file. To authenticate against the API, the client will first need to
get an access token from the authorization server. Then, in each request to the
sensor, the client sends the JWT access token in the authorization header (using
"Bearer " + access token). To authenticate against the browsable API, the OAuth 2
authorization code flow is used. In the OAuth 2 authorization code flow, the user will
be redirected to the authorization server to enter their username and password before
being redirected back to the sensor.

For the authorization code flow, set `CLIENT_ID` and `CLIENT_SECRET` in the environment
file. These parameters are used by the sensor to authenticate itself to the
authorization server. Also set `OAUTH_TOKEN_URL` and `OAUTH_AUTHORIZATION_URL` to the
token and authorization endpoints of the authroization server.

The OAuth 2 access token (used both in the authorization header and authorization code
flow) signature will be verified using the public key from the `PATH_TO_JWT_PUBLIC_KEY`
setting. The access token verification checks additional properties including the access
token expiration time and client id. For scos-sensor, mutual TLS is required when using
OAuth 2 (see [Certificates](#Certificates) section below). As part of the OAuth 2
access token verification, scos-sensor will verfiy the UID in the subject of the client
certificate matches the UID in the JWT access token.

The token is expected to come from an OAuth 2 authorization server. For more
information, about OAuth 2 see https://tools.ietf.org/html/rfc6749.
[This section](https://tools.ietf.org/html/rfc6749#section-4.1) describes the
authorization code flow.

Currently, only JWS (JSON Web Signature) JWTs are supported.

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

```
openssl req -x509 -sha512 -days 365 -newkey rsa:4096 -keyout scostestca.key -out scostestca.pem
```

Generate a host certificate signing request.

```
openssl req -new -newkey rsa:4096 -keyout sensor01.key -out sensor01.csr
```

Before we proceed with openssl, we need to create a configuration file -- sensor01.ext.
It'll store some additional parameters needed during signing the certificate. Adjust
the settings in the below example for your sensor:

```
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
```
openssl x509 -req -CA scostestca.pem -CAkey scostestca.key -in sensor01.csr -out sensor01.pem -days 365 -sha256 -CAcreateserial -extfile sensor01.ext
```

If the sensor private key is encrypted, decrypt it using the following command:
```
openssl rsa -in sensor01.key -out sensor01_decrypted.key
```

Combine the sensor certificate and private key into one file:
```
cat sensor01_decrypted.key sensor01.pem > sensor01_combined.pem
```

##### Client Certificate
This certificate is required for using the sensor with mutual TLS which is required if
OAuth authentication is enabled.

Replace the brackets with the information specific to your user and organization.

```
openssl req -new -newkey rsa:4096 -keyout client.key -out client.csr -subj "/C=[2 letter country code]/ST=[state or province]/L=[locality]/O=[organization]/OU=[organizational unit]/UID=[user ID]/CN=[common name]"
```

Create client.ext with the following:

```
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

Import client.pfx into web browser.

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
optionally be enabled for token authentication and is required for OAUTH
authentication. The client certificate subject UID is only verified for OAuth 2
authentication, not for token authentication. To require client certificates, uncomment
`ssl_verify_client on;` in the [Nginx configuration file](nginx/conf.template). If you
use OCSP, also uncomment `ssl_ocsp on;`.

Copy the server certificate and server private key (sensor01_combined.pem) to
`scos-sensor/configs/certs`. Then set `SSL_CERT_PATH` and `SSL_KEY_PATH` (in the
environment file) to the path of the sensor01_combined.pem relative to configs/certs
(for file at `scos-sensor/configs/certs/sensor01_combined.pem`, set
`SSL_CERT_PATH=sensor01_combined.pem` and `SSL_KEY_PATH=sensor01_combined.pem`). For
mutual TLS/OAuth, also copy the CA certificate to the same directory. Then, set
`SSL_CA_PATH` to the path of the CA certificate relative to `configs/certs`.

If you are using OAuth authentication, set `PATH_TO_JWT_PUBLIC_KEY` to the path of the
JWT public key relative to configs/certs. This public key file should correspond to the
private key of the OAuth authorization server. Alternatively, the JWT private key
created above could be used to manually sign a JWT token for testing if
`PATH_TO_JWT_PUBLIC_KEY` is set to the JWT public key created above.

If you are using client certificates, use client.pfx to connect to the API by importing
this certificate into your browser.

For callback functionality with an OAuth authorized callback URL, set
`PATH_TO_CLIENT_CERT` and `PATH_TO_VERIFY_CERT`, both relative to configs/certs.
Depending on the configuration of the callback URL server and the authorization server,
the sensor server certificate could be used as a client certificate by setting
`PATH_TO_CLIENT_CERT` to the path of sensor01_combined.pem relative to configs/certs.
Also the CA used to verify the client certificate could potentially be used to verify
the callback URL server certificate by setting `PATH_TO_VERIFY_CERT` to the same file
as used for `SSL_CA_PATH` (scostestca.pem).

#### Permissions and Users

##### Token
The API requires the user to be a superuser. New users created using the
API initially do not have superuser access. However, an admin can mark a user as a
superuser in the Sensor Configuration Portal.

##### OAuth
The API requires the user to either have an authority in the JWT token matching the the
`REQUIRED_ROLE` setting. When using JWT tokens, the user does not
have to be pre-created using the sensor's API. The API will accept any user using a
JWT token if they have an authority matching the required role setting.

### Callback URL Authentication
OAuth and Token authentication are supported for authenticating to the server
pointed to by the callback URL. Callback SSL verification can be enabled
or disabled using `CALLBACK_SSL_VERIFICATION` in the environment file.

#### Token
A simple form of token authentication is supported for the callback URL. The sensor
will send the user's (user who created the schedule) token in the authorization header
("Token " + <token>) when posting results to callback URL. The server can then verify
the token against what it originally sent to the sensor when creating the schedule.
This method of authentication for the callback URL is enabled by default. To verify it
is enabled, set `CALLBACK_AUTHENTICATION` to `TOKEN` in the environment file (this will
be enabled if `CALLBACK_AUTHENTICATION` set to anything other than `OAUTH`).
`PATH_TO_VERIFY_CERT`, in the environment file, can be used to set a CA certificate to
verify the callback URL server SSL certificate. If this is unset and
`CALLBACK_SSL_VERIFICATION` is set to true, [standard trusted CAs](
    https://requests.readthedocs.io/en/master/user/advanced/#ca-certificates) will be
used. If `CALLBACK_SSL_VERIFICATION` is not true, verification of the callback URL
server SSL certificate will not be performed.

#### OAuth
The OAuth 2 password flow is supported for callback URL authentication. The following
settings in the environment file are used to configure the OAuth 2 password flow
authentication.
- `CALLBACK_AUTHENTICATION` - set to `OAUTH`.
- `CLIENT_ID` - client ID used to authorize the client (the sensor) to the
authorization server.
- `CLIENT_SECRET` - client secret used to authorize the client (the sensor) to the
authorization server.
- `OAUTH_TOKEN_URL` - URL to get the access token.
- `PATH_TO_CLIENT_CERT` - client certificate used to authenticate to the
authorization server.
- `PATH_TO_VERIFY_CERT` - CA certificate to verify the authorization server and
callback URL server SSL certificate. If this is unset and `CALLBACK_SSL_VERIFICATION`
is set to true, [standard trusted CAs](
    https://requests.readthedocs.io/en/master/user/advanced/#ca-certificates) will be
used.

In src/sensor/settings.py, the OAuth `USER_NAME` and `PASSWORD` are set to be the same
as `CLIENT_ID` and `CLIENT_SECRET`. This may need to change depending on your
authorization server.

OAuth callback URL authentication uses the [OAuth resource owner password credentials
flow](https://tools.ietf.org/html/rfc6749#section-4.3).

## Glossary

In this section, we'll go over the high-level concepts used by `scos-sensor`.

 - *action*: A function that the sensor owner implements and exposes to the API.
   Actions are the things that the sensor owner wants the sensor to be able to *do*.
   Since actions block the scheduler while they run, they have exclusive access to the
   sensor's resources (like the SDR). Currently, there are several logical groupings of
   actions, such as those that create acquisitions, or admin-only actions that handle
   administrative tasks. However, actions can theoretically do anything a sensor owner
   can implement. Some less common (but perfectly acceptable) ideas for actions might
   be to rotate an antenna, or start streaming data over a socket and only return when
   the recipient closes the connection.

 - *acquisition*: The combination of data and metadata created by an action (though an
   action does not have to create an acquisition). Metadata is accessible directly
   though the API, while data is retrievable in an easy-to-use archive format with its
   associated metadata.

 - *admin*: A user account that has full control over the sensor and can create
   schedule entries and view, modify, or delete any other user's schedule entries or
   acquisitions. Admins can create non-privileged *user* accounts.

 - *capability*: Available actions, installation specifications (e.g., mobile or
   stationary), and operational ranges of hardware components (e.g., frequency range of
   SDR). These values are generally hard-coded by the sensor owner and rarely change.

 - *schedule*: The collection of all schedule entries (active and inactive) on the
   sensor.

 - *scheduler*: A thread responsible for executing the schedule. The scheduler reads
   the schedule at most once a second and consumes all past and present times for each
   active schedule entry until the schedule is exhausted. The latest task per schedule
   entry is then added to a priority queue, and the scheduler executes the associated
   actions and stores/POSTs task results. The scheduler operates in a simple blocking
   fashion, which significantly simplifies resource deconfliction. When executing the
   task queue, the scheduler makes a best effort to run each task at its designated
   time, but the scheduler will not cancel a running task to start another task, even
   of higher priority.

 - *schedule entry*: Describes a range of scheduler tasks. A schedule entry is at
   minimum a human readable name and an associated action. Combining different values
   of *start*, *stop*, *interval*, and *priority* allows for flexible task scheduling.
   If no start time is given, the first task is scheduled as soon as possible. If no
   stop time is given, tasks continue to be scheduled until the schedule entry is
   manually deactivated. Leaving the interval undefined results in a "one-shot" entry,
   where the scheduler deactivates the entry after a single task is scheduled. One-shot
   entries can be used with a future start time. If two tasks are scheduled to run at
   the same time, they will be run in order of *priority*. If two tasks are scheduled
   to run at the same time and have the same *priority*, execution order is
   implementation-dependent (undefined).

 - *task*: A representation of an action to be run at a specific time.

 - *task result*: A record of the outcome of a task. A result is recorded for each task
   after the action function returns, and includes metadata such as when the task
   *started*, when it *finished*, its *duration*, the *result* (`success` or
   `failure`), and a freeform *detail* string. A `TaskResult` JSON object is also
   POSTed to a schedule entry's `callback_url`, if provided.


## References

 - [SCOS Control Plane API Reference](https://ntia.github.io/scos-sensor/)
 - [SCOS Data Transfer Specification](https://github.com/NTIA/sigmf-ns-ntia)


## License

See [LICENSE](LICENSE.md).
