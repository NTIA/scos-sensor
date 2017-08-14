SCOS Sensor Setup Guide
=======================

Stuff inside backticks are `commands` to be used in terminal (without the backticks)

 - install ubuntu 16.04
    - overwrite entire disk, no encryption
    - connect to internet by setting unique static ip
    - install updates while installing
    - set username to "deploy"
    - set hostname
    - set password
    - allow auto-login, do not encrypt home dir
 - from this point on, unplug debug monitor, kbd, and mouse, and work
   remotely from another linux machine on the same subnet by using
   `ssh deploy@{HOSTNAME}.local`.
    - `sudo systemctl enable multi-user.target`  (multi-user is like server-mode)
    - `sudo systemctl set-default multi-user.target`  (disable GUI on startup)
    - `sudo systemctl isolate multi-user.target`  (shutdown GUI)
    - install docker
      # follow the instructions at
        https://docs.docker.com/engine/installation/linux/docker-ce/ubuntu/
      # WARNING: make sure and follow the correct instructions for `amd64`
      # if you're on a x86_64 (64-bit intel) processor, and for `armhf`
      # if you're on an arm-based platform.
    - check that docker is enabled at start (docker.service; enabled;)
      `systemctl status docker`
    - give `deploy` user access to docker daemon without sudo
      `sudo groupadd docker`
      `sudo usermod -aG docker $USER`
    - you must now log out and back in (end ssh session and re-connect)
    - get scos-sensor
      `git clone https://github.com/NTIA/scos-sensor`
      `cd scos-sensor`
    - get some python tools
      `sudo pip install python-pip`
      `pip install --user docker docker-compose`
      # add pip's "user local" dir tree to "deploy"'s bashrc file:
      `echo "PATH=~/.local/bin:$PATH" >> ~/.bashrc`
      `source ~/.bashrc`
      # docker-compose should now be available
      `docker-compose version`
    - Now is a good time to modify nginx config (./nginx/conf.g/scos-sensor)
      with your sensor's actual domain name or host name, and
    - Modify ./src/sensor/production_settings.py with the domain or host name
      or your sensor and ensure DEBUG=False.
    - (!! IMPORTANT !!) modify the docker-compose file's nginx volume section
      so that it mounts YOUR ssl cert pem and key instead of copy in a dummy
      cert and key
    - build the containers (this may take some to start up)
      `docker-compose build`
      # OR, on arm platforms:
      `docker-compose -f docker-compose-arm32v7.yml build`
    - create an environment variable with a secret key
      `export SECRET_KEY={YOUR SUPER SECRET KEY HERE}`
      # TODO: make SECRET_KEY survive a hardware power failure

 - at this point, the containers should be ready to run, but there are no
   authorized users of the sensor API yet, so we'll log into the container to
   create an admin user.
   - `docker run -it scossensor_sensor bash`
   - `python manage.py createsuperuser`
     # follow prompts to create an "admin" account
   - `exit`
     # commit changes to the image
   - docker commit $(docker ps -lq) scossensor_sensor
     # start the sensor and leave it attached to the current terminal session
   - `docker-compose up`
     # or start a daemon
     `docker-compose start`
