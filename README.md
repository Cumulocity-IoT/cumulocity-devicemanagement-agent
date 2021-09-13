# Cumulocity IoT Device Management Reference Agent
Cumulocity Device Management (DM) Reference Agent written in Python3 to demonstrate most of the [Device Management Capabilities](https://cumulocity.com/guides/users-guide/device-management/) of [Cumulocity IoT](https://www.softwareag.cloud/site/product/cumulocity-iot.html)

# Quick Start

To quickly run the agent just make sure that Docker is installed on your computer an run

    ./start.sh

in a console of your choice. The script will build a docker image and starting one instance afterwards.
When bootstrapping is used the docker container Id is the device Id which should be entered when registering a device in cumulocity.

To connect to your own tenant, run

```
C8YDM_MQTT_URL=<tenant domain> \
C8YDM_SECRET_C8Y__BOOTSTRAP__TENANT=<tenant ID> \
C8YDM_SECRET_C8Y__BOOTSTRAP__USER=<username used for bootstrapping> \
C8YDM_SECRET_C8Y__BOOTSTRAP__PASSWORD=<password used for bootstrapping> \
./start.sh
```

If you don't want to run within docker follow the steps below.

# Configuration

The agent can be configured via the agent.ini which must be placed in 

    {userFolder}/.cumulocity

When running in docker container the agent.ini can be mounted to the /root/.cumulocity/agent.ini

Below a reference agent.ini is proviced:

```console
[mqtt]
url = mqtt.eu-latest.cumulocity.com
port = 8883
tls = true
cert_auth = false
client_cert = s7y_pi.crt
client_key = s7y_pi.key
cacert = /etc/ssl/certs/ca-certificates.crt
ping.interval.seconds = 60

[agent]
name = dm-example-device
type = c8y_dm_example_device
main.loop.interval.seconds = 10
requiredinterval = 10
loglevel = INFO
```
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

The environment variables which with C8YDM_ prefix are mapped to configuration files.
Mapping rules:

  - Prefix C8YDM_<PREFIX>_ means what section the option belongs to
  - Upper case letters are mapped to lower case letters
  - Double underscore __ is mapped to .

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

### Using certificate authentication

You can generate certificates necessary to certficate authentication, and you can upload the generated root certificate o your tenant's trusted certificate list by executing the scripts like below:

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
