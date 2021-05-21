# Cumulocity IoT Device Management Reference Agent
Cumulocity Device Management (DM) Reference Agent written in Python3 to demonstrate most of the Device Management Capabilities of Cumulocity IoT

# Quick Start

To quickly run the agent just make sure that Docker is installed on your computer an run

    ./start.sh

The script will build an docker image and starting one instance.
When bootstrapping is used the docker container Id is the device Id which should be entered when registering a device in cumulocity.

If you don't want to run within docker follow the steps below.

# Build

The agent can be build in multiple ways.
## Building via pip

To build the agent via pip just run

    pip install -r requirements.txt

 to install dependencies and afterwards

    pip install .

to build the agent itself.
Please note that in debian/ubuntu you need additionally install

    apt install python-apt

via apt.
## Building debian package

In order to build the .deb yourself first install python-stdeb via apt.

    apt install python-stdeb

 Afterwards run

    python setup.py --command-packages=stdeb.command bdist_deb

on the level of the setup.py.

In oder to install the debian package locally run

    apt install ./deb_dist/python-c8ydm_0.1-1_all.deb 

## Building docker image

To build a docker image you can make use of the provided [Dockerfile](./docker/Dockerfile).

Example:
```console
docker build -t dm-image -f docker/Dockerfile .
```

# Run

## Python

Before running the agent some manual steps need to be taken

1. Manually put the [config file](./config/agent.ini) into /root/.cumulocity

You can run the agent by executing

```console
sudo c8ydm.start
```
in your console when you used [Building via pip](#building-via-pip) to build and install the agent.

## apt / Debian package

Before running the agent some manual steps need to be taken

1. Manually put the [config file](./config/agent.ini) into /root/.cumulocity

You can run the agent by executing

```console
sudo c8ydm.start
```
in your console when you used [Building via deb](#building-debian-package) to build and install the agent.

## Docker

You can run the agent by executing

```console
docker run -d -v /var/run/docker.sock:/var/run/docker.sock dm-image
```
in your console when you used [Building Docker Image](#building-docker-image) to build and install the agent.

The config can be mounted the container. Otherwise the default config will be used.

# Develop

## Dev Container
The project comes with VS Code devcontainer support. Make sure you use [Visual Studio Code](https://code.visualstudio.com/) in combination with docker. Just open the project in VS Code and click on "Reopen in Dev Container".

In the background the Agent will be build and started. Also a debug/run configuration is provided so you can easilly start/debug the agent within VS Code. 

## Extending the agent

The agent knows three types of classes that it will automatically load and include from the "agentmodules" directory.

1. Sensors

        class Sensor:
          __metaclass__ = ABCMeta

          def __init__(self, serial):
            self.serial = serial

          '''
          Returns a list of SmartREST messages. Will be called every iteration of the main loop.
          '''
          @abstractmethod
          def getSensorMessages(self): pass

   Sensors are periodically polled by the main loop and published.

2. Listeners

        class Listener:
          __metaclass__ = ABCMeta

          def __init__(self, serial, agent):
            self.serial = serial
            self.agent = agent

          '''
          Callback that is executed for any operation received
          '''
          @abstractmethod
          def handleOperation(self, message): pass

          '''
          Returns a list of supported operations
          '''
          @abstractmethod
          def getSupportedOperations(self): pass

          '''
          Returns a list of supported SmartREST templates (X-Ids)
          '''
          @abstractmethod
          def getSupportedTemplates(self): pass

   Listeners are called whenever there is a message received on a subscribed topic.

3. Initializers

        class Initializer:
          __metaclass__ = ABCMeta

          def __init__(self, serial):
            self.serial = serial

          '''
          Returns a list of SmartREST messages. Will be called at the start of the agent
          '''
          @abstractmethod
          def getMessages(self): pass

   Initializers are only called once at the start of the agent.

You can take a look at the two example modules for how it can be used.

# Log & Configuration
The logfile and configuration can be found in the following directory.

    /root/.cumulocity

_____________________
These tools are provided as-is and without warranty or support. They do not constitute part of the Software AG product suite. Users are free to use, fork and modify them, subject to the license agreement. While Software AG welcomes contributions, we cannot guarantee to include every contribution in the master project.

For more information you can Ask a Question in the [Tech Community Forums](https://tech.forums.softwareag.com/tag/Cumulocity-IoT).
