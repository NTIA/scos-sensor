class scos (
    $ubuntu_image = undef,
    $nginx_image = undef,
)

{
    service { 'puppet':
        ensure => running,
        enable => true,
    } 

    file { 'scos_sensor':
        source => 'puppet:///modules/scos/',
        ensure => 'directory',
        path => '/opt/scos',
        recurse => true,
    }

    exec { 'secret':
        onlyif => '/usr/bin/test ! -e /opt/scos/.secret_key',         
        command => '/usr/bin/openssl rand -base64 32 > /opt/scos/.secret_key',
        notify  => Exec['reboot'],
    }

    exec { 'db_superuser':
        onlyif => '/usr/bin/test ! -e /opt/scos/.db_superuser',
        command => '/usr/bin/openssl rand -base64 16 > /opt/scos/.db_superuser',
    }

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
NGINX_IMAGE=$nginx_image",
    }
 
    if ($server_name_env != undef) {
        exec { 'envsubst':
            command => '/usr/bin/envsubst \'$DOMAINS\' < /opt/scos/nginx/conf.d/conf.template > \
/opt/scos/nginx/conf.d/scos-sensor.conf',
        }
    }

    file { '/opt/scos/db.sqlite3':
       ensure  => 'file',
       replace => 'no',
    }

    exec { 'reboot':
        command => '/sbin/reboot',
        refreshonly => true,
    }

#    cron { 'scos_init':
#        special => 'reboot',
#        user => 'root',
#        command => '/bin/sleep 300; /opt/puppetlabs/puppet/bin/puppet agent --onetime --no-daemonize',
#    }

    if ($secret_key_env != undef) and ($secret_key != undef) and ($server_name_env != undef) and ($db_superuser != undef) {
        docker_compose { '/opt/scos/docker-compose.yml':
            subscribe => File['/etc/environment'], 
            ensure  => present,
            scale   => {
                'api' => 1,
                'nginx' => 1,
            },
        }
        notify {"*** ${hostname} is up and running. Woof! ***":}
    }

#    exec { 'ssl_cert':
#        command => "/bin/echo $nginx_ssl_cert > /opt/scos/ssl_cert",
#   

}
