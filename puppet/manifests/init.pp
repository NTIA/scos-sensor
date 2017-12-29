# Setup and present variables that will be entered via Foreman
# Source (docker/github)
# Branch or Version/Tag
# Install dir
# DB User
# SSL certs

class scos_dev (
  $install_source = Enum['docker','github'],
  $install_version = 'master',
  $git_username = undef,
  $git_password = undef,
  $install_root = '/opt/scos-sensor',
  $repo_root = '/opt/scos-sensor_repo',
  $ssl_dir = "${install_root}/nginx/certs",
  $ssl_cert = undef,
  $ssl_key = undef,
  $db_admin_email = undef,
  $db_admin_pw = 'changeme!',
)

{

# Ensure common services are installed and running i.e. Puppet, Docker, git etc Setup secret key, DB user, SSL cert Logic to deterine docker vs. github source processes

stage { 'first':

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

if ($install_source == 'docker') {
}

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

# Docker logic Pt 2
# Deploy & run

stage { 'last':

  if ($install_source == 'docker') {
  }

# Github logic Pt 2
# Deploy, build & run

  if ($install_source == 'github') {
    exec {'puppet_deploy':
      onlyif      => "/usr/bin/test ! -e ${install_root}/.deployed",
      command     => "${install_root}/scripts/puppet_deploy.sh"
      environment => [
      "REPO_ROOT=${install_root}",
      'DEBUG=false',
      "SECRET_KEY=${secret_key}",
      "DOMAINS=${hostname} ${fqdn} ${hostname}.local localhost",
      "IPS=${networking[ip]} 127.0.0.1",
      'GUNICORN_LOG_LEVEL=info',
      "SSL_CERT_PATH=${ssl_dir}/ssl-cert-snakeoil.pem",
      "SSL_KEY_PATH=${ssl_dir}/ssl-cert-snakeoil.key",
      ],
      logoutput   => true,
    }
    notify {"*** ${hostname} is up and running. Woof! ***":}
  }
}
Stage['first'] -> Stage['last']
}
