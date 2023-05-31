#!/usr/bin/env bash

echo "Refreshing minikube images..."
minikube image rm order:latest stock:latest user:latest
minikube image load order:latest stock:latest user:latest

echo "Installing Redis Helm Charts for the order, payment and stock databases..."
helm install -f helm-config/redis-helm-values.yaml order-db-0 bitnami/redis --set master.service.nodePorts.redis=30000 --set replica.service.nodePorts.redis=30001
helm install -f helm-config/redis-helm-values.yaml order-db-1 bitnami/redis --set master.service.nodePorts.redis=30010 --set replica.service.nodePorts.redis=30011
helm install -f helm-config/redis-helm-values.yaml order-db-2 bitnami/redis --set master.service.nodePorts.redis=30020 --set replica.service.nodePorts.redis=30021

helm install -f helm-config/redis-helm-values.yaml payment-db-0 bitnami/redis --set master.service.nodePorts.redis=30100 --set replica.service.nodePorts.redis=30101
helm install -f helm-config/redis-helm-values.yaml payment-db-1 bitnami/redis --set master.service.nodePorts.redis=30110 --set replica.service.nodePorts.redis=30111
helm install -f helm-config/redis-helm-values.yaml payment-db-2 bitnami/redis --set master.service.nodePorts.redis=30120 --set replica.service.nodePorts.redis=30121

helm install -f helm-config/redis-helm-values.yaml stock-db-0 bitnami/redis --set master.service.nodePorts.redis=30200 --set replica.service.nodePorts.redis=30201
helm install -f helm-config/redis-helm-values.yaml stock-db-1 bitnami/redis --set master.service.nodePorts.redis=30210 --set replica.service.nodePorts.redis=30211
helm install -f helm-config/redis-helm-values.yaml stock-db-2 bitnami/redis --set master.service.nodePorts.redis=30220 --set replica.service.nodePorts.redis=30221

echo "Applying k8s yml files..."
kubectl apply -f k8s
