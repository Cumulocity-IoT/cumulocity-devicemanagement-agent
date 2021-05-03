#!/bin/bash
docker build -t dm-image -f docker/Dockerfile .
docker run -d -v /var/run/docker.sock:/var/run/docker.sock dm-image