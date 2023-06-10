# COMP 429 Project - Distance Vector Routing Protocol Network

Project 2 implements modified Distance Vector Routing Algorithm

## SDK - Python 3.8

`python3 -m venv venv`

`source venv/bin/active`


## Structure

**dvrp-network/** is the root level with the entry point of this application.

Root also contains **dvrp/**, **tests/**, **topologies/** directories.
Add app specific implementations into packages in **dvrp/** directory.

## Formatting

VSCode has native support for Black formatter.

You need to install the package in your virtual environment.

`pip3 install black`

In *./vscode/settings.json* configuration is given so that VSCode uses Black on **.py** file save.


## To run first install local dvrp package

`pip3 install -e .`

`python3 main.py <topology-filename>.txt` (make sure this file is placed in *topologies/*)


## Currently working on...
Implementing TCP server