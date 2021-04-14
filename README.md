# cumulocity-devicemanagement-agent
Cumulocity Reference Agent written in Python to demonstrate most of the Device Management Capabilities of Cumulocity IoT
# Building the debian package

In order to build the .deb yourself first install python-stdeb via apt. Afterwards run

    python setup.py --command-packages=stdeb.command bdist_deb

on the level of the setup.py.

# Installing the debian package

In oder to install the debian package locally run

    apt install ./deb_dist/python-c8ydm_0.1-1_all.deb 

The package is also already available under https://packagecloud.io/tyrmanuz/poc
Follow the install instructions on the repository to configure your apt to be able to install from the repository.

Additionally you need to install the following package

    apt install python-apt

Note: This is not yet bundled correctly as a dependency therefore manual installation is necessary

# Running the agent

Before running the agent some manual steps need to be taken

1. Install the python dependencies from requirements.txt as they are not yet bundled into the debian package
2. Manually but the config files into /root/.cumulocity

Afterwards agent can be started

    sudo c8ydm.start

Note: The agent is not yet realized as a daemon. The above call will be blocking. Ensure to run as root other with the debian package management does not work.

# Bootstrapping

By default after installation the agent points to mqtt.cumulocity.com. This value can be changed in the configuration file after installation.
The agent uses bootstrap credentials and the serialNumber is printed in the log on boot.

# Extending the agent

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
