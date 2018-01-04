# Main: Set variables, set manifest run order.

class scos

(
  $install_source = Enum['dockerhub','github'],
  $install_version = 'master',
  $git_username = undef,
  $git_password = undef,
  $install_root = '/opt/scos-sensor',
  $ssl_dir = "${install_root}/nginx/certs",
  $ssl_cert = undef,
  $ssl_key = undef,
  $db_admin_email = undef,
  $db_admin_pw = 'changeme!',
)

{

contain 'scos::clone'
contain 'scos::setup'
contain 'scos::docker'

Class['scos::clone'] -> Class['scos::setup'] -> Class['scos::docker']

}
