# Part 1: Clone/copy repo/container to sensor

class scos::clone (
  $install_source = $scos::install_source,
  $install_version = $scos::install_version,
  $git_username = $scos::git_username,
  $git_password = $scos::git_password,
  $install_root = $scos::install_root,
#  $repo_root = $scos::repo_root,
  $ssl_dir = $scos::ssl_dir,
  $ssl_cert = $scos::ssl_cert,
  $ssl_key = $scos::ssl_key,
  $db_admin_email = $scos::db_admin_email,
  $db_admin_pw = $scos::db_admin_pw,
  )

{

# Ensure common services are installed and running i.e. Puppet

  service { 'puppet':
    ensure => running,
    enable => true,
  }

  vcsrepo { $install_root:
    ensure   => latest,
    provider => git,
    source   => "https://${git_username}:${git_password}@github.com/NTIA/scos-sensor.git",
    revision => $install_version,
    notify   => Exec['cleanup'],
  }

# Cleanup only if source/branch changes

  exec { 'cleanup':
    refreshonly => true,
    command     => "${install_root}/scripts/puppet_cleanup.sh"
  }
}
