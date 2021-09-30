#!/bin/bash
DOCKER_FILE_PATH=docker/Dockerfile
DOCKER_IMAGE_NAME=c8ydm-image
DOCKER_CONTAINER_NAME=c8ydm
# construct build args from env
function env_build_arg() {
    BUILD_ARG_LIST=$(grep -oP '^ARG .*(?==)' "$DOCKER_FILE_PATH" | cut -d' ' -f2-)
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
docker build -t $DOCKER_IMAGE_NAME -f "$DOCKER_FILE_PATH" $(env_build_arg) .
# check interactivity
INTERACTIVITY_ARG='-d'
if [ "${INTERACTIVE:-}" = 1 ]
then
    INTERACTIVITY_ARG='-it'
fi
# load variables starting with "C8YDM"
docker run --env-file <(env | grep C8YDM) \
           --name $DOCKER_CONTAINER_NAME --rm $INTERACTIVITY_ARG \
           -v /var/run/docker.sock:/var/run/docker.sock $DOCKER_IMAGE_NAME
