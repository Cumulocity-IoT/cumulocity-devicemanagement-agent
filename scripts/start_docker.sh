#!/bin/bash

set -euo pipefail

CA_NAME="iot-ca"
CERT_NAME="device-cert"

if [ -n "${C8YDM_MQTT_CERT_AUTH:-}" ] && [ $C8YDM_MQTT_CERT_AUTH = "true" ]; then
    # use container id as serial if not manual provided
    if [ -n "${C8YDM_AGENT_DEVICE__ID}" ]; then
        C8YDM_AGENT_DEVICE__ID=$HOSTNAME
        export C8YDM_AGENT_DEVICE__ID=$HOSTNAME
    fi
    
    ./scripts/generate_cert.sh \
    --serial $C8YDM_AGENT_DEVICE__ID \
    --root-name $CA_NAME \
    --cert-name $CERT_NAME \
    --cert-dir "/root/.cumulocity/certs"

    ./scripts/upload_cert.sh \
    --tenant-domain $C8YDM_MQTT_URL \
    --tenant-id $CERT_TENANT \
    --username $CERT_USER \
    --password $CERT_PASSWORD \
    --cert-path "/root/.cumulocity/certs/$CA_NAME.pem" \
    --cert-name $CA_NAME
fi

if which vncserver; then
    USER=root vncserver :1 &
fi
sleep 5s
service ssh start && exec c8ydm.start
