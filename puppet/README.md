# Foreman and Puppet
This project provides support for automatically provisioning and deploying the sensor code through the use of [The Foreman](https://www.theforeman.org) and [Puppet](https://puppet.com). This documentation does not cover the installation and setup of these tools, and assumes you are familiar with their use.

## Initial Setup

### Foreman

Provisioning is carried out through Foreman. Provisioning bare metal is largely dependent on the hardware, architecture, and distribution you wish to use on the sensor, and is outside the scope of this document. In general, three steps are performed to provision a sensor (which correlates to the three template files needed within Foreman):

* PXE template - Sets up essential OS options (e.g. keyboard layout) and configures DHCP networking
* Provisioning template - Installs selected OS, sets up partition table, and provides configuration options
* Finishing template - Configures Puppet

In Foreman, these are configured through `Hosts > Installation Media`, `Hosts > Provisioning Templates` and `Infrastructure > Provisioning Setup`. To ensure the Puppet 5 agent is installed on the sensors, a `Configure > Global Parameters` parameter was set in Foreman:

`enable-puppetlabs-puppet5-repo = true`

![Puppet 5](/docs/img/foreman_puppet5_parameter.png?raw=true)

### Puppet

The scos-sensor code is deployed through Puppet. Within this scos-sensor repo (in `/scripts`), is a bash script to copy the required `scos` Puppet module to the Puppet Master (a note on nomelcature, Puppet "modules" are synonymous with a Foreman "classes"). Clone this repo to the Puppet Master, and from within the `/scripts` directory run `./puppet_install.sh` and follow the prompts. You should not need to change the defaults. Note, this only needs to be run once.

Once the `scos` Puppet module is installed, you will need to refresh Foreman through the `Configure > Classes > Import Environment from ...` button. You should see a new `scos` class added which needs to be configured before being assigned to a sensor.

The `scos` class has the following parameters which need to be set before it can be assigned to a sensor. Default values have been provided where possible:

* `install source` -  Where the scos-sensor code will be sourced from. Either `dockerhub` or `github`. Dockerhub is primarily for production version, Github for development versions.  
* `install version` - A variable pertaining to the branch (Github) or version (Dockerhub) to be installed on the sensor. **Note, the Dockerhub version functionality isn't currently implemented. The Dockerhub version is hard-coded in [docker-compose.yml](../docker-compose.yml) to use the latest version.**
* `install root` - The location on the sensor where the scos-sensor code will be installed
* `ssl dir` - Where the nginx ssl cert will be stored
* `ssl cert` - The nginx SSL cert to be used on the sensor. You will need to use Foreman `Smart Class Parameter > ssl cert > Matchers` to assign a specific SSL cert to a single host, e.g. by matching on FQDN
* `ssl key` - The private key associated with the nginx ssl cert. You will need to use Foreman `Smart Class Parameter > ssl key > Matchers` to assign a specific private key to a single host. e.g. by matching on FQDN. Make sure this variable has the `Hidden Value` checkbox selected.
* `git password` - Github password to use when cloning the scos-sensor repository from Github to the sensor. Only required if using a Github private repository.
* `git username` - Github username to use when cloning the scos-sensor repository from Github to the sensor. Only required if using a Github private repository.
* `db admin email` - Administrator email address for the database
* `db admin password` - Administrator password for the database

![scos class](/docs/img/foreman_scos_class.png?raw=true)

In addition to the `scos` class, the sensors will also need the following classes installed and configured. The names are the modules taken from the [Puppet Forge](https://forge.puppet.com). These can be assigned to a `Configure > Host Group`, to make setup easier:

* [`puppetlabs/docker`](https://forge.puppet.com/puppetlabs/docker)
* [`docker::compose`](https://forge.puppet.com/puppetlabs/docker) - Comes with `puppetlabs/docker` module
* [`puppetlabs/git`](https://forge.puppet.com/puppetlabs/git)
* [`puppetlabs/vcsrepo`](https://forge.puppet.com/puppetlabs/vcsrepo) - Note, this will not show as a Smart Class in Foreman
* [`stankevich/python`](https://forge.puppet.com/stankevich/python)
* `scos` - only do this if you wish to assign it to every sensor in the Host Group

![Host Group](/docs/img/foreman_host_group.png?raw=true)

## Creating a New SCOS Sensor

Once you have Foreman and Puppet setup as above, the procedure for creating a new SCOS sensor is as follows. From within Foreman under `Hosts > Create Host`

### Host Tab  
*  Name - Sensor hostname. This should match the SSL cert you are assigned to it above.  
*  Host Group - Select the host group, if you are using this functionality.  
*  Deploy On - Bare Metal
*  Environment - Select the environment. This needs to match where you installed the SCOS Puppet module.  
*  Puppet Master - Leave as inherited.  
*  Puppet CA - Leave as inherited. 

![Host Tab](/docs/img/foreman_host_tab.png?raw=true)

### Operating System Tab  
*  Architecture - x86_64  
*  Operating System - Ubuntu 16.04.3 LTS  
*  Build - Checked  
*  Media - Ubuntu mirror  
*  Partition Table - Preseed default  
*  PXE loader - PXELinux BIOS  
*  Disk - Leave blank  
*  Root pass - The system root password you wish to use.

![Operating System Tab](/docs/img/foreman_os_tab.png?raw=true)

### Interfaces Tab  
* Edit the default Interface:  
  * Type - Interface  
  *  MAC Address - This must match the MAC address of the sensor NIC  
  *  DNS Name - This should match the sensor hostname above  
  *  Domain - Set what Foreman domain this sensor is being deployed to  
  *  IPv4 Subnet - Set what Foreman subnet this sensor is being deployed to  
  *  IPv6 Subnet - No subnets  
  *  IPv4 Address - The IP you want the sensor to have. Must fall within IPv4 subnet  
  *  IPv6 Address - Leave blank  
  *  Managed - Checked  
  *  Primary - Checked  
  *  Provision - Checked  
  *  Virtual NIC - Unchecked  
  
![Interfaces Tab](/docs/img/foreman_interface_tab.png?raw=true)
      
### Puppet Classes Tab  
* See required modules listed above. These can be inherited based on the `Host Group`, if you selected it. If you want to assign the `scos` class at this time, this will install the scos-sensor code automatically, otherwise you'll need to assign it individually to the sensor after provisioning using `Hosts > All Hosts > <sensor name> > Edit > Puppet Classes > +socs`   

![Puppet Classes Tab](/docs/img/foreman_puppet_tab.png?raw=true)

### Parameters Tab  
* Leave alone

![Parameters Tab](/docs/img/foreman_parameters_tab.png?raw=true)
    
### Additional Information Tab  
* Leave alone  

With all these parameters configured, select the `Submit` button. Foreman is now waiting for the sensor to contact it. You will need to go the sensor device and power it on. At startup press `F10` to select boot mode, and from there select `PXE boot`/`Network boot`. If configured correctly the sensor will contact Foreman and start building itself: installing the OS, Puppet, and the scos-sensor code.
