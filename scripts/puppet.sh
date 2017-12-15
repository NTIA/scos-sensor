#!/bin/bash

# Title: puppet.sh
# Author: Brad Eales
# Date: 2017-12-15
# Version 0.1

# Use this script to create the `scos` Puppet module on the Puppet Master which
# will deploy the scos-sensor code to new sensors.

## VARIABLES ##

continue="y"
common_module="n"
environment_module="y"
install_path="/etc/puppetlabs/code/environments"
install_environment="development"
path_confirmed="y"
puppet_environments=`ls -1d /etc/puppetlabs/code/environments/* | xargs -n 1 basename`

## FUNCTIONS ##

scos_copy () {
    printf "Creating module! \n"
    mkdir -p $1/scos/files 
    cp -r ../puppet/lib $1/scos
    cp -r ../puppet/manifests $1/scos
    cp ../docker/docker-compose.yml $1/scos/files
    cp -r ../nginx $1/scos/files
    cp -r ../src $1/scos/files
    cp ../env.template $1/scos/files      
    printf "\nModule created. \n"
    chown -R puppet $1/scos
}

## MAIN ##

printf "\nThis script will create a 'scos' Puppet module on a Puppet Master which will deploy the scos-sensor code to new sensors.\n"
read -e -i "$continue" -p "Do you wish to continue (y or n)? " continue

if [ $continue != "y" ]
then
    printf "Script aborted, module not installed\n"
    exit 1
fi

read -e -i "$common_module" -p "Do you wish to install as a common module (y or n)? " common_module

if [ $common_module == "y" ]
then
    install_path="/etc/puppetlabs/code/modules/"
    read -e -i "$path_confirmed" -p "Is this full install path correct: $install_path (y or n)? " path_confirmed
    if [ $path_confirmed == "y" ] 
    then
        scos_copy $install_path
    else
        printf "Script aborted, module not installed\n"
        exit 1
    fi
else
    read -e -i "$environment_module" -p "Do you wish to install as a environment module (y or n)? " environment_module
    if [ $environment_module == "y" ] 
    then
        printf "\nPuppet Environments:\n\n"
        printf "$puppet_environments\n\n"
        read -e -i "$install_environment" -p "Enter install environment: " install_environment
        install_path="$install_path/$install_environment/modules/"
        read -e -i "$path_confirmed" -p "Is this full install path correct: $install_path (y or n)? " path_confirmed
        if [ $path_confirmed == "y" ] 
        then
            scos_copy $install_path
        fi
    else
        printf "Script aborted, module not installed\n"
        exit 1
    fi
fi
