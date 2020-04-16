#!/bin/bash

# A quick script to download data directly from a scos-sensor. Takes either user input, or a config file if specified

# Set variables
doublecheck="y"
remaining=0

# Read in config file from command line (if given)
source "$1"

# Otherwise, take user input and save the config
if [ "$1" == "" ]; then
    set -- data_download.cfg
    doublecheck="n"

    read -e -i "$ip" -p "Enter the IP of the SCOS sensor: " ip
    read -e -i "$token" -p "Enter the auth token: " token # Obtain token from "user" endpoint on the browseable api
    read -e -i "$schedule" -p "Enter the schedule name you want to download from: " schedule # Obtain schedule name from "schedule" endpoint on the browseable api
    read -e -i "$firstfile" -p "Enter the first file number you want to copy: " firstfile
    read -e -i "$lastfile" -p "Enter the last number file you want to copy: " lastfile # See # files from the "acquisitions" endpoint on the browasble api
    read -e -i "$filepath" -p "Where should these files be saved?: " filepath
    read -e -i "$cleanup" -p "Enter minimum filesize to keep (Megabytes): " cleanup

    printf "\n### CONFIG SUMMARY ###\n"
    printf "Sensor IP: $ip\n"
    printf "Auth token: $token\n"
    printf "Schedule name: $schedule\n"
    printf "First file to copy: $firstfile\n"
    printf "Last file to copy: $lastfile\n"
    printf "Save location: $filepath\n"
    printf "Minimum filesize kept: ${cleanup}MB \n"

    read -e -i "$doublecheck" -p "Check the above settings. Do you wish to proceed (y/n)? " doublecheck

    # Save settings as defaults for next time
    echo "ip=$ip" > ./$1
    echo "token=$token" >> ./$1
    echo "schedule=$schedule" >> ./$1
    echo "firstfile=$firstfile" >> ./$1
    echo "lastfile=$lastfile" >> ./$1
    echo "filepath=$filepath" >> ./$1
    echo "cleanup=$cleanup" >> ./$1
fi

# Delete files that are under minimum size
find $filepath -name "*.sigmf" -type 'f' -size -${cleanup}M -delete

# Copy files using curl
if [ $doublecheck == "y" ]; then
    printf "Copy started: `date` \n"
    for i in $(seq $firstfile $lastfile); do
        start=$SECONDS
        if [ ! -f $filepath/$schedule\_$i.sigmf ]; then
            curl -o $filepath/$schedule\_$i.sigmf -kLsS -H "Authorization: Token $token" https://$ip/api/v1/tasks/completed/$schedule/$i/archive
            # Poorly try to estimate copy time remaining
            remaining=$(( (((SECONDS - start) * (lastfile - firstfile - i) / 60) + remaining) / 2 ))
            printf "Downloaded ${schedule}_${i}.sigmf. ${remaining} mins remaining. \n"
        fi
    done
    printf "Copy finished: `date` \n"
    printf "\n### COPY COMPLETED ###\n"
fi
