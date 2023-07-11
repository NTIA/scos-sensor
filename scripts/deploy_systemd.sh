cd $REPO_ROOT
systemctl --user stop pod_scos-sensor.service
systemctl --user disable pod_scos-sensor.service
rm -f ~/.config/systemd/user/pod_scos-sensor.service
rm -f ~/.config/systemd/user/container-scos-sensor_api_1.service
rm -f ~/.config/systemd/user/container-scos-sensor_db_1.service
rm -f ~/.config/systemd/user/container-scos-sensor_nginx_1.service
rm -f ~/.config/systemd/user/default.target.wants/pod_scos-sensor.service
systemctl --user daemon-reload
systemctl --user reset-failed
rm -f *.service
podman pod rm pod_scos-sensor
sudo rm -rf dbdata
podman-compose --in-pod scos_pod --pod-args="--infra=true" --podman-run-args="--health-on-failure=restart" up --build --no-start
# use --new in below command to have systemd create the containers (above command wouldn't be needed)
podman generate systemd --files --name --pod-prefix "" pod_scos-sensor # may need to clear out old service files first
cp *.service ~/.config/systemd/user
systemctl --user enable pod_scos-sensor.service
systemctl --user daemon-reload
systemctl --user start pod_scos-sensor.service
