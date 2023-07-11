# https://superuser.com/questions/513159/how-to-remove-systemd-services
systemctl --user stop pod_scos-sensor.service
systemctl --user disable pod_scos-sensor.service
rm -f ~/.config/systemd/user/pod_scos-sensor.service
rm -f ~/.config/systemd/user/container-scos-sensor_api_1.service
rm -f ~/.config/systemd/user/container-scos-sensor_db_1.service
rm -f ~/.config/systemd/user/container-scos-sensor_nginx_1.service
rm -f ~/.config/systemd/user/default.target.wants/pod_scos-sensor.service
systemctl --user daemon-reload
systemctl --user reset-failed
cd $REPO_ROOT
rm -f *.service
podman pod rm pod_scos-sensor
sudo rm -rf dbdata
