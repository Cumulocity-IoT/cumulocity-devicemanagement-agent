#!/bin/bash

set -euo pipefail

while [[ $# -gt 0 ]]
do
    key="$1"
    case $key in
    --tenant-domain)
	    tenant_domain="$2"
	    shift
	    shift
	    ;;
    --tenant-id)
	    tenant_id="$2"
	    shift
	    shift
	    ;;
    --username)
	    username="$2"
	    shift
	    shift
	    ;;
    --password)
	    password="$2"
	    shift
	    shift
	    ;;        
	--cert-path)
	    cert_path="$2"
	    shift
	    shift
	    ;;
	--cert-name)
	    cert_name="$2"
	    shift
	    shift
	    ;;
    esac
done

cert_content=$(cat "$cert_path" | tail -n+2 | head -n-1 | tr -d '\n')

curl --location --request POST "https://$tenant_domain/tenant/tenants/$tenant_id/trusted-certificates" \
    --header "Authorization: Basic $(echo -n "$tenant_id/$username:$password" | base64 | tr -d '\n')" \
    --header "Accept: application/json" --header "Content-Type: application/json" \
    --data-raw "{\"name\":\"$cert_name\",\"certInPemFormat\":\"$cert_content\",\"status\":\"ENABLED\",\"autoRegistrationEnabled\":true}"
