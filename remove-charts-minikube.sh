#!/usr/bin/env bash

echo "Deleting k8s yml files..."
kubectl delete -f k8s

echo "Uninstalling Redis Helm Chart..."
helm uninstall order-db
helm uninstall payment-db
helm uninstall stock-db

echo "Removing volumes..."
kubectl delete pvc redis-data-order-db-redis-master-0 redis-data-order-db-redis-replicas-0 redis-data-payment-db-redis-master-0 redis-data-payment-db-redis-replicas-0 redis-data-stock-db-redis-master-0 redis-data-stock-db-redis-replicas-0