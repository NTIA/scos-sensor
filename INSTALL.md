SCOS Sensor Setup Guide
=======================

Stuff inside backticks are `commands` to be used in terminal

Initial OS Setup
----------------

 - Install Ubuntu 16.04
    - overwrite entire disk, no encryption
    - connect to internet by setting unique static ip
    - install updates while installing
    - set username to "deploy"
    - set hostname
    - set password
    - allow auto-login, do not encrypt home dir

From this point on, unplug debug monitor, keyboard, and mouse, and work remotely from another linux machine on the same subnet by using `ssh deploy@{HOSTNAME}.local`.

  - `sudo systemctl enable multi-user.target`  (multi-user is like server-mode)
  - `sudo systemctl set-default multi-user.target`  (disable GUI on startup)
  - `sudo systemctl isolate multi-user.target`  (shutdown GUI)

Install Necessary Software
--------------------------

  - install docker
    - follow the instructions at https://docs.docker.com/engine/installation/linux/docker-ce/ubuntu/
    - WARNING: make sure and follow the correct instructions for `amd64` if you're on a x86_64 (64-bit intel) processor, and for `armhf` if you're on an arm-based platform.
    - check that docker is enabled at start `systemctl status docker` -> `... (docker.service; enabled;)`
    - give `deploy` user access to docker daemon without sudo:
      - `sudo groupadd docker`
      - `sudo usermod -aG docker $USER`
    - you must now log out and back in (end ssh session and re-connect)
    - get scos-sensor
      - `git clone https://github.com/NTIA/scos-sensor`
      - `cd scos-sensor`
    - get some python tools
      - `sudo pip install python-pip`
      - `pip install --user docker docker-compose`
    - add pip's "user local" dir tree to "deploy"'s bashrc file:
      - `echo "PATH=~/.local/bin:$PATH" >> ~/.bashrc`
      - `source ~/.bashrc`
    - docker-compose should now be available
      - `docker-compose version`
    - Now is a good time to modify local settings
      - `cp env.template env`
      - Open `env` in your favorite editor and modify it with your sensor's actual domain name and IP. The file is designed to make its best guess, but it's better to hardcode the values if you know them.
      - Carefully note the items marked **SECUIRTY WARNING**
 - build the containers (this may take some to start up)
   - `./scripts/build.sh`


Start Sensor
------------

 - `./scripts/run.sh`

 At this point, the sensor should be running, but you need to create an admin user:

 - `./scripts/createadmin.sh`

You should now be able to navigate to `localhost` in your browser to use the browsable API.

 - Some helpful debugging commands (from the docker directory):
   - `docker-compose -p scossensor logs -f` (watch logs)
   - `docker-compose -p scossensor exec api bash` (open a shell in the container)
