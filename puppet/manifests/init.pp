# Setup and present variables that will be entered via Foreman
# Source (docker/github)
# Branch or Version/Tag
# Install dir
# DB User
# SSL certs

class scos_dev (
    $install_source = Enum['docker','github'],
    $install_version = "master",
    $git_username = undef,
    $git_password = undef,
    $install_root = "/opt/scos-sensor",
    $repo_root = "/opt/scos-sensor_repo",
    $ssl_dir = "${install_root}/nginx/certs",
    $ssl_cert = undef,
    $ssl_key = undef,
    $db_admin_pw = "changeme!",
)

{

# Ensure common services are installed and running i.e. Puppet, Docker, git etc Setup secret key, DB user, SSL cert Logic to deterine docker vs. github source processes

    service { 'puppet':
        ensure => running,
        enable => true,
    }

    file { [ "$install_root", "$install_root/nginx", "$ssl_dir", "${install_root}/nginx/conf.d"]:
	ensure => 'directory',
    }

    exec { 'secret':
        onlyif => "/usr/bin/test ! -e $install_root/.secret_key",
        command => "/usr/bin/openssl rand -base64 32 > $install_root/.secret_key",
    }

    exec { 'db_superuser':
        command => "/bin/echo $db_admin_pw > $install_root/.db_superuser",
    }

    file { "$ssl_dir/ssl-cert-snakeoil.pem":
	      content => $ssl_cert,
    }

    file { "$ssl_dir/ssl-cert-snakeoil.key":
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

    if ($install_source == "github") {
        vcsrepo { "$repo_root":
            ensure   => present,
            provider => git,
            source   => 'https://${git_username}:${git_password}@github.com/NTIA/scos-sensor.git',
            revision => $install_version,
        }

	file {"${install_root}/src":
		ensure => 'directory',
		recurse => true,
		source => "${repo_root}/src",
	}

	file {"${install_root}/Dockerfile":
		ensure => present,
		source => "${repo_root}/Dockerfile",
	}

  file {"${install_root}/entrypoints":
      ensure => 'directory',
		  recurse => true,
		  source => "${repo_root}/entrypoints",
  }

  file {"${install_root}/gunicorn":
      ensure => 'directory',
		  recurse => true,
		  source => "${repo_root}/gunicorn",
  }

  file {"${install_root}/config":
      ensure => 'directory',
		  recurse => true,
		  source => "${repo_root}/config",
  }
  file {"${install_root}/scripts":
      ensure => 'directory',
		  recurse => true,
		  source => "${repo_root}/scripts",
  }

  file {"${install_root}/docker-compose.yml":
		  ensure => present,
		  source => "${repo_root}/docker-compose.yml",
	}

  exec {'puppet_deploy':
      command => "${install_root}/scripts/puppet_deploy.sh"
      environment => [
      "DEBUG=false",
      "SECRET_KEY=${secret_key}",
      "DOMAINS=${hostname} ${fqdn} ${hostname}.local localhost",
      "IPS=${networking[ip]} 127.0.0.1",
      "GUNICORN_LOG_LEVEL=info",
      "SSL_CERT_PATH=${ssl_dir}/ssl-cert-snakeoil.pem",
      "SSL_KEY_PATH=${ssl_dir}/ssl-cert-snakeoil.key",
      ]
  }

        docker::image { 'ntiaits/test_scossensor_api':
            #image_tag => 'ntiaits/test_scossensor_api',
            #docker_file => "${install_root}/Dockerfile",
	    subscribe => File["${install_root}/Dockerfile"],
            docker_dir => "${install_root}",
	    notify => Docker_compose["${install_root}/docker-compose.yml"],
	    ensure => present,
        }
    }

# Setup environment

    file { '/etc/environment':
        ensure => present,
        require => Exec['secret'],
        content => "# This file is managed by Puppet - any manual edits will be lost
DEBUG=false
SECRET_KEY='${secret_key}'
DOMAINS='${hostname} ${fqdn} ${hostname}.local localhost'
IPS='${networking[ip]} 127.0.0.1'
GUNICORN_LOG_LEVEL=info
REPO_ROOT=$install_root
SSL_CERT_PATH=${ssl_dir}/ssl-cert-snakeoil.pem
SSL_KEY_PATH=${ssl_dir}/ssl-cert-snakeoil.key",
    }

    if ($server_name_env != undef) {
        exec { 'envsubst1':
            command => "/usr/bin/envsubst \'\$DOMAINS\' < $repo_root/nginx/conf.template > $install_root/nginx/conf.d/scos-sensor.conf",
        }
    }

    file { "$install_root/db.sqlite3":
       ensure  => 'file',
       replace => 'no',
    }

# Restart

    exec { 'reboot':
        command => '/sbin/reboot',
        refreshonly => true,
    }

# Docker logic Pt 2
# Deploy & run

# Github logic Pt 2
# Deploy, build & run

    #if ($install_source == "github") {
    #    docker::image { 'ntiaits/test_scossensor_api':
    #        #image_tag => 'ntiaits/test_scossensor_api',
    #        docker_file => "${install_root}/Dockerfile",
    #        #docker_dir => "${install_root}",
    #    }
    #}

    if ($secret_key_env != undef) and ($secret_key != undef) and ($server_name_env != undef) and ($db_superuser != undef) {
        docker_compose { "${install_root}/docker-compose.yml":
            #subscribe => File['/etc/environment'],
            ensure  => present,
            scale   => {
                'api' => 1,
                'nginx' => 1,
		'autoheal' => 1,
		'ws_logger' => 1
            },
	    up_args => '--no-build',
	    require => Docker::image['ntiaits/test_scossensor_api'],
        }
        notify {"*** ${hostname} is up and running. Woof! ***":}
    }
}
