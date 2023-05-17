#!/usr/bin/env bash

echo "Refreshing minikube images..."
minikube image rm order:latest stock:latest user:latest
minikube image load order:latest stock:latest user:latest

echo "Installing Redis Helm Chart..."
helm install -f helm-config/redis-helm-values.yaml redis bitnami/redis

echo "Applying k8s yml files..."
kubectl apply -f k8s
