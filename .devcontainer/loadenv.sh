#!/bin/bash

#
# Import env variable (with expansion) from a dotenv file.
# Defaults to .env
#
loadenv () {
    envfile=${1:-".env"}
    if [ -f "$envfile" ]; then
        echo "Importing env: $envfile"

        # import dotenv
        export $(cat "$envfile" | sed 's/#.*//g'| xargs)

        # substitute any reference env
        # Note: Can't do this on the same line as envsubst looks in already
        # exposed env variable
        export $(echo $(cat "$envfile" | sed 's/#.*//g'| xargs) | envsubst)
    fi
}
