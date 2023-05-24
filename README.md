# Group 16 -  Web-scale Data Management Project

Web-scale Data Management project structure with Python's Flask and Redis. 

### Project structure

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

### Deployment types:

#### docker-compose (local development)

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

#### minikube (local k8s cluster)

This setup is for local k8s testing to see if your k8s config works before deploying to the cloud. 

***Requirements:*** 
- You need to have minukube installed on your machine: https://minikube.sigs.k8s.io/docs/start/
- Minikube must have the `ingress` and `metrics-server` addons enabled:
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

#### kubernetes cluster (managed k8s cluster in the cloud)

Similarly to the `minikube` deployment but run the `deploy-charts-cluster.sh` in the helm step to also install an ingress to the cluster. 

***Requirements:*** You need to have access to kubectl of a k8s cluster.
