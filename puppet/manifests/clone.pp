# Part 1: Clone/copy repo/container to sensor

class scos::clone (
  )

inherits scos

{

# Ensure common services are installed and running i.e. Puppet

  service { 'puppet':
    ensure => running,
    enable => true,
  }

  if $install_version == 'latest' {
    vcsrepo { $install_root:
      ensure   => latest, # Will use latest commit
      provider => git,
      source   => "https://${git_username}:${git_password}@github.com/NTIA/scos-sensor.git",
      revision => master,
      notify   => Exec['cleanup'],
    }
  }
  else {
    vcsrepo { $install_root:
      ensure   => latest, # Will use latest commit
      provider => git,
      source   => "https://${git_username}:${git_password}@github.com/NTIA/scos-sensor.git",
      revision => $install_version,
      notify   => Exec['cleanup'],
    }
  }

# Trigger cleanup if source changes

  exec { 'source_change':
    onlyif  => "/usr/bin/test ! -e ${install_root}/.${install_source}",
    command => "/bin/echo",
    notify  => Exec['cleanup'],
  }

# Trigger cleanup if Docker image version changes

  exec { 'source_change':
    onlyif  => "${install_root}/scripts/update_docker_images.sh",
    command => "/bin/echo",
    notify  => Exec['cleanup'],
  }

# Cleanup

  exec { 'cleanup':
    onlyif      => "/usr/bin/test -d ${install_root}",
    refreshonly => true,
    command     => "${install_root}/scripts/puppet_cleanup.sh",
    environment => [
      "REPO_ROOT=${install_root}", #Note this subtle change
    ],
#    logoutput   => true,
  }
}
