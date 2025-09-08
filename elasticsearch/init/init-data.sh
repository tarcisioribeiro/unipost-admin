#!/bin/bash

# Wait for Elasticsearch to be ready
echo "Waiting for Elasticsearch to be ready..."
until curl -s -u elastic:$ELASTIC_PASSWORD "http://localhost:9200/_cluster/health" | grep -q '"status":"green\|yellow"'; do
  echo "Elasticsearch is not ready yet..."
  sleep 10
done

echo "Elasticsearch is ready! Basic setup completed."
echo "Dataset loading will be handled by the application container."