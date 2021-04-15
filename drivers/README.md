# SCOS Sensor Drivers Directory

This directory is mounted as a Docker volume to `/drivers` in the SCOS sensor Docker
container.

Some sensors/SDRs require drivers which cannot be packaged with their respective SCOS
plugins. Those drivers can be placed here manually, allowing them to be referenced from
within the SCOS sensor Docker container.
