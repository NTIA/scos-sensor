# Setup and present variables that will be entered via Foreman
# Source (docker/github)
# Branch or Version/Tag
# Install dir
# DB User
# SSL certs

class scos::setup (
  $install_source = $scos::install_source,
  $install_version = $scos::install_version,
  $git_username = $scos::git_username,
  $git_password = $scos::git_password,
  $install_root = $scos::install_root,
  $repo_root = $scos::repo_root,
  $ssl_dir = $scos::ssl_dir,
  $ssl_cert = $scos::ssl_cert,
  $ssl_key = $scos::ssl_key,
  $db_admin_email = $scos::db_admin_email,
  $db_admin_pw = $scos::db_admin_pw,
  )

{

# Ensure common services are installed and running i.e. Puppet, Docker, git etc Setup secret key, DB user, SSL cert Logic to deterine docker vs. github source processes

  service { 'puppet':
    ensure => running,
    enable => true,
  }

  file { [ $install_root, "${install_root}/nginx", $ssl_dir, "${install_root}/nginx/conf.d"]:
    ensure => 'directory',
  }

  exec { 'secret':
    onlyif  => "/usr/bin/test ! -e ${install_root}/.secret_key",
    command => "/usr/bin/openssl rand -base64 32 > ${install_root}/.secret_key",
  }

  exec { 'db_admin_pw':
    command => "/bin/echo ${db_admin_pw} > ${install_root}/.db_admin_pw",
  }

  exec { 'db_admin_email':
    command => "/bin/echo ${db_admin_email} > ${install_root}/.db_admin_email",
  }

  file { "${ssl_dir}/ssl-cert-snakeoil.pem":
    content => $ssl_cert,
  }

  file { "${ssl_dir}/ssl-cert-snakeoil.key":
    content => $ssl_key,
  }

# Docker container logic Pt 1
# Check if tag changed
# Pull matching tagged github release to temp location
# Copy only required files

# Github logic Pt 1
# Check if branch changed
# Pull github branch to temp location
# Copy entire repo to avoid overwriting secret etc.

  if ($install_source == 'github') {
    vcsrepo { $repo_root:
      ensure   => present,
      provider => git,
      source   => 'https://${git_username}:${git_password}@github.com/NTIA/scos-sensor.git',
      revision => $install_version,
    }

    file {"${install_root}/src":
      ensure  => 'directory',
      recurse => true,
      source  => "${repo_root}/src",
    }

    file {"${install_root}/Dockerfile":
      ensure => present,
      source => "${repo_root}/Dockerfile",
    }

    file {"${install_root}/entrypoints":
      ensure  => 'directory',
      recurse => true,
      source  => "${repo_root}/entrypoints",
    }

    file {"${install_root}/gunicorn":
      ensure  => 'directory',
      recurse => true,
      source  => "${repo_root}/gunicorn",
    }

    file {"${install_root}/config":
      ensure  => 'directory',
      recurse => true,
      source  => "${repo_root}/config",
    }

    file {"${install_root}/scripts":
      ensure  => 'directory',
      recurse => true,
      source  => "${repo_root}/scripts",
      mode    => '0744',
    }

    file {"${install_root}/docker-compose.yml":
      ensure => present,
      source => "${repo_root}/docker-compose.yml",
    }

  }

# Setup environment file in case of reboots
  file { '/etc/environment':
    ensure  => present,
    require => Exec['secret'],
    content => "# This file is managed by Puppet - any manual edits will be lost
DEBUG=false
SECRET_KEY='${secret_key}'
DOMAINS='${hostname} ${fqdn} ${hostname}.local localhost'
IPS='${networking[ip]} 127.0.0.1'
GUNICORN_LOG_LEVEL=info
REPO_ROOT=${install_root}
SSL_CERT_PATH=${ssl_dir}/ssl-cert-snakeoil.pem
SSL_KEY_PATH=${ssl_dir}/ssl-cert-snakeoil.key",
  }

  exec { 'envsubst1':
    onlyif      => "/usr/bin/test ! -e ${install_root}/nginx/conf.d/scos-sensor.conf",
    command     => "/usr/bin/envsubst \'\$DOMAINS\' < ${repo_root}/nginx/conf.template > ${install_root}/nginx/conf.d/scos-sensor.conf",
    environment => ["DOMAINS=${hostname} ${fqdn} ${hostname}.local localhost"],
  }

  file { "${install_root}/db.sqlite3":
    ensure  => 'file',
    replace => 'no',
  }

}
