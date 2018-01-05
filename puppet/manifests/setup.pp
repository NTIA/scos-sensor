# Part 2: Setup and present variables that will be entered via Foreman

class scos::setup (
  $install_source = $scos::install_source,
  $install_version = $scos::install_version,
  $git_username = $scos::git_username,
  $git_password = $scos::git_password,
  $install_root = $scos::install_root,
  $ssl_dir = $scos::ssl_dir,
  $ssl_cert = $scos::ssl_cert,
  $ssl_key = $scos::ssl_key,
  $db_admin_email = $scos::db_admin_email,
  $db_admin_pw = $scos::db_admin_pw,
  )

{

# Setup secret key, DB user, SSL cert Logic to deterine docker vs. github source processes

  file { [ $install_root, "${install_root}/nginx", $ssl_dir, "${install_root}/nginx/conf.d"]:
    ensure => 'directory',
    replace => 'false',
  }

  $secret_key = fqdn_rand_string(32)

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

# Setup Dockerhub permanent environment file for persistance

  if ($install_source == 'dockerhub') {
    file { '/etc/environment':
      ensure  => present,
      content => "# This file is managed by Puppet - any manual edits will be lost
DEBUG=false
SECRET_KEY='${secret_key}'
DOMAINS='${hostname} ${fqdn} ${hostname}.local localhost'
IPS='${networking[ip]} 127.0.0.1'
GUNICORN_LOG_LEVEL=info
REPO_ROOT=${install_root}
SSL_CERT_PATH=${ssl_dir}/ssl-cert-snakeoil.pem
SSL_KEY_PATH=${ssl_dir}/ssl-cert-snakeoil.key
DOCKER_TAG=${install_version}", 
    }
  }

# Setup Github permanent environment file for persistance

  if ($install_source == 'github') {
    file { '/etc/environment':
      ensure  => present,
      content => "# This file is managed by Puppet - any manual edits will be lost
DEBUG=false
SECRET_KEY='${secret_key}'
DOMAINS='${hostname} ${fqdn} ${hostname}.local localhost'
IPS='${networking[ip]} 127.0.0.1'
GUNICORN_LOG_LEVEL=info
REPO_ROOT=${install_root}
SSL_CERT_PATH=${ssl_dir}/ssl-cert-snakeoil.pem
SSL_KEY_PATH=${ssl_dir}/ssl-cert-snakeoil.key
DOCKER_TAG=latest", 
    }
  }

  exec { 'envsubst1':
    onlyif      => "/usr/bin/test ! -e ${install_root}/nginx/conf.d/scos-sensor.conf",
    command     => "/usr/bin/envsubst \'\$DOMAINS\' < ${install_root}/nginx/conf.template > ${install_root}/nginx/conf.d/scos-sensor.conf",
    environment => ["DOMAINS=${hostname} ${fqdn} ${hostname}.local localhost"],
  }

  file { "${install_root}/db.sqlite3":
    ensure  => 'file',
    replace => 'no',
  }

}
