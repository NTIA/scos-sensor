docker-compose down
sudo rm -rf /home/deploy/scos-sensor/dbdata
docker system prune -af
docker-compose build --no-cache
docker-compose up -d --force-recreate
docker-compose logs -f
