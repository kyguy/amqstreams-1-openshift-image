#!/bin/bash
set -e

SCRIPT_DIR=$(dirname $0)
MANIFESTS_DIR=${SCRIPT_DIR}/manifests

# create destination folder of manifests
mkdir -p /manifests

# Update SHAs to point to latest builds
./update_shas.py

# copy manifests files
cp -r ${MANIFESTS_DIR}/* /manifests
