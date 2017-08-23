NTIA/ITS SCOS Sensor
====================

The SCOS sensor is a remote API for any sensor that can be controlled via python.

It provides:
  - ready-made containers for x86 and arm32v7 hardware
  - TODO

![Browsable API Screenshot](docs/api_root.png)

Quickstart
----------

(See INSTALL for step-by-step instructions)

  - Install `git`, `Docker` and `docker-compose`

```bash
$ git clone https://github.com/NTIA/scos-sensor
$ cd scos-sensor
$ cp env.template env
$ ./scripts/build.sh
$ ./scripts/run.sh
$ ./scripts/createadmin.sh
```

RESTful API Reference
---------------------

 - [View PDF](docs/api/openapi.pdf)
 - [View HTML](https://rawgit.com/NTIA/scos-sensor/master/docs/api/openapi.html)
