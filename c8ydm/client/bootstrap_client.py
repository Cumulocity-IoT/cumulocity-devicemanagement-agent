#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import time

import paho.mqtt.client as mqtt


class Bootstrap():
    bootstrapped = False

    def __init__(self, serial, path, configuration):
        self.serial = serial
        self.configuration = configuration
        self.url = self.configuration.getValue('mqtt', 'url')
        self.port = self.configuration.getValue('mqtt', 'port')
        self.ping = self.configuration.getValue('mqtt', 'ping.interval.seconds')

    def on_connect(self, client, userdata, flags, rc):
        logging.debug('Bootstrap connected with result code: ' + str(rc))
        client.subscribe('s/dcr')

    def on_disconnect(self, client, userdata, rc):
        logging.debug('Bootstrap disconnected with result code: ' + str(rc))

    def on_messageRegistration(self, client, userdata, msg):
        message = msg.payload.decode('utf-8')
        messageParts = message.split(',')
        logging.debug(messageParts)
        if messageParts[0] == '70':

            while not self.bootstrapped:
                try:
                    logging.debug('Storing credentials...')
                    self.configuration.writeCredentials(messageParts[1], messageParts[2], messageParts[3])
                    logging.debug('Storing credentials successful')
                    client.unsubscribe('s/dcr')
                    self.bootstrapped = True
                except Exception as e:
                    logging.debug('Storing credentials failed. Waiting 5 Sec. to retry..')
                    logging.exception(e)
                    time.sleep(5)

    def bootstrap(self):
        logging.info('Start bootstrap client')

        client = mqtt.Client(client_id=self.serial)
        client.on_message = self.on_messageRegistration
        client.on_connect = self.on_connect
        client.on_disconnect = self.on_disconnect

        credentials = self.configuration.getBootstrapCredentials()

        client.username_pw_set(credentials[0] + '/' + credentials[1], credentials[2])
        client.connect(self.url, int(self.port), int(self.ping))

        client.loop_start()
        client.publish('s/ucr')

        while not self.bootstrapped:
            time.sleep(5)
            logging.debug('poll credentials')
            client.publish('s/ucr')

        client.on_message = None
        client.on_connect = None
        client.disconnect()
        client.loop_stop()
        client = None
        time.sleep(10)
        logging.info('Stop bootstrap client')
