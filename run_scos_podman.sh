#!/bin/bash
sudo -E podman-compose down
sudo podman system reset # container ids remain even after podman-compose down
sudo podman system reset # single command does not always work
sudo podman system reset
sudo killall -9 conmon # conmon not being killed by podman
sudo podman network rm scos-sensor_default
sudo rm -rf  /var/lib/cni/networks/* # https://github.com/containers/podman/issues/3759
sudo rm -rf dbdata
# using buildah due to podman-compose build networking error when running apt
sudo -E buildah bud -f ./docker/Dockerfile-api -t smsntia/scos-sensor:latest --build-arg BASE_IMAGE --build-arg DEBUG --build-arg DOCKER_GIT_CREDENTIALS .
sudo -E buildah bud -f ./docker/Dockerfile-nginx -t smsntia/nginx:latest .
sudo -E podman-compose up -d
