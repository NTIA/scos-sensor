#!/bin/bash

# Use this script to create the `scos` Puppet module on the Puppet Master which
# will deploy the scos-sensor code to new sensors.

# Pseudocode

# determine where puppet is installed
# get a list of puppet environments on puppet master  
# user inputs which environment to deploy to, or as a common module 
# create module folder structure
# copy manifest files
# copy fact generation files
# copy scos-code files 
