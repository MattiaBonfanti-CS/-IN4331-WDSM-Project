# Group 16 -  Web-scale Data Management Project

Web-scale Data Management project structure with Python's Flask, Redis and Kubernetes.

## Project structure

* `benchmark`
    Folder containing the scripts for running the benchmark tests: stress test with Locust and consistency test.
    More information [here](benchmark/README.md)

* `env`
    Folder containing the Redis env variables for the docker-compose deployment
    
* `helm-config` 
   Helm chart values for Redis and ingress-nginx
        
* `k8s`
    Folder containing the kubernetes deployments, apps and services for the ingress, order, payment and stock services.
    
* `order`
    Folder containing the order application logic and dockerfile. 
    
* `payment`
    Folder containing the payment application logic and dockerfile. 

* `stock`
    Folder containing the stock application logic and dockerfile. 

* `test`
    Folder containing some basic correctness tests for the entire system. (Feel free to enhance them)

## Deployment types:

### docker-compose (local development)

***Requirements:*** You need to have docker and docker-compose installed on your machine.

After coding the REST endpoint logic run the following in the base folder to test if your logic is correct
(you can use the provided tests in the `\test` folder and change them as you wish):

```shell script
docker-compose up --build
```

To shut off and remove the containers run:
```shell script
docker-compose down
```

### MiniKube (local k8s cluster)

This setup is for local k8s testing to see if your k8s config works before deploying to the cloud. 

***Requirements:*** 
- You need to have MiniKube installed on your machine: https://minikube.sigs.k8s.io/docs/start/
- MiniKube must be started with at least 8GB of memory and 8 CPUs capacity:
```shell script
# To remove an existing cluster
minikube unistall

# To start the new cluster with the necessary resources
minikube start --memory 8192 --cpus 8

# Or you can set the default values in the MiniKube configuration file
minikube config set memory 8192
minikube config set cpus 8
minikube start
```
- MiniKube must have the `ingress` and `metrics-server` addons enabled:
```shell script
minikube addons enable ingress
minikube addons enable metrics-server
```
- Helm must be installed installed on your machine: https://helm.sh/docs/intro/install/

First add the Redis Chart repository to Helm:
```shell script
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
```

Then deploy the database chart as well as the services pods using:

```shell script
./deploy-charts-minikube.sh
```

To remove the deployments:

```shell script
./remove-charts-minikube.sh
```

To stop the cluster:

```shell script
minikube stop
```

### Kubernetes cluster (managed k8s cluster in the cloud)

***Requirements:*** 
- You need to have access to kubectl of a k8s cluster.
- You need to have a k8s cluster running in the cloud.
- Helm must be installed installed on your machine: https://helm.sh/docs/intro/install/

First add the Nginx, the metrics-server and Redis Chart repository to Helm:
```shell script
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server

helm repo update
```

Then deploy the database chart as well as the services pods using:

```shell script
./deploy-charts-cluster.sh
```

To remove the deployments:

```shell script
./remove-charts-cluster.sh
```

## Test

After the system has been deployed with one of the above methods, the basic tests can be run as follows:
- Update the ORDER_URL, STOCK_URL and PAYMENT_URL values in the `tests/utils.py` file with the url used to access the deployment (e.g.: docker-compose swarm, k8s ingress)
- Run the script:
```shell script
python test/test_microservices.py
```

## Contributors

IN4331 Web-scale Data Management - Group 16:
- Nevena Gincheva
- Violeta Chatalbasheva
- Taichi Uno
- Dyon van der Ende
- Mattia Bonfanti

