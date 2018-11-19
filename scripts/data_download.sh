#!/bin/bash

# A quick script to download data directly from a scos-sensor

# Read in settings from last run (if present)
source ./data_download.cfg

doublecheck="n"

read -e -i "$ip" -p "Enter the IP of the SCOS sensor: " ip
read -e -i "$token" -p "Enter the auth token: " token # Obtain token from "user" endpoint on the browseable api
read -e -i "$schedule" -p "Enter the schedule name you want to download from: " schedule # Obtain schedule name from "schedule" endpoint on the browseable api
read -e -i "$firstfile" -p "Enter the first file number you want to copy: " firstfile
read -e -i "$lastfile" -p "Enter the last number file you want to copy: " lastfile # See # files from the "acquisitions" endpoint on the browasble api
read -e -i "$filepath" -p "Where should these files be saved?: " filepath

printf "\n### CONFIG SUMMARY ###\n"
printf "Sensor IP: $ip\n"
printf "Auth token: $token\n"
printf "Schedule name: $schedule\n"
printf "First file to copy: $firstfile\n"
printf "Last file to copy: $lastfile\n"
printf "Save location: $filepath\n"

read -e -i "$doublecheck" -p "Check the above settings. Do you wish to proceed (y/n)? " doublecheck

# Copy files using curl
if [ $doublecheck == "y" ]; then
    for i in $(seq $firstfile $lastfile); do
        printf "Downloading ${schedule}_${i}.sigmf \n"
        curl -o $filepath/$schedule\_$i.sigmf -kLsS -H "Authorization: Token $token" https://$ip/api/v1/acquisitions/$schedule/$i/archive
    done
    printf "\n### COPY COMPLETED ###\n"
fi

# Save settings as defaults for next time
echo "ip=$ip" > ./data_download.cfg
echo "token=$token" >> ./data_download.cfg
echo "schedule=$schedule" >> ./data_download.cfg
echo "firstfile=$firstfile" >> ./data_download.cfg
echo "lastfile=$lastfile" >> ./data_download.cfg
echo "filepath=$filepath" >> ./data_download.cfg
