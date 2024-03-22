openssl req -x509 -sha512 -days 365 -newkey rsa:4096 -passout pass:"changeme" -keyout scostestca.key -out scostestca.pem -subj "/C=TC/ST=test_state/L=test_locality/O=test_org/OU=test_ou/CN=test_ca"
openssl req -new -newkey rsa:4096 -nodes -keyout localhost.key -out localhost.csr -subj "/C=TC/ST=test_state/L=test_locality/O=test_org/OU=test_ou/CN=localhost"
echo "authorityKeyIdentifier=keyid,issuer:always
basicConstraints=CA:FALSE
subjectAltName = @alt_names
subjectKeyIdentifier = hash
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth, clientAuth
[alt_names]
DNS.1 = localhost
IP.1 = 127.0.0.1" > localhost.ext
openssl x509 -req -passin pass:"changeme" -CA scostestca.pem -CAkey scostestca.key -in localhost.csr -out localhost.pem -days 365 -sha256 -CAcreateserial -extfile localhost.ext
cat localhost.key localhost.pem > localhost_combined.pem
cp scostestca.pem ../configs/certs/scos_test_ca.crt
cp localhost_combined.pem ../configs/certs/sensor01.pem
