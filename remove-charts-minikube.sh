#!/usr/bin/env bash

echo "Deleting k8s yml files..."
kubectl delete -f k8s

echo "Uninstalling Redis Helm Chart..."
helm uninstall order-db
helm uninstall payment-db
helm uninstall stock-db
