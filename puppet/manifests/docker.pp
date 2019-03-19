# Part 3: Start Docker container

class scos::docker (
  )

inherits scos::setup

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
        "POSTGRES_PASSWORD=${postgres_password_actual}",
        "DOMAINS=${hostname} ${hostname}.local localhost",
        "FQDN=${fqdn}",
        "IPS=${networking[ip]} 127.0.0.1",
        'GUNICORN_LOG_LEVEL=info',
        "SSL_CERT_PATH=${ssl_dir}/ssl-cert-snakeoil.pem",
        "SSL_KEY_PATH=${ssl_dir}/ssl-cert-snakeoil.key",
        "DOCKER_TAG=${install_version}",
        "SENTRY_DSN=${sentry_dsn}",
      ],
#      logoutput   => true,
    }
    notify {"*** ${hostname} is up and running. Woof! ***":}
  }

# Github logic - deploy, build & run

  if ($install_source == 'github') {
    exec {'puppet_deploy_github':
      onlyif      => "/usr/bin/test ! -e ${install_root}/.deployed",
      command     => "${install_root}/scripts/puppet_deploy_github.sh",
      timeout     => 0,
      environment => [
        "REPO_ROOT=${install_root}", #Note this subtle change
        'DEBUG=false',
        "SECRET_KEY=${secret_key}",
        "POSTGRES_PASSWORD=${postgres_password_actual}",
        "DOMAINS=${hostname} ${hostname}.local localhost",
        "FQDN=${fqdn}",
        "IPS=${networking[ip]} 127.0.0.1",
        'GUNICORN_LOG_LEVEL=info',
        "SSL_CERT_PATH=${ssl_dir}/ssl-cert-snakeoil.pem",
        "SSL_KEY_PATH=${ssl_dir}/ssl-cert-snakeoil.key",
        "DOCKER_TAG=latest", #Github should always use 'latest' in branch
        "SENTRY_DSN=${sentry_dsn}",
      ],
#      logoutput   => true,
    }
    notify {"*** ${hostname} is up and running. Woof! ***":}
  }
  notify {"*** Nginx secret key is: ${secret_key} ***":}
  notify {"*** Admin password is: ${admin_password_actual} ***":}
  notify {"*** Postgres password is: ${postgres_password_actual} ***":}
}
