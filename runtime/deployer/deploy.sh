#!/bin/sh
set -e

CAMUNDA_URL=http://camunda:8080/engine-rest

echo "🚀 Deploying BPMN/DMN to Camunda..."

curl -X POST "$CAMUNDA_URL/deployment/create" \
  -F "deployment-name=custom-processes" \
  -F "deployment-source=docker" \
  -F "data=@bpmn/*.bpmn" \
  -F "data=@dmn/*.dmn"


