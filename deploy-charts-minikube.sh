#!/usr/bin/env bash

echo "Refreshing minikube images..."
minikube image rm order:latest stock:latest user:latest
minikube image load order:latest stock:latest user:latest

echo "Installing Redis Helm Charts for the order, payment and stock databases..."
helm install -f helm-config/redis-helm-values.yaml order-db bitnami/redis
helm install -f helm-config/redis-helm-values.yaml payment-db bitnami/redis
helm install -f helm-config/redis-helm-values.yaml stock-db bitnami/redis

echo "Applying k8s yml files..."
kubectl apply -f k8s
