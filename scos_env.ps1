$env:API_URL = "http://192.168.70.197:80/emp/"
$env:AUTH_PASSWORD = "rfeye400251"
$env:AUTH_USER = "admin"
$env:SSH_HOST = "192.168.70.197"
$env:SSH_USER = "root"
$env:SSH_PASSWORD = "rf3y3"
$env:DOCKER_GIT_CREDENTIALS = "https://gchenNTIA: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@github.com"


$env:MOCK_SIGAN=$null
$env:MOCK_SIGAN_RANDOM=$null

$env:ADDITIONAL_USER_NAMES = ""
$env:ADDITIONAL_USER_PASSWORD = ""

$env:ADMIN_EMAIL = "admin@example.com"
$env:ADMIN_NAME = "admin"
$env:ADMIN_PASSWORD = "password"

$env:AUTHENTICATION = "TOKEN"

$env:CALLBACK_AUTHENTICATION = "TOKEN"
$env:CALLBACK_SSL_VERIFICATION = "false"
$env:CALLBACK_TIMEOUT = "2"

$env:DEBUG = "true"

$env:DOCKER_TAG = "latest"

$env:DOMAINS = "localhost $(hostname).local"

$env:ENCRYPT_DATA_FILES = "true"

$env:ENCRYPTION_KEY = python -c 'import secrets; import base64; print(base64.b64encode(secrets.token_bytes(32)).decode())'

$env:FQDN = hostname

$env:GIT_BRANCH = "git:$(git rev-parse --abbrev-ref HEAD)@$(git rev-parse --short HEAD)"
$env:GPS_MODULE = ""
$env:GPS_CLASS = ""

$env:IPS = "$((Get-NetIPAddress -AddressFamily IPv4).IPAddress -join ' ') 127.0.0.1"

$env:POSTGRES_PASSWORD = python -c 'import secrets; import base64; print(base64.b64encode(secrets.token_bytes(32)).decode())'

$env:MANAGER_FQDN = hostname
$env:MANAGER_IP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object IPAddress -ne '127.0.0.1')[0].IPAddress

$env:PATH_TO_CLIENT_CERT = "sensor01.pem"
$env:PATH_TO_VERIFY_CERT = "scos_test_ca.crt"

$env:REPO_ROOT = git rev-parse --show-toplevel

$env:SCOS_SENSOR_GIT_TAG = git describe --tags

$env:SECRET_KEY = python -c 'import secrets; print(secrets.token_urlsafe(64))'

$env:SIGAN_CLASS = "CRFSSigan"
$env:SIGAN_MODULE = "scos_crfs.hardware.crfs_sigan"
#$env:USB_DEVICE = ""
$env:DEVICE_MODEL = "RSA507A"
$env:BASE_IMAGE = "ubuntu:24.04"

$env:SSL_CA_PATH = "scos_test_ca.crt"
$env:SSL_CERT_PATH = "sensor01.pem"
$env:SSL_KEY_PATH = "sensor01.pem"

$env:SSD_DEVICE = "/dev/nvme0n1"

$env:API_SHM_SIZE = "16gb"

$env:CALIBRATION_EXPIRATION_LIMIT = "3600"

if ($env:DEBUG -eq "true") {
    $env:GUNICORN_LOG_LEVEL = "debug"
    $env:RAY_record_ref_creation_sites = "1"
} else {
    $env:GUNICORN_LOG_LEVEL = "info"
}