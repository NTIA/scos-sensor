# Part 1: Clone/copy repo/container to sensor

class scos::clone (
  $install_source = $scos::install_source,
  $install_version = $scos::install_version,
  $git_username = $scos::git_username,
  $git_password = $scos::git_password,
  $install_root = $scos::install_root,
  $ssl_dir = $scos::ssl_dir,
  $ssl_cert = $scos::ssl_cert,
  $ssl_key = $scos::ssl_key,
  $admin_email = $scos::admin_email,
  $admin_password = $scos::admin_password,
  )

{

# Ensure common services are installed and running i.e. Puppet

  service { 'puppet':
    ensure => running,
    enable => true,
  }

  vcsrepo { $install_root:
    ensure   => latest, # Will use latest commit
    provider => git,
    source   => "https://${git_username}:${git_password}@github.com/NTIA/scos-sensor.git",
    revision => $install_version,
    notify   => Exec['cleanup'],
  }

# Trigger cleanup if source changes

  exec { 'source_change':
    onlyif  => "/usr/bin/test ! -e ${install_root}/.${install_source}",
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
