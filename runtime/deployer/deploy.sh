#!/bin/sh
set -e

cd /deploy   # <-- wichtig, weil WORKDIR ist /deploy im Container

CAMUNDA_URL=http://camunda:8080/engine-rest

echo "⏳ Waiting for Camunda..."
until curl -s "$CAMUNDA_URL/engine" > /dev/null; do
  sleep 5
done

echo "🚀 Deploying BPMN/DMN to Camunda..."

curl -X POST "$CAMUNDA_URL/deployment/create" \
  -F "deployment-name=custom-processes" \
  -F "deployment-source=docker" \
  -F "data=@bpmn/DMN_Test_1.bpmn" \
  -F "data=@dmn/test_1.dmn"



