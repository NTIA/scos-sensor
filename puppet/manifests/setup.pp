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
  $admin_email = $scos::admin_email,
  $admin_password = $scos::admin_password,
  $secret_key = $scos::setup::secret_key,
  )

{

# Setup secret key, admin password, DB user, SSL cert Logic to deterine docker vs. github source processes

  file { [ $install_root, "${install_root}/nginx", $ssl_dir, "${install_root}/nginx/conf.d"]:
    ensure => 'directory',
    replace => 'false',
  }

  $secret_key = fqdn_rand_string(32)

  if ($admin_password == '') {
    $admin_password_actual = fqdn_rand_string(12)
  }
  else {
    $admin_password_actual = $admin_password
  }

  exec { 'admin_password':
    command => "/bin/echo ${admin_password_actual} > ${install_root}/.admin_password",
  }

  exec { 'admin_email':
    command => "/bin/echo ${admin_email} > ${install_root}/.admin_email",
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
