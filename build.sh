#!/bin/bash
echo "Running build for haruba"
docker build -t registry.adimian.com/haruba/haruba .
docker push registry.adimian.com/haruba/haruba