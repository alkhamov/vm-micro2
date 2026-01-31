#!/bin/sh
set -e

CAMUNDA_URL=http://camunda:8080/engine-rest

echo "⏳ Waiting for Camunda to be ready..."
until curl -s "$CAMUNDA_URL/engine" > /dev/null; do
  sleep 5
done

echo "✅ Camunda is ready, deploying BPMN/DMN..."


