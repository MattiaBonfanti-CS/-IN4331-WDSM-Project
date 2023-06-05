#!/usr/bin/env bash

echo "Deleting k8s yml files..."
kubectl delete -f k8s

echo "Uninstalling Redis Helm Chart..."
helm uninstall order-db-0
helm uninstall order-db-1
helm uninstall order-db-2

helm uninstall payment-db-0
helm uninstall payment-db-1
helm uninstall payment-db-2

helm uninstall stock-db-0
helm uninstall stock-db-1
helm uninstall stock-db-2

echo "Uninstalling Nginx Chart..."
helm uninstall nginx

echo "Uninstalling metrics-server Chart..."
helm uninstall metrics-server

echo "Removing volumes..."
kubectl delete pvc redis-data-order-db-0-redis-master-0 \
                   redis-data-order-db-0-redis-replicas-0 \
                   redis-data-order-db-1-redis-master-0 \
                   redis-data-order-db-1-redis-replicas-0 \
                   redis-data-order-db-2-redis-master-0 \
                   redis-data-order-db-2-redis-replicas-0 \
                   redis-data-payment-db-0-redis-master-0 \
                   redis-data-payment-db-0-redis-replicas-0 \
                   redis-data-payment-db-1-redis-master-0 \
                   redis-data-payment-db-1-redis-replicas-0 \
                   redis-data-payment-db-2-redis-master-0 \
                   redis-data-payment-db-2-redis-replicas-0 \
                   redis-data-stock-db-0-redis-master-0 \
                   redis-data-stock-db-0-redis-replicas-0 \
                   redis-data-stock-db-1-redis-master-0 \
                   redis-data-stock-db-1-redis-replicas-0 \
                   redis-data-stock-db-2-redis-master-0 \
                   redis-data-stock-db-2-redis-replicas-0