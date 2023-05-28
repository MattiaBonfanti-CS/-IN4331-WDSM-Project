#!/usr/bin/env bash

echo "Deleting k8s yml files..."
kubectl delete -f k8s

echo "Uninstalling Redis Helm Chart..."
helm uninstall order-db

helm uninstall payment-db

helm uninstall stock-db-0
helm uninstall stock-db-1
helm uninstall stock-db-2

echo "Removing volumes..."
kubectl delete pvc redis-data-order-db-redis-master-0 \
                   redis-data-order-db-redis-replicas-0 \
                   redis-data-payment-db-redis-master-0 \
                   redis-data-payment-db-redis-replicas-0 \
                   redis-data-stock-db-0-redis-master-0 \
                   redis-data-stock-db-0-redis-replicas-0 \
                   redis-data-stock-db-1-redis-master-0 \
                   redis-data-stock-db-1-redis-replicas-0 \
                   redis-data-stock-db-2-redis-master-0 \
                   redis-data-stock-db-2-redis-replicas-0