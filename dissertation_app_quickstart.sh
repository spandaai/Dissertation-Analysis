#!/bin/bash
# Wrapper script to call Docker/build.sh

# Navigate to the Docker directory
cd Docker || { echo "Failed to change directory to Docker"; exit 1; }

# Ensure build.sh is executable
chmod +x start.sh

# Execute the build.sh script
./start.sh
