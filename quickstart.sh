#!/bin/bash
# Wrapper script to call Docker-build/build.sh
cd "$(dirname "$0")/Docker-build" && ./build.sh
