#!/bin/bash
DOCKER_FILE_PATH=docker/Dockerfile
# construct build args from env
function env_build_arg() {
    BUILD_ARG_LIST=$(grep -oP '^ARG .*(?==)' docker/Dockerfile | cut -d' ' -f2-)
    BUILD_ARG_ARG=''
    for BUILD_ARG in $BUILD_ARG_LIST
    do
        ENV_BUILD_ARG=$(env | grep ^$BUILD_ARG=)
        if [ ! -z "$ENV_BUILD_ARG" ]
        then
            BUILD_ARG_ARG="$BUILD_ARG_ARG --build-arg $ENV_BUILD_ARG"
        fi
    done
    echo $BUILD_ARG_ARG
}
docker build -t dm-image -f "$DOCKER_FILE_PATH" $(env_build_arg) .
# load variables starting with "C8YDM"
docker run --env-file <(env | grep C8YDM) \
           -d -v /var/run/docker.sock:/var/run/docker.sock dm-image
