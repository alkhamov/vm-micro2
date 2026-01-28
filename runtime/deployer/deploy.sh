#!/bin/sh
set -e

CAMUNDA_URL="http://camunda:8080/engine-rest/deployment/create"

echo "Waiting for Camunda to be ready..."
sleep 15

echo "Deploying BPMN and DMN files..."

curl -X POST "$CAMUNDA_URL" \
  -F "deployment-name=camunda-lab-deployment" \
  -F "enable-duplicate-filtering=true" \
  -F "deploy-changed-only=true" \
  -F "bpmn=@bpmn/DMN_Test_1.bpmn" \
  -F "dmn=@dmn/test_1.dmn"

echo "Deployment finished"

