# YAML-Defined Schedule Initialization

To pre-load a schedule state from config files, add the following to a file ending in `.yml` in this directory.

```yaml
entry_name:
  action: action_name
  owner: username
```

The above fields are required, but any other `ScheduleEntry` object fields can be specified as well.

A full example, which will create a private entry performing the `monitor_usrp` action as user `admin` every `60` seconds, would be:

```yaml
# File: monitor_usrp.yml

monitor_usrp:
  action: monitor_usrp
  owner: admin
  is_private: true
  interval: 60
```

## Known Issues

- [ ] Because the entry is created outside of a request context, the `callback_url` field is not currently valid in yaml-defined schedule entries
