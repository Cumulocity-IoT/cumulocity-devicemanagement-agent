#!/bin/bash

set -euo pipefail

CA_NAME="iot-ca"
CERT_NAME="device-cert"

if [ -n "${C8YDM_MQTT_CERT_AUTH:-}" ] && [ $C8YDM_MQTT_CERT_AUTH = "true" ]; then
    # use container id as serial
    ./scripts/generate_cert.sh \
    --serial $HOSTNAME \
    --root-name $CA_NAME \
    --cert-name $CERT_NAME \
    --cert-dir "/root/.cumulocity/certs"

    ./scripts/upload_cert.sh \
    --tenant-domain $C8YDM_MQTT_URL \
    --tenant-id $C8YDM_SECRET_C8Y__BOOTSTRAP__TENANT \
    --username $C8YDM_SECRET_C8Y__BOOTSTRAP__USER \
    --password $C8YDM_SECRET_C8Y__BOOTSTRAP__PASSWORD \
    --cert-path "/root/.cumulocity/certs/$CA_NAME.pem" \
    --cert-name $CA_NAME

    export C8YDM_AGENT_DEVICE__ID=$HOSTNAME
fi

service ssh start && exec c8ydm.start