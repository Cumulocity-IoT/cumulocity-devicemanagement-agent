"""  
Copyright (c) 2021 Software AG, Darmstadt, Germany and/or its licensors

SPDX-License-Identifier: Apache-2.0

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import logging
import time
import ssl
import _thread
import threading
import certifi
import paho.mqtt.client as mqtt


import c8ydm.utils.moduleloader as moduleloader
from c8ydm.client.rest_client import RestClient
from c8ydm.core.configuration import ConfigurationManager
from c8ydm.framework.smartrest import SmartRESTMessage


class Agent():
    __sensors = []
    __listeners = []
    __supportedOperations = set()
    __supportedTemplates = set()
    stopmarker = 0

    def __init__(self, serial, path, configuration, pidfile, simulated):
        self.logger = logging.getLogger(__name__)
        self.serial = serial
        self.simulated = simulated
        self.__client = mqtt.Client(serial)
        self.configuration = configuration
        self.pidfile = pidfile
        self.path = path
        self.url = self.configuration.getValue('mqtt', 'url')
        self.port = self.configuration.getValue('mqtt', 'port')
        self.ping = self.configuration.getValue(
            'mqtt', 'ping.interval.seconds')
        self.tls = self.configuration.getBooleanValue('mqtt', 'tls')
        #self.cacert = self.configuration.getValue('mqtt', 'cacert')
        self.cert_auth = self.configuration.getBooleanValue(
            'mqtt', 'cert_auth')
        self.client_cert = self.configuration.getValue('mqtt', 'client_cert')
        self.client_key = self.configuration.getValue('mqtt', 'client_key')
        self.interval = int(self.configuration.getValue(
            'agent', 'main.loop.interval.seconds'))
        self.device_name = f'{self.configuration.getValue("agent", "name")}-{serial}'
        self.device_type = self.configuration.getValue('agent', 'type')

        self.stop_event = threading.Event()
        self.refresh_token_interval = 60
        self.token = None
        self.is_connected = False
        self.rest_client = RestClient(self)

        if self.simulated:
            self.model = 'docker'
        else:
            self.model = 'raspberry'

    def handle_sensor_message(self, sensor):
        messages = sensor.getSensorMessages()
        if messages is not None and len(messages) > 0:
            for message in messages:
                self.publishMessage(message)

    def handle_initializer_message(self, initializer):
        messages = initializer.getMessages()
        if messages is not None and len(messages) > 0:
            for message in messages:
                if message:
                    self.logger.debug('Send topic: %s, msg: %s',
                                    message.topic, message.getMessage())
                    self.publishMessage(message)

    def run(self):
        try:
            self.logger.info('Starting agent')
            self.__client = mqtt.Client(self.serial)
            credentials = self.configuration.getCredentials()
            self.__client = self.connect(
                credentials, self.serial, self.url, int(self.port), int(self.ping))
            self.__client.loop_start()
            while not self.is_connected:
                time.sleep(1)
                self.logger.debug('Waiting for MQTT Client to be connected')
            self.__init_agent()
            while not self.stopmarker:
                self.logger.debug('New cycle')
                self.interval = int(self.configuration.getValue(
                    'agent', 'main.loop.interval.seconds'))
                for sensor in self.__sensors:
                    sensor_thread = threading.Thread(target=self.handle_sensor_message, args=(sensor,))
                    sensor_thread.daemon = True
                    sensor_thread.name = f'SensorThread-{sensor.__class__.__name__}'
                    sensor_thread.start()
                    #_thread.start_new_thread(self.handle_sensor_message, (sensor,))
                time.sleep(self.interval)
        except Exception as e:
            self.logger.exception(f'Error in C8Y Agent: {e}', e)
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
                    self.__client.tls_set(certifi.where(),
                                          certfile=self.client_cert,
                                          keyfile=self.client_key,
                                          tls_version=ssl.PROTOCOL_TLSv1_2,
                                          cert_reqs=ssl.CERT_NONE
                                          )
                else:
                    self.__client.tls_set(certifi.where())
                    self.__client.username_pw_set(
                        credentials[0]+'/' + credentials[1], credentials[2])
            else:
                self.__client.username_pw_set(
                    credentials[0]+'/' + credentials[1], credentials[2])

            self.__client.connect(url, int(port), int(ping))
            self.__client.loop_start()
            return self.__client
        except Exception as e:
            self.logger.exception(f'Error on connecting C8Y Agent: {e}', e)
            self.disconnect(self.__client)
            self.logger.info('Will retry to connect to C8Y in 5 sec...')
            time.sleep(5)
            # Run again after 5 sec. delay.
            return self.run()

    def disconnect(self, client):
        self.logger.info("Disconnecting MQTT Client")
        self.__client = None
        if client == None:
            return
        client.loop_stop()  # stop the loop
        client.disconnect()
        if self.cert_auth:
            self.logger.info("Stopping refresh token thread")
            self.stop_event.set()
        

    def stop(self):
        msg = SmartRESTMessage('s/us', '400', ['c8y_AgentStopEvent', 'C8Y DM Agent stopped'])
        self.publishMessage(msg, qos=0, wait_for_publish=True)
        self.disconnect(self.__client)
        self.stopmarker = 1

    def pollPendingOperations(self):
        while not self.stopmarker:
            try:
                time.sleep(15)
                self.logger.debug('Polling for pending Operations')
                pending = SmartRESTMessage('s/us', '500', [])
                self.publishMessage(pending)
            except Exception as e:
                self.logger.error(
                    'Error on polling for Pending Operations: ' + str(e))

    def __init_agent(self):
        self.__listeners = []
        self.__sensors = []

        # Refresh Token for REST Requests
        if self.cert_auth:
            self.logger.info("Starting refresh token thread ")
            token_thread = threading.Thread(target=self.refresh_token)
            token_thread.daemon = True
            token_thread.name = f'TokenThread-1'
            token_thread.start()
               
        # set Device Name
        msg = SmartRESTMessage('s/us', '100', [self.device_name, self.device_type])
        self.publishMessage(msg, 2, wait_for_publish=True)

        #self.logger.info(f'Device published!')
        configurationManager = ConfigurationManager(
            self.serial, self, self.configuration)

        messages = configurationManager.getMessages()
        for message in messages:
            self.logger.debug('Send topic: %s, msg: %s',
                              message.topic, message.getMessage())
            self.__client.publish(message.topic, message.getMessage())
        self.__listeners.append(configurationManager)
        self.__supportedOperations.update(
            configurationManager.getSupportedOperations())

        # Load custom modules
        modules = moduleloader.findAgentModules()
        classCache = {}

        for sensor in modules['sensors']:
            currentSensor = sensor(self.serial, self)
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
                currentInitializer = initializer(self.serial, self)
                classCache[initializer.__name__] = currentInitializer
            init_thread = threading.Thread(target=self.handle_initializer_message, args=(currentInitializer,))
            init_thread.daemon = True
            init_thread.name = f'InitializerThread-{currentInitializer.__class__.__name__}'
            init_thread.start()
            #_thread.start_new_thread(self.handle_initializer_message, (currentInitializer,))

        classCache = None

        # set supported operations
        self.logger.info('Supported operations:')
        self.logger.info(self.__supportedOperations)
        supportedOperationsMsg = SmartRESTMessage(
            's/us', 114, self.__supportedOperations)
        self.publishMessage(supportedOperationsMsg)

        # set required interval
        required_interval = self.configuration.getValue(
            'agent', 'requiredinterval')
        self.logger.info(f'Required interval: {required_interval}')
        requiredIntervalMsg = SmartRESTMessage(
            's/us', 117, [f'{required_interval}'])
        self.publishMessage(requiredIntervalMsg)

        # set device model
        self.logger.info('Model:')
        self.logger.info([self.serial, self.model, '1.0'])
        modelMsg = SmartRESTMessage(
            's/us', 110, [self.serial, self.model, '1.0'])
        self.publishMessage(modelMsg)

        self.__client.subscribe('s/e')
        self.__client.subscribe('s/ds')
        self.__client.subscribe('s/dat')

        # subscribe additional topics
        for xid in self.__supportedTemplates:
            self.logger.info('Subscribing to XID: %s', xid)
            self.__client.subscribe('s/dc/' + xid)

        # Set all dangling Operations to failed on Agent start
        internald_id = self.rest_client.get_internal_id(self.serial)
        ops = self.rest_client.get_all_dangling_operations(internald_id)
        self.rest_client.set_operations_to_failed(ops)


    def __on_connect(self, client, userdata, flags, rc):
        try:
            self.logger.info('Agent connected with result code: ' + str(rc))
            if rc > 0:
                self.logger.warning(
                    'Disconnecting Agent and try to re-connect manually..')
                # TODO What should be done when rc != 0? Reconnect? Abort?
                self.disconnect(self.__client)
                time.sleep(5)
                self.logger.info('Restarting Agent ..')
                self.run()
            else:
                self.is_connected = True
        except Exception as ex:
            self.logger.error(ex)

    def __on_message(self, client, userdata, msg):
        try:
            decoded = msg.payload.decode('utf-8')
            messageParts = decoded.split(',')
            message = SmartRESTMessage(
                msg.topic, messageParts[0], messageParts[1:])
            self.logger.debug('Received: topic=%s msg=%s',
                          message.topic, message.getMessage())
            if message.messageId == '71':
                self.token = message.values[0]
                self.logger.info('New JWT Token received')
                self.rest_client.update_token(self.token)
            for listener in self.__listeners:
                self.logger.debug('Trigger listener ' +
                              listener.__class__.__name__)
                listener_thread = threading.Thread(target=listener.handleOperation, args=(message,))
                listener_thread.daemon = True
                listener_thread.name = f'ListenerThread-{listener.__class__.__name__}'
                listener_thread.start()
                #_thread.start_new_thread(listener.handleOperation, (message,))
        except Exception as e:
            self.logger.error(f'Error on handling MQTT Message.', e)

    def __on_disconnect(self, client, userdata, rc):
        self.logger.debug("on_disconnect rc: " + str(rc))
        # if rc==5:
        #     self.reset()
        #     return
        if rc != 0:
            self.logger.error(f'Disconnected with result code {rc}! Trying to reconnect...')
            #self.__client.reconnect()
            time.sleep(5)
            # Run again after 5 sec. delay.
            return self.run()

    def __on_log(self, client, userdata, level, buf):
        self.logger.log(level, buf)

    def publishMessage(self, message, qos=0, wait_for_publish=False):
        self.logger.debug(f'Send: topic={message.topic} msg={message.getMessage()}')
        if self.__client is not None and self.__client.is_connected:
            if wait_for_publish:
                self.__client.publish(message.topic, message.getMessage(), qos).wait_for_publish()
            else:
                self.__client.publish(message.topic, message.getMessage(), qos)


    def refresh_token(self):
        self.stop_event.clear()
        while True:
            self.logger.info("Refreshing Token")
            self.__client.publish('s/uat','',2)
            if self.stop_event.wait(timeout=self.refresh_token_interval):
                self.logger.info("Exit Refreshing Token Thread")
                break
