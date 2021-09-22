#!/bin/bash
set -euo pipefail

while [[ $# -gt 0 ]]
do
    key="$1"
    case $key in
    --url)
	    url="$2"
	    shift
	    shift
	    ;;
	--tenant)
	    tenant="$2"
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
    esac
done

container_id=$(docker ps | grep "vsc-cumulocity-devicemanagement-agent" | awk '{ print $1 }')
echo $container_id
pytest --serial $container_id --url $url \
       --tenant $tenant \
       --username $username \
       --password $password