#!/bin/bash

set -euo pipefail

SCRIPT_DIR=$(cd $(dirname $0); pwd)
INTERMEDIATE_CONFIG="$SCRIPT_DIR/intermediate-config.cnf"
END_USER_CONFIG="$SCRIPT_DIR/end-user-config.cnf"

DEVICE_CERT="device-cert"

function clean() {
    local filename_prefix=$1
    rm $filename_prefix-private-key.pem \
       $filename_prefix-cert-sign-request.pem \
       $filename_prefix-cert.pem || echo "nothing to delete, continue"
}

function private_key() {
    local filename_prefix=$1
    openssl genrsa -out "$filename_prefix"-private-key.pem 2048
}

function csr() {
    local filename_prefix=$1
    local subject=$2
    openssl req -new \
        -key "$filename_prefix"-private-key.pem \
        -out "$filename_prefix"-cert-sign-request.pem \
        -extensions v3_req \
        -subj "$subject"
}

function create_root_self_signed_cert() {
    local filename_prefix=$1
    local subject
    subject="/C=EU/ST=PL/O=Iot Device Factory/CN=IotDevFactory"

    clean "$filename_prefix"
    private_key "$filename_prefix"
    csr "$filename_prefix" "$subject"

    #sign request
    openssl x509 -in "$filename_prefix"-cert-sign-request.pem \
        -out "$filename_prefix".pem \
        -req -signkey "$filename_prefix"-private-key.pem \
        -extensions v3_req \
        -extfile $INTERMEDIATE_CONFIG \
        -days 3650
}

function create_signed_cert() {
    local serial=$1
    local filename_prefix=$2
    local signing_cert_file_name_prefix=$3

    local subject
    subject="/C=EU/ST=PL/O=device/CN=$serial"

    clean "$serial"
    private_key "$filename_prefix"
    csr "$filename_prefix" "$subject"

    #sign cert request
    openssl x509 -req \
        -CA "$signing_cert_file_name_prefix".pem \
        -CAkey "$signing_cert_file_name_prefix"-private-key.pem \
        -in "$filename_prefix"-cert-sign-request.pem \
        -out "$filename_prefix".pem \
        -days 730 \
        -extensions v3_req \
        -extfile $END_USER_CONFIG \
        -CAcreateserial
}

while [[ $# -gt 0 ]]
do
    key="$1"
    case $key in
    --serial)
	    serial="$2"
	    shift
	    shift
	    ;;
	--root-name)
	    root_name="$2"
	    shift
	    shift
	    ;;
	--cert-name)
	    cert_name="$2"
	    shift
	    shift
	    ;;        
    --cert-dir)
	    cert_dir="$2"
	    shift
	    shift
	    ;;
    esac
done

mkdir -p "$cert_dir"
cd "$cert_dir"

create_root_self_signed_cert "$root_name"
create_signed_cert "$serial" "$cert_name" "$root_name"
cat "$cert_name.pem" "$root_name.pem" > "chain-cert.pem"
echo "done"
