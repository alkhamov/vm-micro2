#!/bin/sh
set -eu

CAMUNDA_URL="http://camunda:8080/engine-rest"

echo "⏳ Waiting for Camunda..."
until curl -sf "$CAMUNDA_URL/engine" > /dev/null; do
  sleep 3
done
echo "✅ Camunda ready"

deploy_file() {
  FILE="$1"
  TYPE="$2"

  echo "➡️  Deploying $TYPE: $(basename "$FILE")"

  curl -sf -X POST "$CAMUNDA_URL/deployment/create" \
    -F "deployment-name=custom-$TYPE" \
    -F "deployment-source=docker" \
    -F "data=@$FILE" \
    > /dev/null

  echo "✅ Done: $(basename "$FILE")"
}

FOUND=false

# BPMN
if [ -d /deploy/bpmn ]; then
  for f in /deploy/bpmn/*.bpmn; do
    [ -e "$f" ] || continue
    FOUND=true
    deploy_file "$f" "bpmn"
  done
fi

# DMN
if [ -d /deploy/dmn ]; then
  for f in /deploy/dmn/*.dmn; do
    [ -e "$f" ] || continue
    FOUND=true
    deploy_file "$f" "dmn"
  done
fi

if [ "$FOUND" = false ]; then
  echo "⚠️  No BPMN or DMN files found!"
else
  echo "🚀 All deployments finished"
fi
