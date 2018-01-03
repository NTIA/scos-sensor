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

# Docker container logic Pt 1
# Check if tag changed
# Pull matching tagged github release

# Github logic Pt 1
# Check if branch changed

  if ($install_source == 'github') {
    vcsrepo { $install_root:
      ensure   => present,
      provider => git,
      source   => "https://${git_username}:${git_password}@github.com/NTIA/scos-sensor.git",
      revision => $install_version,
    }
  }
}
