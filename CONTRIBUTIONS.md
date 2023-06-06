# Group 16

https://github.com/MattiaBonfanti-CS/IN4331-WDSM-Project

## End term - 6 June 2023

Our contributions for the project so far are:

#### Mattia

Worked on the stock microservice and implemented locking and serialized transactions.
Implemented Database sharding in the code and in the architecture. 
Setup kubernetes and added deployment scripts. 
Tested the system using the provided benchmark tools and setup additional docker-compose and kubernetes features. 

#### Violeta

Worked on implementation of the order service and tested the correct functioning of the system.
Implemented locks and serialized transactions in the order microservice 
and applied the transaction manager ```saga_py``` library for the checkout operation.

#### Nevena

Worked on implementation of the order service and tested the correct functioning of the system.
Implemented locks and serialized transactions in some methods in the order microservice.
Research for libraries for distributed transactions which follow either SAGA or 2PC.
Implement distributed transactions with `talepy` library for the checkout operation.

#### Taichi

Worked on implementation of the payment service, database sharding, serialized transactions and locking implementation payment service.

#### Dyon

Worked on implementation of the payment service, database sharding, serialized transactions and locking implementation payment service.

### Issues

One major issue that we run into as a team was when we tested the connection between the ```orders``` and the ```payment``` microservices.
The ```order``` microservice was asking the ```payment``` to update the user's credit but while the payment was performing
this operation, it was sending back a request to the orders to check if that order exists. That led to a communication failure due to a
network problem. To mitigate this we created a payment object in the payment Redis database to link the payment with the ```order_id```.
We make the assumption that the ```pay``` endpoint cannot be accessed on its own so, we know that the order will exist.
This way, the payment service can check locally whether a payment for that order exists and avoid the call back to the order service and the network issue.

Another issue that was very recurrent was the 504 Gateway Timeout error when we were running the Locust stress tests. 
This was because the default time out of the nginx was only 60 sec which caused some requests to start failing. 
This was fixed with more proper proxy settings in the NGINX ingress.

------------------------------------------------

## Midterm - 14 May 2023

Our contributions for the project so far are:

#### Mattia

Worked on the stock microservice, tested the system and setup additional docker-compose features. 

#### Violeta

Worked on implementation of the order service and tested the correct functioning of the system
.
#### Nevena

Worked on implementation of the order service and tested the correct functioning of the system
.
#### Taichi

Worked on implementation of the payment service.

#### Dyon

Worked on implementation of the payment service.
