#!/bin/bash

# Start Elasticsearch in background
/usr/local/bin/docker-entrypoint.sh elasticsearch &

# Get the PID of Elasticsearch
ES_PID=$!

# Wait for Elasticsearch to be ready and run init script
(sleep 45 && /usr/share/elasticsearch/init/init-data.sh) &

# Wait for Elasticsearch process
wait $ES_PID