#!/usr/bin/env bash

echo "Refreshing minikube images..."
minikube image rm order:latest stock:latest user:latest
minikube image load order:latest stock:latest user:latest

echo "Installing Redis Helm Charts for the order, payment and stock databases..."
helm install -f helm-config/redis-helm-values.yaml order-db bitnami/redis --set master.service.nodePorts.redis=30000 --set replica.service.nodePorts.redis=30001
helm install -f helm-config/redis-helm-values.yaml payment-db bitnami/redis --set master.service.nodePorts.redis=30100 --set replica.service.nodePorts.redis=30101
helm install -f helm-config/redis-helm-values.yaml stock-db bitnami/redis --set master.service.nodePorts.redis=30200 --set replica.service.nodePorts.redis=30201

echo "Applying k8s yml files..."
kubectl apply -f k8s
