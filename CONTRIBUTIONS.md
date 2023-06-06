# Group 16

https://github.com/MattiaBonfanti-CS/IN4331-WDSM-Project

## End term - 6 June 2023

Our contributions for the project so far are:

#### Mattia

Worked on the stock microservice, database sharding, serialized transations and locking implementation stock service, kubernetes setup, tested the system and setup additional docker-compose and kubernetes features. 

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

Worked on implementation of the payment service, database sharding, serialized transations and locking implementation payment service.

#### Dyon

Worked on implementation of the payment service, database sharding, serialized transations and locking implementation payment service.

### Issues

One major issue that we run into as a team was when we tested the connection between the ```orders``` and the ```payment``` microservices.
The ```order``` microservice was asking the ```payment``` to update the user's credit but while the payment was performing
this operation, it was sending back a request to the orders to check if that order exists. That led to a communication failure due to a
network problem. To mitigate this we created a payment object in the payment Redis database to link the payment with the ```order_id```.
We make the assumption that the ```pay``` endpoint cannot be accessed on its own so, we know that the order will exist.
This way, the payment service can check locally whether a payment for that order exists and avoid the call back to the order service and the network issue.

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
