#!/usr/bin/env bash

echo "Refreshing Docker images..."
docker rmi order:latest user:latest stock:latest

cd order
docker build -t order:latest .
cd ../

cd payment
docker build -t user:latest .
cd ../

cd stock
docker build -t stock:latest .
cd ../

echo "Installing Redis Helm Charts for the order, payment and stock databases..."
helm install -f helm-config/redis-helm-values.yaml order-db-0 bitnami/redis
helm install -f helm-config/redis-helm-values.yaml order-db-1 bitnami/redis
helm install -f helm-config/redis-helm-values.yaml order-db-2 bitnami/redis

helm install -f helm-config/redis-helm-values.yaml payment-db-0 bitnami/redis
helm install -f helm-config/redis-helm-values.yaml payment-db-1 bitnami/redis
helm install -f helm-config/redis-helm-values.yaml payment-db-2 bitnami/redis

helm install -f helm-config/redis-helm-values.yaml stock-db-0 bitnami/redis
helm install -f helm-config/redis-helm-values.yaml stock-db-1 bitnami/redis
helm install -f helm-config/redis-helm-values.yaml stock-db-2 bitnami/redis

echo "Installing Nginx Helm Chart to enable the ingress..."
helm install -f helm-config/nginx-helm-values.yaml nginx ingress-nginx/ingress-nginx

echo "Installing metrics-server Helm Chart to enable autoscaling..."
helm install metrics-server metrics-server/metrics-server

echo "Applying k8s yml files..."
kubectl apply -f k8s
