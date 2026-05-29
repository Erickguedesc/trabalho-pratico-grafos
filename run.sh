#!/bin/bash
set -e

docker compose up -d neo4j
docker compose --profile mine up --build minerador
docker compose --profile run up --build app