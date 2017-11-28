export UBUNTU_IMAGE="ubuntu" &> export_ubuntu.txt
if [ "$(docker ps -q -f name=testscossensor_1)" ]; then
    docker rm testscossensor_1 &> docker_rm_1_out.txt
fi
if [ -d "test_results" ]; then
    rm -r "test_results" &> rm_out.txt
fi
scripts/deploy.sh &> deploy_out.txt
docker build -f Dockerfile -t testscossensor . &> docker_build_out.txt
docker run --name testscossensor_1 -e SECRET_KEY -e DEBUG -e DOMAINS -e IPS -d testscossensor /testing_entrypoint.sh &> docker_run_out.txt
docker logs -f testscossensor_1 &> docker_logs_out.txt
docker cp testscossensor_1:/test_results . &> docker_cp_out.txt
docker rm testscossensor_1 &> docker_rm_2_out.txt
true
