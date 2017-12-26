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
    $ubuntu_image = "ubuntu",
    $nginx_image = "nginx",
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

#    service { 'docker':
#        ensure => running,
#        enable => true,
#    }

#    package { 'git':
#        ensure => installed,
#    }

    file { [ "$install_root", "$install_root/nginx", "$ssl_dir"]:
	ensure => 'directory',
    }

    exec { 'secret':
        onlyif => "/usr/bin/test ! -e $install_root/.secret_key",
        command => "/usr/bin/openssl rand -base64 32 > $install_root/.secret_key",
        notify  => Exec['reboot'],
    }

    exec { 'db_superuser':
        command => "/bin/echo $db_admin_pw > $install_root/.db_superuser",
    }

    #exec { 'ssl_cert':
    #    command => "/bin/echo $ssl_cert > ${ssl_dir}/ssl-cert-snakeoil.pem",
    #}
    file { "$ssl_dir/ssl-cert-snakeoil.pem":
	content => $ssl_cert,
    }

    #exec { 'ssl_key':
    #    command => "/bin/echo $ssl_key > ${ssl_dir}/ssl-cert-snakeoil.key",
    #}
    file {"$ssl_dir/ssl-cert-snakeoil.key":
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
            source   => 'https://sms-ntia:LowiNkeR1@github.com/NTIA/scos-sensor.git',
            revision => $install_version,
            #user     => $git_username,
            #password => $git_password,
        }
     
         exec { 'repo_install':
            command => "/bin/cp -pr ${repo_root}/docker ${install_root}/docker && /bin/cp -r ${repo_root}/nginx ${install_root}/nginx && /bin/cp -r ${repo_root}/src ${install_root}/src && /bin/cp ${repo_root}/env.template ${install_root} && /bin/cp -r ${repo_root}/gunicorn ${install_root}/gunicorn  && /bin/cp -r ${repo_root}/config ${install_root}/config && /bin/cp -r ${repo_root}/scripts ${install_root}/scripts",
            #notify  => Service['docker'], # causes docker to run before build, maybe Exec['reboot'] instead?
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
UBUNTU_IMAGE=$ubuntu_image
NGINX_IMAGE=$nginx_image
REPO_ROOT=$install_root
SSL_CERT_PATH=${ssl_dir}/ssl-cert-snakeoil.pem
SSL_KEY_PATH=${ssl_dir}/ssl-cert-snakeoil.key",
    }

    if ($server_name_env != undef) {
        exec { 'envsubst1':
            command => "/usr/bin/envsubst \'\$DOMAINS\' < $install_root/nginx/conf.template > \
$install_root/nginx/conf.d/scos-sensor.conf",
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

    if ($install_source == "github") {
        
        exec { 'envsubst2':
            command => "/usr/bin/envsubst \'\$UBUNTU_IMAGE\' < ${install_root}/docker/Dockerfile.template > ${install_root}/Dockerfile",
        }

        docker::image { 'ntiaits/test_scossensor_api':
            #image_tag => 'ntiaits/test_scossensor_api',
#            docker_file => "${install_root}/Dockerfile",
            docker_dir => "${install_root}",
        }
    }

    if ($secret_key_env != undef) and ($secret_key != undef) and ($server_name_env != undef) and ($db_superuser != undef) {
        docker_compose { "${install_root}/docker/docker-compose.yml":
            subscribe => File['/etc/environment'], 
            ensure  => present,
            scale   => {
                'api' => 1,
                'nginx' => 1,
            },
        }
        notify {"*** ${hostname} is up and running. Woof! ***":}
    }
}
