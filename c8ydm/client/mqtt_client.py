#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import time

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
        self.interval = int(self.configuration.getValue('agent', 'main.loop.interval.seconds'))
        #self.runningInDocker = os.environ.get('container', False)
        if self.simulated:
            self.model = 'docker'
        else:
            self.model = 'raspberry'

    def __on_connect(self, client, userdata, flags, rc):
        logging.info('Agent connected with result code: ' + str(rc))
        if rc > 0:
            logging.warning('Disconnecting Agent and try to re-connect manually..')
            self.disconnect(self.__client)
            time.sleep(5)
            #credentials = self.configuration.getCredentials()
            #self.__client = self.connect(credentials,self.serial, self.url, int(self.port), int(self.ping))
            logging.info('Restarting Agent ..')
            self.run()
        else:
            # Load core modules
            time.sleep(5)
            commandHandler = CommandHandler(self.serial, self, self.configuration)
            configurationManager = ConfigurationManager(self.serial, self, self.configuration)
            firmwareManagement = FirmwareManagement(self, self.path, self.configuration)

            messages = configurationManager.getMessages()
            for message in messages:
                logging.debug('Send topic: %s, msg: %s', message.topic, message.getMessage())
                self.__client.publish(message.topic, message.getMessage())
            self.__listeners.append(commandHandler)
            self.__listeners.append(configurationManager)
            self.__listeners.append(firmwareManagement)
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
                    logging.debug('Send topic: %s, msg: %s', message.topic, message.getMessage())
                    self.__client.publish(message.topic, message.getMessage())

            classCache = None

            # set supported operations
            logging.info('Supported operations:')
            logging.info(self.__supportedOperations)
            supportedOperationsMsg = SmartRESTMessage('s/us', 114, self.__supportedOperations)
            self.publishMessage(supportedOperationsMsg)

            # set required interval
            logging.info('Required interval:')
            logging.info(['1'])
            requiredIntervalMsg = SmartRESTMessage('s/us', 117, ['1'])
            self.publishMessage(requiredIntervalMsg)

            # set device model
            logging.info('Model:')
            logging.info([self.serial, self.model, '1.0'])
            modelMsg = SmartRESTMessage('s/us', 110, [self.serial, self.model, '1.0'])
            self.publishMessage(modelMsg)

            self.__client.subscribe('s/e')
            self.__client.subscribe('s/ds')

            # subscribe additional topics
            for xid in self.__supportedTemplates:
                logging.info('Subscribing to XID: %s', xid)
                self.__client.subscribe('s/dc/' + xid)

    def __on_disconnect(self, client, userdata, rc):
        logging.info('Agent is disconnected with result code: ' +str(rc))

    def __on_message(self, client, userdata, msg):
        try:
            decoded = msg.payload.decode('utf-8')
            messageParts = decoded.split(',')
            message = SmartRESTMessage(msg.topic, messageParts[0], messageParts[1:])
            logging.debug('Received: topic=%s msg=%s', message.topic, message.getMessage())
            for listener in self.__listeners:
                logging.debug('Trigger listener ' + listener.__class__.__name__)
                thread.start_new_thread(listener.handleOperation, (message,))
        except Exception as e:
            logging.error('Error on handling MQTT Message:' + str(e))

    def __on_log(self, client, userdata, level, buf):
        logging.log(level, buf)

    def __on_subscribe(self, client, userdata, mid, granted_qos):
        logging.info('')

    def publishMessage(self, message):
        logging.debug('Send: topic=%s msg=%s', message.topic, message.getMessage())
        self.__client.publish(message.topic, message.getMessage())

    def stop(self):
        self.disconnect(self.__client)
        stopmarker = 1

    def pollPendingOperations(self):
        while not self.stopmarker:
            try:
                time.sleep(15)
                logging.debug('Polling for pending Operations')
                pending = SmartRESTMessage('s/us', '500', [])
                self.publishMessage(pending)
            except Exception as e:
                logging.error('Error on polling for Pending Operations: '+ str(e))

    def disconnect(self, client):
      client.loop_stop()  # stop the loop
      client.disconnect()
      logging.info("Disconnecting MQTT Client")

    def connect(self, credentials, serial, url, port, ping):
        try:
            self.__client.on_connect = self.__on_connect
            self.__client.on_message = self.__on_message
            self.__client.on_log = self.__on_log
            self.__client.username_pw_set(credentials[0] + '/' + credentials[1], credentials[2])
            self.__client.connect(url, int(port), int(ping))
            self.__client.loop_start()
            return self.__client
        except Exception as e:
            logging.error('Error on connecting C8Y Agent %s', e)
            self.disconnect(self.__client)
            logging.info('Will retry to connect to C8Y in 5 sec...')
            time.sleep(5)
             # Run again after 5 sec. delay.
            return self.connect(credentials,self.serial, self.url, int(self.port), int(self.ping))

    def run(self):
        try:
          logging.info('Starting agent')
          credentials = self.configuration.getCredentials()
          initialized = self.configuration.getValue('agent', 'initialized')

          self.__client = self.connect(credentials,self.serial, self.url, int(self.port), int(self.ping))

          #if not initialized:
          #  time.sleep(10)
          #  self.configuration.setValue('agent', 'initialized', "1")
          #  self.snapdClient.restartSnap('c8ycc')
          self.__client.loop_start()
          while not self.stopmarker:
            self.interval = int(self.configuration.getValue('agent', 'main.loop.interval.seconds'))
            time.sleep(self.interval)
            logging.debug('New cycle')

        except Exception as e:
          logging.error('Error in C8Y Agent %s', e)
          self.disconnect(self.__client)
          logging.info('Will retry to connect to C8Y in 5 sec...')
          time.sleep(5)
          # Run again after 5 sec. delay.
          self.run()