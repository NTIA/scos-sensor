# Part 3: Start Docker container

class scos::docker (
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
  $secret_key = $scos::setup::secret_key,
  )

{

# Dockerhub logic - deploy & run

  if ($install_source == 'dockerhub') {
      exec {'puppet_deploy_dockerhub':
      onlyif      => "/usr/bin/test ! -e ${install_root}/.deployed",
      command     => "${install_root}/scripts/puppet_deploy_dockerhub.sh",
      environment => [
      "REPO_ROOT=${install_root}", #Note this subtle change
      'DEBUG=false',
      "SECRET_KEY=${secret_key}",
      "DOMAINS=${hostname} ${fqdn} ${hostname}.local localhost",
      "IPS=${networking[ip]} 127.0.0.1",
      'GUNICORN_LOG_LEVEL=info',
      "SSL_CERT_PATH=${ssl_dir}/ssl-cert-snakeoil.pem",
      "SSL_KEY_PATH=${ssl_dir}/ssl-cert-snakeoil.key"
      ],
      logoutput   => true,
    }
    notify {"*** ${hostname} is up and running. Woof! ***":}
  }

# Github logic - deploy, build & run

  if ($install_source == 'github') {
    exec {'puppet_deploy_github':
      onlyif      => "/usr/bin/test ! -e ${install_root}/.deployed",
      command     => "${install_root}/scripts/puppet_deploy_github.sh",
      environment => [
      "REPO_ROOT=${install_root}", #Note this subtle change
      'DEBUG=false',
      "SECRET_KEY=${secret_key}",
      "DOMAINS=${hostname} ${fqdn} ${hostname}.local localhost",
      "IPS=${networking[ip]} 127.0.0.1",
      'GUNICORN_LOG_LEVEL=info',
      "SSL_CERT_PATH=${ssl_dir}/ssl-cert-snakeoil.pem",
      "SSL_KEY_PATH=${ssl_dir}/ssl-cert-snakeoil.key"
      ],
      logoutput   => true,
    }
    notify {"*** ${hostname} is up and running. Woof! ***":}
  }
  notify {"*** secret_key is ${secret_key}! ***":}
}
