#!/bin/sh
set -e

CAMUNDA_URL=http://camunda:8080/engine-rest

# Warten bis Camunda bereit ist
echo "⏳ Waiting for Camunda..."
until curl -s "$CAMUNDA_URL/engine" > /dev/null; do
  sleep 5
done

echo "✅ Camunda ready, deploying BPMN/DMN..."

# Deploy aller Dateien
curl -X POST "$CAMUNDA_URL/deployment/create" \
  -F "deployment-name=custom-processes" \
  -F "deployment-source=docker" \
  -F "data=@dmn/test_1.dmn" 
  -F "data=@bpmn/test_2.bpmn"

echo "🚀 Deployment finished!"
