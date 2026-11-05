#!/usr/bin/env bash
# Equivalent of docker-compose.yml using plain docker commands. Run in the Codespace terminal:
#   bash deploy_containers.sh
set -euo pipefail

NETWORK="superkart-net"

echo ">> Creating the Docker network (if it does not exist)"
docker network inspect "$NETWORK" >/dev/null 2>&1 || docker network create "$NETWORK"

echo ">> Building images"
docker build -t superkart-backend  ./backend_files
docker build -t superkart-frontend ./frontend_files

echo ">> Removing old containers (if any)"
docker rm -f superkart-backend superkart-frontend >/dev/null 2>&1 || true

echo ">> Starting the backend (Flask, port 7860)"
docker run -d --name superkart-backend --network "$NETWORK" -p 7860:7860 superkart-backend

echo ">> Starting the frontend (Streamlit, port 8501)"
docker run -d --name superkart-frontend --network "$NETWORK" -p 8501:8501 \
  -e BACKEND_URL=http://superkart-backend:7860 superkart-frontend

docker ps --filter "name=superkart"
echo
echo "Backend  -> port 7860 (make it Public in the Ports tab to call the API from Colab)"
echo "Frontend -> port 8501 (open in the browser)"
