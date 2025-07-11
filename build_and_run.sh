#!/bin/bash

# Stop any existing containers running on port 8081
echo "Stopping any existing containers on port 8081..."
docker ps -q --filter "expose=8081" | xargs -I {} docker stop {}

# Build the Docker image
echo "Building Docker image..."
docker build -t dockerfile .

# Run the image mapping port 8080 of the Docker container to port 8081 of the host
echo "Running Docker container on port 8081..."
echo "This might take a moment, please wait..."

if ls api/* &> /dev/null; then
    echo "Found 'api/' directory, enabling Docker logs for better troubleshooting..."
    docker run -it --rm -p 8081:8000 dockerfile
else
    echo "Running Docker container..."
    docker run -d -p 8081:8000 dockerfile
fi
