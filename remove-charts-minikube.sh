#!/usr/bin/env bash

echo "Deleting k8s yml files..."
kubectl delete -f k8s

echo "Uninstalling Redis Helm Chart..."
helm uninstall redis
