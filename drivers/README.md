# SCOS Sensor Drivers Directory

This directory is mounted as a Docker volume to `/drivers` in the scos-sensor Docker
container.

Some signal analyzers require drivers which cannot be packaged with their respective
SCOS plugins. Those drivers can be placed here manually, allowing them to be referenced
from within the scos-sensor Docker container.

A json file can be used to copy files in this directory to a required destination in
the Docker container.

Below is a sample json file. The `"source_path"` must be relative to the `drivers`
directory. The `"dest_path"` can be anywhere in the Docker container. If they do not
exist, the destination directory and parent directories will automatically be created.

```json
{
    "scos_files": [
        {
            "source_path": "test_drivers1/test1.sh",
            "dest_path": "/test_drivers/test_drivers1/new_name.sh"
        },
        {
            "source_path": "test_drivers2/test2.sh",
            "dest_path": "/test_drivers/test_drivers2/test.sh"
        }
    ]
}
```

A json file for configuring the copying of files can be placed anywhere inside the
`drivers` directory. Multiple json configuration files can be added. Any json files that
do not have `"scos_files"` will be ignored as a configuration file, but can be copied
if specified in `"source_path"`. Copying directories is not currently supported.
