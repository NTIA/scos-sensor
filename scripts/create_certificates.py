import datetime
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography import x509
import os
import sys
import configparser
import ipaddress

from cryptography.x509 import NameOID

# https://cryptography.io/en/latest/x509/tutorial/#creating-a-self-signed-certificate
# https://realpython.com/python-https/


def gen_private_key(passphrase, save_path=None):
    key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
    print("Saving private key to " + save_path)
    if save_path:
        if not passphrase:
            encryption_algorithm=serialization.NoEncryption()
        else:
            encryption_algorithm=serialization.BestAvailableEncryption(bytes(passphrase, "utf-8"))
        with open(save_path, "wb") as private_key_file:
            private_key_file.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=encryption_algorithm
            ))
    return key

def gen_public_key(country, state, locality, organization, common_name, private_key, save_path=None, sans=[], ca=False):
    public_key = private_key.public_key()
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, country),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, state),
        x509.NameAttribute(NameOID.LOCALITY_NAME, locality),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
    ])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(public_key)
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(
            # Certificate is valid for 30 days
            datetime.datetime.utcnow() + datetime.timedelta(days=365)
        )
    )
    for san in sans:
        cert = cert.add_extension(san, critical=False)
    if ca:
        cert = cert.add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
    cert = cert.add_extension(x509.SubjectKeyIdentifier.from_public_key(public_key), critical=False)
    cert = cert.sign(private_key, hashes.SHA512()) # Sign our certificate with our private key
    
    if save_path:
        print("Saving certificate to " + save_path)
        with open(save_path, "wb") as public_key_file:
            public_key_file.write(cert.public_bytes(serialization.Encoding.PEM))
    return cert

def gen_csr(country, state, locality, organization, common_name, private_key, save_path=None):
    subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, country),
            x509.NameAttribute(
                NameOID.STATE_OR_PROVINCE_NAME, state
            ),
            x509.NameAttribute(NameOID.LOCALITY_NAME, locality),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ]
    )

    builder = (
        x509.CertificateSigningRequestBuilder()
        .subject_name(subject)
    )
    csr = builder.sign(private_key, hashes.SHA512())
    if save_path:
        with open(save_path, "wb") as csr_file:
            csr_file.write(csr.public_bytes(serialization.Encoding.PEM))
    return csr

def sign_csr(csr, ca_public_key, ca_private_key, save_path=None, sans=[]):
    builder = (
        x509.CertificateBuilder()
        .subject_name(csr.subject)
        .issuer_name(ca_public_key.subject)
        .public_key(csr.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(# Certificate is valid for 30 days
        datetime.datetime.utcnow() + datetime.timedelta(days=365))
    )

    for extension in csr.extensions:
        builder = builder.add_extension(extension.value, extension.critical)
    for san in sans:
        builder = builder.add_extension(san, critical=False)
    builder = builder.add_extension(x509.SubjectKeyIdentifier.from_public_key(csr.public_key()), critical=False)
    issuer_subject_key_identifier = ca_public_key.extensions.get_extension_for_class(x509.SubjectKeyIdentifier)
    builder = builder.add_extension(x509.AuthorityKeyIdentifier.from_issuer_subject_key_identifier(issuer_subject_key_identifier.value), critical=False)

    public_key = builder.sign(
        private_key=ca_private_key,
        algorithm=hashes.SHA512()
    )

    if save_path:
        print("Saving certificate to " + save_path)
        with open(save_path, "wb") as signed_cert_file:
            signed_cert_file.write(public_key.public_bytes(serialization.Encoding.PEM))
    return public_key

def main():
    if len(sys.argv) < 4:
        print("Usage: python create_certificates.py <ini_path> <ini_section> <key_passphrase>\n" +
              "Creates localhost certifice authority, server certificate, and client certificate " +
              "for testing.\n" +
              "If key_passphrase=\"None\", private keys will not be encrypted."
        )
        sys.exit(1)
    ini_path = sys.argv[1].strip()
    if not os.path.isabs(ini_path):
        ini_path = os.path.join(os.getcwd(), ini_path)
    ini_section = sys.argv[2].strip()
    key_passphrase = sys.argv[3].strip()
    if key_passphrase == "None":
        key_passphrase = None
    settings = configparser.ConfigParser()
    settings.read(ini_path)
    ca_private_key_save_path = None
    ca_common_name = None
    if "ca_private_key_save_path" in settings[ini_section]:
        ca_private_key_save_path = settings[ini_section]["ca_private_key_save_path"]
        if not os.path.isabs(ca_private_key_save_path):
            ca_private_key_save_path = os.path.join(os.getcwd(), ca_private_key_save_path)
    if "CA_COMMON_NAME" in settings[ini_section]:
        ca_common_name = settings[ini_section]["CA_COMMON_NAME"]
    if "ca_private_key_path" in settings[ini_section]:
        existing_ca_private_key_path = settings[ini_section]["ca_private_key_path"]
        if not os.path.isabs(existing_ca_private_key_path):
            existing_ca_private_key_path = os.path.join(os.getcwd(), existing_ca_private_key_path)
    else:
        existing_ca_private_key_path = None
    if "ca_certificate_path" in settings[ini_section]:
        existing_ca_cert_path = settings[ini_section]["ca_certificate_path"]
        if not os.path.isabs(existing_ca_cert_path):
            existing_ca_cert_path = os.path.join(os.getcwd(), existing_ca_cert_path)
    else:
        existing_ca_cert_path = None
    if (existing_ca_private_key_path and not existing_ca_cert_path) or (not existing_ca_private_key_path and existing_ca_cert_path):
        print("ca_private_key_path and ca_certificate_path both must be specified in ini file to use existing certificate authority!")
        sys.exit(1)
    existing_ca_cert = None
    existing_ca_private_key = None
    if existing_ca_cert_path and existing_ca_private_key_path:
        with open(existing_ca_cert_path, 'rb') as ca_file: 
            existing_ca_cert = x509.load_pem_x509_certificate(ca_file.read())
        with open(existing_ca_private_key_path, 'rb') as ca_key:
            existing_ca_private_key = serialization.load_pem_private_key(ca_key.read(), password=None)

    if not existing_ca_cert and not existing_ca_private_key:
        if not ca_private_key_save_path:
            raise Exception("Must specify ca_private_key_save_path in ini file when not using existing certificate authority!")
        if not ca_common_name:
            raise Exception("Must specify CA_COMMON_NAME in ini file when not using existing certificate authority!")
        # create a ca private key
        ca_private_key = gen_private_key(passphrase=key_passphrase, save_path=ca_private_key_save_path)

        # create ca public key
        ca_public_key_path = os.path.join(os.getcwd(), "src/authentication/tests/certs/scostestca.crt")
        ca_san_dns = settings[ini_section]["ca_san_dns"]
        ca_san_ip = settings[ini_section]["ca_san_ip"]
        ca_public_key = gen_public_key(
            country=settings[ini_section]["COUNTRY_NAME"],
            state=settings[ini_section]["STATE_OR_PROVINCE_NAME"],
            locality=settings[ini_section]["LOCALITY_NAME"],
            organization=settings[ini_section]["ORGANIZATION_NAME"],
            common_name=ca_common_name,
            private_key=ca_private_key,
            save_path=ca_public_key_path,
            sans=[x509.SubjectAlternativeName([x509.DNSName(ca_san_dns), x509.IPAddress(ipaddress.IPv4Address(ca_san_ip))])],
            ca=True
        )
    else:
        ca_private_key = existing_ca_private_key
        ca_public_key = existing_ca_cert

    # generate server private key
    server_private_key_path = os.path.join(os.getcwd(), "src/authentication/tests/certs/sensor01_private.pem")
    server_private_key = gen_private_key(passphrase=key_passphrase, save_path=server_private_key_path)

    # generate csr
    server_csr = gen_csr(
        country=settings[ini_section]["COUNTRY_NAME"],
        state=settings[ini_section]["STATE_OR_PROVINCE_NAME"],
        locality=settings[ini_section]["LOCALITY_NAME"],
        organization=settings[ini_section]["ORGANIZATION_NAME"],
        common_name=settings[ini_section]["SERVER_COMMON_NAME"],
        private_key=server_private_key
    )
    # sign
    server_cert_path = os.path.join(os.getcwd(), "src/authentication/tests/certs/sensor01_certificate.pem")
    server_san_dns = settings[ini_section]["server_san_dns"]
    server_san_ip = settings[ini_section]["server_san_ip"]
    sign_csr(server_csr, ca_public_key, ca_private_key, save_path=server_cert_path,
        sans=[x509.SubjectAlternativeName([x509.DNSName(server_san_dns), x509.IPAddress(ipaddress.IPv4Address(server_san_ip))])])

    # generate client private key
    client_private_key_path = os.path.join(os.getcwd(), "src/authentication/tests/certs/sensor01_client_private.pem")
    client_private_key = gen_private_key(passphrase=key_passphrase, save_path=client_private_key_path)

    # generate csr
    client_csr = gen_csr(
        country=settings[ini_section]["COUNTRY_NAME"],
        state=settings[ini_section]["STATE_OR_PROVINCE_NAME"],
        locality=settings[ini_section]["LOCALITY_NAME"],
        organization=settings[ini_section]["ORGANIZATION_NAME"],
        common_name=settings[ini_section]["CLIENT_COMMON_NAME"],
        private_key=client_private_key,
    )
    # sign
    client_cert_path = os.path.join(os.getcwd(), "src/authentication/tests/certs/sensor01_client.pem")
    client_san_dns = settings[ini_section]["client_san_dns"]
    client_san_ip = settings[ini_section]["client_san_ip"]
    sign_csr(client_csr, ca_public_key, ca_private_key, save_path=client_cert_path,
        sans=[x509.SubjectAlternativeName([x509.DNSName(client_san_dns), x509.IPAddress(ipaddress.IPv4Address(client_san_ip))])])

if __name__ == "__main__":
    main()