# Cumulocity IoT Device Management Reference Agent
Cumulocity Device Management (DM) Reference Agent written in Python3 to demonstrate most of the [Device Management Capabilities](https://cumulocity.com/guides/users-guide/device-management/) of [Cumulocity IoT](https://www.softwareag.cloud/site/product/cumulocity-iot.html)

# Quick Start

The agent can be run in a docker container or natively on a device with preferrable with linux OS (e.g raspberry pi) or any other operating system.

The docker version is mainly used to simulate a device including a SSH + VNC server for Remote Access. It can be also used to simulatoe multiple instances of the agent & devices.

The native version is mainly used when connecting physical devices with real capabilities and sensors attached.

## Docker Quick Start
To quickly run the agent you can use the [prebuild docker image](https://hub.docker.com/repository/docker/switschel/c8ydm).

    docker run switschel/c8ydm

If you want docker management included just mount the docker sock to the container by adding

    -v /var/run/docker.sock:/var/run/docker.sock

Per default Bootstrapping is used and no other information is necessary. In this case the docker **container Id** is the device Id which should be entered when [registering a device in cumulocity](https://www.cumulocity.com/guides/users-guide/device-management/#device-registration-manually).

You can find it out with:
    
    docker ps

If you don't want to use the prebuild image for any reason (e.g. you want to make changes to the docker image) just clone the repo and in a linux shell of your choice use:

    chmod +x start.sh & ./start.sh

In windows shells like PS or CMD run:
    
    start.bat
    
The script will build a docker image and starting one instance afterwards.

If you want to run the Agent without using docker you need to [build](#build) and  [run](#run) the Agent manually.

### Docker Quick Start Configuration

To configure the agent you can mount the [agent.ini](./config/agent.ini) to the docker image by using in the docker run command:

    -v {{path-to-your-local-agent.ini}}:/root/.cumulocity/agent.ini

As an alternative you can use [environment variables](#environment-variables) to overwrite the default values in the agent.ini within the image. Here is an example to change the loglevel:

    -e C8YDM_AGENT_LOGLEVEL=DEBUG

For the local docker build you can use three options to change the docker image:

1. Enable/Disable VNC as part of the docker image (1 per default)

    ```
    INSTALL_VNC=1 ./start.sh
    ```

2. By default, the docker container runs in background. If you want to run it interactively:

    ```
    INTERACTIVE=1 ./start.sh
    ```
3. Generate self-signed certificates and using certificate based authentication

    ```
    USE_CERTS=1 ./start.sh
    ```
### Quick Start with Device Certificates in docker container

The agent contains scripts for generating & uploading self-signed certificates. To use them additional informatiopn as environment variables are needed. You can use the [use_certs.env](./use_certs.env) file as a template to provide them or add the environment variables using "-e" command of docker. 

Here is an example env file to generate a self signed certificate and upload it to a target tenant:

    C8YDM_MQTT_CERT_AUTH=true
    C8YDM_MQTT_URL=mqtt.eu-latest.cumulocity.com
    CERT_TENANT=<tenantID>
    CERT_USER=<username>
    CERT_PASSWORD=<password>

The easiest way is to use the --env-file comand of docker to load it. Example:

    docker run --env-file use_certs.env switschel/c8ydm

or for the local image run after maintaining the [use_certs.env](./use_certs.env):

    USE_CERTS=1 ./start.sh

If you have your own certificates already you have multiple options to use them. In all cases you must make use of the "device.id" property in the agent.ini to set a device ID you used to generate the certificates.

**Option 1:** Mount the whole config folder to the docker container containing the certs and adapted agent.ini. Make sure that you set the properties accordingly and that the cert paths are pointing to the location /root/.cumulocity/certs: 

    -v {{path-to-your-local-config-folder}}:/root/.cumulocity/


**Option 2:** Mount the certificates and adapt the config using environment variables

**Option 3:** Before building the docker image locally copy the certs to "config/certs" folder, change the agent.ini, [build](#building-docker-image) the image and [run](#docker) the image. 


## Native

To quickly run the agent natively make sure pyhton 3.7+ and pip is installed on your computer. 
Manually put the [config file](./config/agent.ini) and the [DM_Agent.json](./config/DM_Agent.json) into the /.cumulocity folder in your **user folder**. 
For example: "/home/user1/.cumulocity" in Linux or "C:\Users\user1\\.cumulocity" in Windows.

Installation

    pip install c8ydm

To start the agent run

    c8ydm.start

and to stop run

    c8ydm.stop



# Features

## Supported Cumulocity DM Features

| **Feature**                                  | **Supported**          |
|----------------------------------------------|------------------------|
|     Device Certificates                      |     Yes                |
|     Device Bootstrapping & Registration      |     Yes                |
|     Software Updates (apt)                   |     Yes                |
|     Firmware Updates (simulated only)        |     Yes                |
|     Configuration Updates text-based         |     Yes                |
|     Configuration file-based                 |     Yes                |
|     Device Profiles                          |     Yes                |
|     Network                                  |     Yes                |
|     Device Metrics (CPU, Memory etc.)        |     Yes                |
|     Remote Logfile Requests                  |     Yes                |
|     Location Updates                         |     Yes                |
|     Remote Shell                             |     Yes                |
|     Remote Access (SSH, VNC, Passthrough)    |     Yes                |
|     Hardware Metering (CPU, Memory, HDD)     |     Yes                |
|     Raspberry PI SenseHAT                    |     Yes                |
|     Docker Management                        |     Yes                |
|     Connectivity (Mobile) Management         |     No                 |
|     Adv. Software Management                 |     Yes (apt)          |
|     Service Management                       |     Yes (docker)       |  

## Raspberry PI & SenseHAT Support

The DM Agent can run on a Raspberry PI (3+) with a SenseHAT. 
It supports:
* Reading out all sensor values of the SenseHAT (Humidity, Temperature, Acceleration, Gyroscope, Compass)
* Display Messages on the LEDs sent via Cumulocity to the Pi (c8y_Message) via Message Widget. 
* Generates Events when the Joystick is pressed in different direction.

It is suggested to run the Agent as a Service. Use [dm-agent.service](./service/dm-agent.service) to install it:
```
sudo cp ./service/dm-agent.service /etc/systemd/system/
sudo systemctl enable dm-agent.service
sudo systemctl daemon-reload
sudo service dm-agent start 
```
# Configuration

The agent can be configured via the agent.ini which must be placed in 

    {userFolder}/.cumulocity

When running in docker container the agent.ini can be mounted to the /root/.cumulocity/agent.ini

You can find a reference agent.ini [here](/config/agent.ini)

| Category | Property   | Description
| ---------|:----------:|:-----------
| mqtt     | url        | The URL of the Cumulocity MQTT endpoint
| mqtt     | port       | The Port of the Cumulocity MQTT endpoint
| mqtt     | tls        | True when using port 8883, false when using port 1883 
| mqtt     | cert_auth  | true when you want use Device Certificates for Device Authentication
| mqtt     | client_cert | Path to your cert which should be used to for Authentication
| mqtt     | client_key  | Path to your private key for Authentication
| mqtt     | ping.interval.seconds | Interval in seconds for the mqtt client to send pings to MQTT Broker to keep the connection alive.
| agent    | name       | The prefix name of the Device in Cumulocity. The serial will be attached with a "-" e.g. dm-example-device-1234567.
| agent    | type       | The Device Type in Cumulocity
| agent    | main.loop.interval.seconds | The interval in seconds sensor data will be forwarded to Cumulocity
| agent    | requiredinterval | The interval in minutes for Cumulocity to detect that the device is online/offline.
| agent    | loglevel   | The log level to write and print to file/console. 

## Environment variables

The environment variables with "C8YDM_" prefix are mapped to configuration files.
Mapping rules:

  - Prefix C8YDM_{{CATEGORY}} means what category the option belongs to
  - Upper case letters are mapped to lower case letters
  - Double underscore __ is mapped to .

Examples: 

    C8YDM_MQTT_CERT_AUTH => mqtt.cert_auth 
    C8YDM_AGENT_MAIN__LOOP__INTERVAL__SECONDS => agent.main.loop.interval.seconds

# Build

The agent can be build in multiple ways.
## Building via pip

To build the agent via pip just run (as a root user, otherwise add "sudo" prior all commands).

    pip3 install -r requirements.txt

 to install dependencies and afterwards

    pip3 install .

to build the agent itself.
Please note that in debian/ubuntu you need additionally install

    apt install python-apt

via apt.

Continue with chapter [Run](#run)
## Building debian package

In order to build the .deb yourself first install python-stdeb via apt.

    apt install python3-stdeb

 Afterwards run

    python3 setup.py --command-packages=stdeb.command bdist_deb

on the level of the setup.py.

In oder to install the debian package locally run

    apt install ./deb_dist/python-c8ydm_0.1-1_all.deb

Continue with chapter [Run](#run)

## Building docker image

To build a docker image you can make use of the provided [Dockerfile](./docker/Dockerfile).

Example:
```console
docker build -t dm-image -f docker/Dockerfile .
```

# Run

## Python

Before running the agent some manual steps need to be taken

1. Manually put the [config file](./config/agent.ini) into {userfolder}/.cumulocity

You can run the agent by executing (as root, otherwise add "sudo")

```console
c8ydm.start
```
in your console when you used [Building via pip](#building-via-pip) to build and install the agent.

## apt / debian package

Before running the agent some manual steps need to be taken

1. Manually put the [config file](./config/agent.ini) and the [DM_Agent.json](./config/DM_Agent.json) into ~/.cumulocity folder. ~ stands for the current user folder. The SmartRESTTemplate will be automatically uploaded on first start.

2. You have to install "c8y-device-proxy" via pip or using the provided deb file of the [C8Y Device Proxy](https://github.com/SoftwareAG/cumulocity-remote-access-agent/releases/download/v1.1.1/python3-c8y-device-proxy_1.1.1-1_all.deb)

You can run the agent by executing (as root, otherwise add "sudo")

```console
c8ydm.start
```
in your console when you used [Building via deb](#building-debian-package) to build and install the agent.

## Docker

You can run the agent by executing

```console
docker run -d -v /var/run/docker.sock:/var/run/docker.sock dm-image
```
in your console when you used [Building Docker Image](#building-docker-image) to build and install the agent.

The config can be mounted the container. Otherwise the default config will be used. See [Docker Quick Start Configuration](#docker-quick-start-configuration)

## Mass deployment

You can run multiple instances of an container via:

```console
. mass_start.sh 5
```

where in this example 5 is the number of agent instances.
# Develop

## Dev Container
The project comes with VS Code devcontainer support. Make sure you use [Visual Studio Code](https://code.visualstudio.com/) in combination with docker. Just open the project in VS Code and click on "Reopen in Dev Container".

In the background the Agent will be build and started. Also a debug/run configuration is provided so you can easilly start/debug the agent within VS Code. 

### Using certificate authentication

You can generate certificates necessary to certficate authentication, and you can upload the generated root certificate to your tenant's trusted certificate list by executing the scripts like below:

```
./scripts/generate_cert.sh \
--serial pyagent0001 \
--root-name iot-ca \
--cert-dir /root/.cumulocity/certs \
--cert-name device-cert

./scripts/upload_cert.sh \
--tenant-domain <tenant domain> \
--tenant-id <tenant ID> \
--username <username for the tenant> \
--password <password for the tenant> \
--cert-path /root/.cumulocity/certs/iot-ca.pem \
--cert-name <(arbitrary) displayed name of the root certificate>
```

After this, you can connect the agent to your tenant using cert authentication (with the serial `pyagent0001` in this case).

### Testing

With the agent running in the container, execute

```
./test.sh \
--url <tenant domain> \
--tenant <tenant ID> \
--username <username for the tenant> \
--password <password for the tenant>
```

to run pytest.

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
