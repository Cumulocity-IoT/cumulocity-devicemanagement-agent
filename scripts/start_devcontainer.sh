#!/bin/bash

CERT_DIR="/root/.cumulocity/certs"
CONFIG_FILE="/root/.cumulocity/agent.ini"

scripts/generate_cert.sh \
    --serial $HOSTNAME \
    --root-name iot-ca \
    --cert-dir $CERT_DIR

# todo read config from environment variables and upload cert here

# escape forward slash for sed
CERT_DIR_ESCAPED=$(echo "$CERT_DIR" | sed 's/\//\\\//g')

cacert="$CERT_DIR_ESCAPED\/iot-ca.pem"
client_cert="$CERT_DIR_ESCAPED\/chain-$HOSTNAME.pem"
client_key="$CERT_DIR_ESCAPED\/$HOSTNAME-private-key.pem"

sed -i "s/^\(device\.id\s*=\s*\).*\$/\1$HOSTNAME/" $CONFIG_FILE
sed -i "s/^\(cacert\s*=\s*\).*\$/\1$cacert/" $CONFIG_FILE
sed -i "s/^\(client_cert\s*=\s*\).*\$/\1$client_cert/" $CONFIG_FILE
sed -i "s/^\(client_key\s*=\s*\).*\$/\1$client_key/" $CONFIG_FILE

service ssh start
