#!/bin/bash

# A quick script to DELETE data directly from a scos-sensor

# Read in settings from last run (if present)
source ./data_delete.cfg

doublecheck="n"

read -e -i "$ip" -p "Enter the IP of the SCOS sensor: " ip
read -e -i "$token" -p "Enter the auth token: " token # Obtain token from "user" endpoint on the browseable api
read -e -i "$schedule" -p "Enter the schedule name you want to delete from: " schedule # Obtain schedule name from "schedule" endpoint on the browseable api
read -e -i "$firstfile" -p "Enter the first file number you want to delete: " firstfile
read -e -i "$lastfile" -p "Enter the last number file you want to delete: " lastfile # See # files from the "acquisitions" endpoint on the browasble api

printf "\n### CONFIG SUMMARY ###\n"
printf "Sensor IP: $ip\n"
printf "Auth token: $token\n"
printf "Schedule name: $schedule\n"
printf "First file to copy: $firstfile\n"
printf "Last file to copy: $lastfile\n"

read -e -i "$doublecheck" -p "Check the above settings. Are you sure you want to DELETE this (y/n)? " doublecheck

# Copy files using curl
if [ $doublecheck == "y" ]; then
    for i in $(seq $firstfile $lastfile); do
        printf "Deleting ${schedule}_${i}.sigmf \n"
        curl -kLsS -H "Authorization: Token $token" -X "DELETE" https://$ip/api/v1/acquisitions/$schedule/$i
    done
    printf "\n### DELETE COMPLETED ###\n"
fi

# Save settings as defaults for next time
echo "ip=$ip" > ./data_delete.cfg
echo "token=$token" >> ./data_delete.cfg
echo "schedule=$schedule" >> ./data_delete.cfg
echo "firstfile=$firstfile" >> ./data_delete.cfg
echo "lastfile=$lastfile" >> ./data_delete.cfg
