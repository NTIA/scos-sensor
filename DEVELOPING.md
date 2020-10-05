# Developing in SCOS-Sensor

This document dives into the process of developing with this codebase. It
starts with the basics of running the sensor code with local modifications,
Lastly, it talks about the concept of "actions" and how to program a custom
action.


## Running the Sensor

The main README's Quickstart provides guidance on running the sensor in its
stock configuration. The following techniques can be used to see local
modifications. Sections are in order, so "Running Development Server" assumes
you've done the setup setups in "Running Tests", etc.


### Running Tests

`scos-sensor` depends on python3.7+.

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
$ python3 -m pip install -r requirements-dev.txt
$ pytest          # faster, but less thorough
$ tox             # tests code in clean virtualenv
$ tox --recreate  # if you change `requirements.txt`
$ tox -e coverage # check where test coverage lacks
```

### Running Production Server with Local Changes

The Docker compose file and application code looks for information from the
environment when run in production mode, so it's necessary to source the
following file in each shell that you intend to launch the sensor from. (HINT:
it can be useful to add the `source` command to a post-activate file in
whatever virtual environment you're using).

```bash
$ cp env.template env     # modify if necessary, defaults are okay for testing
$ source ./env
```

Then, build the API docker image locally, which will satisfy the
`smsntia/scos-sensor` and `smsntia/autoheal` images in the Docker compose file
and bring up the sensor.

```bash
$ docker-compose down
$ docker-compose build
$ docker-compose up -d
$ docker-compose logs --follow api
```


### Running Development Server (Not Recommended)

Running the sensor API outside of Docker is possible but not recommended, since
Django is being asked to run without several security features it expects. See
[Common Issues](#common_issues) for some hints when running the sensor in this
way. The following steps assume you've already setup some kind of virtual
environment and installed python dev requirements from [Running
Tests](#running_tests).

```bash
$ docker-compose up -d db
$ cd src
$ ./manage.py makemigrations
$ ./manage.py migrate
$ ./manage.py createsuperuser
$ ./manage.py runserver
```

### Common Issues:

- The development server serves on `localhost:8000`, not `:80`
- If you get a Forbidden (403) error, close any tabs and clear any cache and
  cookies related to SCOS Sensor and try again
- If you're using a virtual environment and your SDR driver is installed
  outside of it, you may need to allow access to system sitepackages. For
  example, if you're using a virtualenv called `scos-sensor`, you can remove
  the following text file: `rm -f
  ~/.virtualenvs/scos-sensor/lib/python3.6/no-global-site-packages.txt`, and
  thereafter use the `ignore-installed` flag to pip: `pip install -I -r
  requirements.txt`. This should let the devserver fall back to system
  sitepackages for the SDR driver only.

## Committing

Besides running the test suite and ensuring that all tests are passing, we also
expect all python code that's checked in to have been run through an
auto-formatter.

This project uses a Python auto-formatter called Black. You probably won't like
every decision it makes, but our continuous integration test-runner will reject
your commit if it's not properly formatted.

Additionally, import statement sorting is handled by `isort`.

The continuous integration test-runner verifies the code is auto-formatted by
checking that neither `isort` nor `black` would recommend any changes to the
code. Occasionally, this can fail if these two autoformatters disagree. The
only time I've seen this happen is with a commented-out import statement, which
`isort` parses, and `black` treats as a comment. Solution: don't leave
commented-out import statements in the code.

There are several ways to autoformat your code before committing. First, IDE
integration with on-save hooks is very useful. Second, there is a script,
`scripts/autoformat_python.sh`, that will run both `isort` and `black` over the
codebase. Lastly, if you've already pip-installed the dev requirements from the
section above, you already have a utility called `pre-commit` installed that
will automate setting up this project's git pre-commit hooks. Simply type the
following _once_, and each time you make a commit, it will be appropriately
autoformatted.


```bash
$ pre-commit install
```

## Actions and Hardware Support

Actions are designed to be discovered programmatically in installed packages.
Different types of hardware will each have their own repository which can be
installed as a package into scos-sensor. This allows for actions that are
specific to the hardware being used. Common action classes can still be
re-used by different types hardware through the scos-actions repository.
However, instances of these classes, known as actions, have different
parameters that are specific to the hardware being used. Also, specific
action classes can be created for specific hardware as needed.

If any Python package begins with "scos_", and contains a dictionary of
actions at the Python path <package_name>.discover.actions, these actions
will automatically be available for scheduling.

The [scos-actions](https://github.com/NTIA/scos_actions) repository is the base
repository for actions and hardware support. It contains the action classes
that can be re-used with different parameters and different hardware. It also
contains the hardware interfaces. See the
[scos-actions](https://github.com/NTIA/scos_actions) repository for more details.

The [scos-usrp](https://github.com/NTIA/scos_usrp) repository contains the USRP
hardware support and the USRP specific actions which use the base action classes
from scos-actions.
