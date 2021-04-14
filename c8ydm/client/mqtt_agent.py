import logging
import time
import ssl
import _thread
import threading
import paho.mqtt.client as mqtt

import c8ydm.utils.moduleloader as moduleloader
from c8ydm.core.command import CommandHandler
from c8ydm.core.configuration import ConfigurationManager
from c8ydm.framework.smartrest import SmartRESTMessage

class Agent():
    __sensors = []
    __listeners = []
    __supportedOperations = set()
    __supportedTemplates = set()
    stopmarker = 0

    def __init__(self, serial, path, configuration, pidfile, simulated):
        self.serial = serial
        self.simulated = simulated
        self.__client = mqtt.Client(serial)
        self.configuration = configuration
        self.pidfile = pidfile
        self.path = path
        self.url = self.configuration.getValue('mqtt', 'url')
        self.port = self.configuration.getValue('mqtt', 'port')
        self.ping = self.configuration.getValue('mqtt', 'ping.interval.seconds')
        self.tls = self.configuration.getValue('mqtt','tls')
        self.cacert = self.configuration.getValue('mqtt','cacert')
        self.cert_auth = self.configuration.getValue('mqtt', 'cert_auth')
        self.client_cert = self.configuration.getValue('mqtt', 'client_cert')
        self.client_key = self.confiuration.getValue('mqtt', 'client_key')
        self.interval = int(self.configuration.getValue('agent', 'main.loop.interval.seconds'))
        self.device_name = f'{self.confiuration.getValue("agent", "name")}-{serial}'
        self.device_tyüe = self.confiuration.getValue('agent', 'type')
        self.logger = logging.getLogger(__name__)
        self.stop_event = threading.Event()
        if self.simulated:
            self.model = 'docker'
        else:
            self.model = 'raspberry'
    
    def run(self):
        try:
            self.logger.info('Starting agent')
            credentials = self.configuration.getCredentials()
            initialized = self.configuration.getValue('agent', 'initialized')
            self.__client = self.connect(credentials,self.serial, self.url, int(self.port), int(self.ping))
            self.__client.loop_start()
            while not self.stopmarker:
                self.interval = int(self.configuration.getValue('agent', 'main.loop.interval.seconds'))
                time.sleep(self.interval)
                self.logger.debug('New cycle')

        except Exception as e:
          self.logger.error('Error in C8Y Agent %s', e)
          self.disconnect(self.__client)
          self.logger.info('Will retry to connect to C8Y in 5 sec...')
          time.sleep(5)
          # Run again after 5 sec. delay.
          self.run()

    def connect(self, credentials, serial, url, port, ping):
        try:
            self.__client.on_connect = self.__on_connect
            self.__client.on_message = self.__on_message
            self.__client.on_disconnect = self.__on_disconnect
            #self.__client.on_subscribe = self.__on_subscribe
            self.__client.on_log = self.__on_log

            if self.tls:
                if self.cert_auth:
                    self.logger.debug('Using certificate authenticaiton')
                    self.__client.tls_set(self.cacert,
                                    certfile=self.client_cert,
                                    keyfile=self.client_key,
                                    tls_version=ssl.PROTOCOL_TLSv1_2,
                                    cert_reqs= ssl.CERT_NONE
                                    )                     
                else:
                    self.__client.tls_set(self.cacert) 
                    self.__client.username_pw_set(credentials[0]+'/'+ credentials[1], credentials[2])
            else:
                self.__client.username_pw_set(credentials[0]+'/'+ credentials[1], credentials[2])
            
            self.__client.connect(url, int(port), int(ping))
            self.__client.loop_start()
            return self.__client
        except Exception as e:
            self.logger.error('Error on connecting C8Y Agent %s', e)
            self.disconnect(self.__client)
            self.logger.info('Will retry to connect to C8Y in 5 sec...')
            time.sleep(5)
             # Run again after 5 sec. delay.
            return self.connect(credentials,self.serial, self.url, int(self.port), int(self.ping))

    def disconnect(self, client):
        client.loop_stop()  # stop the loop
        client.disconnect()
        if self.cert_auth:
            self.logger.info("Stopping refresh token thread")
            self.stop_event.set()
        self.logger.info("Disconnecting MQTT Client")
    
    def __on_connect(self, client, userdata, flags, rc):
        self.logger.info('Agent connected with result code: ' + str(rc))
        if rc > 0:
            self.logger.warning('Disconnecting Agent and try to re-connect manually..')
            #TODO What should be done when rc != 0? Reconnect? Abort?
            self.disconnect(self.__client)
            time.sleep(5)
            self.logger.info('Restarting Agent ..')
            self.run()
        else:
            # Load core modules
            time.sleep(5)
            commandHandler = CommandHandler(self.serial, self, self.configuration)
            configurationManager = ConfigurationManager(self.serial, self, self.configuration)

            messages = configurationManager.getMessages()
            for message in messages:
                self.logger.debug('Send topic: %s, msg: %s', message.topic, message.getMessage())
                self.__client.publish(message.topic, message.getMessage())
            self.__listeners.append(commandHandler)
            self.__listeners.append(configurationManager)
            self.__supportedOperations.update(commandHandler.getSupportedOperations())
            self.__supportedOperations.update(configurationManager.getSupportedOperations())

            # Load custom modules
            modules = moduleloader.findAgentModules()
            classCache = {}

            for sensor in modules['sensors']:
                currentSensor = sensor(self.serial)
                classCache[sensor.__name__] = currentSensor
                self.__sensors.append(currentSensor)
            for listener in modules['listeners']:
                if listener.__name__ in classCache:
                    currentListener = classCache[listener.__name__]
                else:
                    currentListener = listener(self.serial, self)
                    classCache[listener.__name__] = currentListener
                supportedOperations = currentListener.getSupportedOperations()
                supportedTemplates = currentListener.getSupportedTemplates()
                if supportedOperations is not None:
                    self.__supportedOperations.update(supportedOperations)
                if supportedTemplates is not None:
                    self.__supportedTemplates.update(supportedTemplates)
                self.__listeners.append(currentListener)
            for initializer in modules['initializers']:
                if initializer.__name__ in classCache:
                    currentInitializer = classCache[initializer.__name__]
                else:
                    currentInitializer = initializer(self.serial)
                    classCache[initializer.__name__] = currentInitializer
                messages = currentInitializer.getMessages()
                if messages is None or len(messages) == 0:
                    continue
                for message in messages:
                    self.logger.debug('Send topic: %s, msg: %s', message.topic, message.getMessage())
                    self.__client.publish(message.topic, message.getMessage())

            classCache = None

            # set Device Name
            self.__client.publish("s/us", "100,"+self.deviceName+","+self.deviceType,2).wait_for_publish()

            # set supported operations
            self.logger.info('Supported operations:')
            self.logger.info(self.__supportedOperations)
            supportedOperationsMsg = SmartRESTMessage('s/us', 114, self.__supportedOperations)
            self.publishMessage(supportedOperationsMsg)

            # set required interval
            required_interval = self.configuration.getValue('agent', 'requiredinterval')
            self.logger.info(f'Required interval: {required_interval}')
            requiredIntervalMsg = SmartRESTMessage('s/us', 117, [f'{required_interval}'])
            self.publishMessage(requiredIntervalMsg)

            # set device model
            self.logger.info('Model:')
            self.logger.info([self.serial, self.model, '1.0'])
            modelMsg = SmartRESTMessage('s/us', 110, [self.serial, self.model, '1.0'])
            self.publishMessage(modelMsg)

            self.__client.subscribe('s/e')
            self.__client.subscribe('s/ds')

            # subscribe additional topics
            for xid in self.__supportedTemplates:
                self.logger.info('Subscribing to XID: %s', xid)
                self.__client.subscribe('s/dc/' + xid)

    def __on_message(self, client, userdata, msg):
        try:
            decoded = msg.payload.decode('utf-8')
            messageParts = decoded.split(',')
            message = SmartRESTMessage(msg.topic, messageParts[0], messageParts[1:])
            logging.debug('Received: topic=%s msg=%s', message.topic, message.getMessage())
            for listener in self.__listeners:
                logging.debug('Trigger listener ' + listener.__class__.__name__)
                _thread.start_new_thread(listener.handleOperation, (message,))
        except Exception as e:
            logging.error('Error on handling MQTT Message:' + str(e))

    def __on_disconnect(self,client, userdata, rc):
        self.logger.debug("on_disconnect rc: " +str(rc))
        # if rc==5:
        #     self.reset()
        #     return
        if rc!=0:
            self.logger.error("Disconnected! Try to reconnect: " +str(rc))
            self.__client.reconnect()

    def __on_log(self, client, userdata, level, buf):
        self.logger.log(level, buf)

    def publishMessage(self, message):
        self.logger.debug('Send: topic=%s msg=%s', message.topic, message.getMessage())
        self.__client.publish(message.topic, message.getMessage())