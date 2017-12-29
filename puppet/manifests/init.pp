class scos

(
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

contain 'scos::setup'
contain 'scos::docker'

class {'scos::install': } -> class {'scos::docker': }

}
