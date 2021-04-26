#!/bin/bash
docker build -t dm-image -f docker/Dockerfile .
docker run -d dm-image