#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
import os
import signal
import subprocess
import sys
import time
import pathlib
from os.path import expanduser
from logging.handlers import RotatingFileHandler
import signal

from paho.mqtt.client import LOGGING_LEVEL
import c8ydm.utils.systemutils as systemutils
from c8ydm.client import Agent
from c8ydm.client import Bootstrap
from c8ydm.utils import Configuration

agent = None
bootstrap_agent = None
terminated = False
simulated = False

def handle_sigterm(*args):
    global terminated
    if not terminated:
        raise KeyboardInterrupt

def keyboard_interupt_hook(exctype, value, traceback):
    try:
        global terminated
        if exctype == KeyboardInterrupt:
            if not terminated:
                logging.info(f'KeyboardInterrupt called!')
                terminated = True
                global agent
                if agent:
                    agent.stop()
                global bootstrap_agent
                if bootstrap_agent:
                    bootstrap_agent.stop()
                stop()
                sys.exit(0)
        #else:
        #    sys.__excepthook__(exctype, value, traceback)
    except Exception as ex:
        logging.error(ex)


def start():
    try:
        sys.excepthook = keyboard_interupt_hook
        global agent
        global simulated
        agent = None
        signal.signal(signal.SIGTERM, handle_sigterm)
        home = expanduser('~')
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        path = pathlib.Path(home + '/.cumulocity')
        path.mkdir(parents=True, exist_ok=True)
        config_path = pathlib.Path(path / 'agent.ini')
        if not config_path.is_file():
            sys.exit(f'No agent.ini found in "{path}". Create it to properly configure the agent.')
        config = Configuration(str(path))
        loglevel = config.getValue('agent', 'loglevel')
        logger.setLevel(loglevel)
        log_file_formatter = logging.Formatter(
            '%(asctime)s %(threadName)s %(levelname)s %(name)s %(message)s')
        log_console_formatter = logging.Formatter('%(asctime)s %(threadName)s %(levelname)s %(name)s %(message)s')
        # Set default log format
        if len(logger.handlers) == 0:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(log_console_formatter)
            console_handler.setLevel(loglevel)
            logger.addHandler(console_handler)
        else:
            handler = logger.handlers[0]
            handler.setFormatter(log_console_formatter)

        # Max 5 log files each 10 MB.
        rotate_handler = RotatingFileHandler(filename=path / 'agent.log', maxBytes=10000000,
                                            backupCount=5)
        rotate_handler.setFormatter(log_file_formatter)
        rotate_handler.setLevel(loglevel)
        # Log to Rotating File
        logger.addHandler(rotate_handler)

        containerId = None
        serial = None

        if serial == None:
            logging.debug(f'Serial not proviced. Fetching from system...')
            try:
                if os.getenv('CONTAINER') == 'docker':
                    containerId = subprocess.check_output(['bash', '-c', 'hostname'], universal_newlines=True)
                    containerId = containerId.strip('\n')
                    containerId = containerId.strip()
                    logging.info('Container Id: %s', str(containerId))
                    simulated = True
            except Exception as e:
                logging.error('Could not retrieve container Id: ' + str(e))

            if containerId is None:
                serial = systemutils.getSerial()
                logging.info('Output of SystemUtils Serial: %s', serial)
                simulated = False
            else:
                serial = containerId.strip()
                simulated = True
        if config.getValue('agent','device.id'):
            serial = config.getValue('agent','device.id')
        #if not simulated:
        startDaemon(str(path) + '/agent.pid')
        logging.info(f'Serial: {serial}')

        credentials = config.getCredentials()
        logging.debug('Credentials:')
        logging.debug(credentials)
        agent = Agent(serial, path, config, str(path) + '/agent.pid', simulated)
        cert_auth = config.getBooleanValue('mqtt','cert_auth')
        logging.debug(f'cert_auth: {cert_auth}')
        if not cert_auth and credentials is None:
            logging.info('No credentials found. Starting bootstrap mode.')
            bootstrapCredentials = config.getBootstrapCredentials()
            if bootstrapCredentials is None:
                logging.error('No bootstrap credentials found. Stopping agent.')
                return
            bootstrapAgent = Bootstrap(serial, str(path), config)
            bootstrapAgent.bootstrap()
            credentials = config.getCredentials()
            if credentials is None:
                logging.error('No credentials found after bootstrapping. Stopping agent.')
                return        
        agent.run()
    except Exception as ex:
        logger.exception(f'Error on main start {ex}', ex)
        


def stop():
    path = expanduser('~') + '/.cumulocity'
    stopDaemon(path + '/agent.pid')

def stopDaemon(pidfile):
    """Stop the daemon."""
    logging.info(f'Stopping...')
    global terminated
    # Get the pid from the pidfile
    try:
        with open(pidfile, 'r') as pf:
            pid = int(pf.read().strip())
    except IOError:
        pid = None

    if not pid:
        return
    else:
        delpid(pidfile)
    # Try killing the daemon process
    try:
        while 1:
            #if not terminated:
            logging.debug(f'Try killing pid {pid}')
            os.kill(pid, signal.SIGKILL)
            time.sleep(0.1)
                
    except OSError as err:
        e = str(err.args)
        if e.find("No such process") > 0:
            if os.path.exists(pidfile):
                os.remove(pidfile)
        else:
            print(str(err.args))
            sys.exit(1)
    


def delpid(pidfile):
    if pathlib.Path(pidfile).is_file():
        logging.info(f'Removing PID File {pidfile}')
        os.remove(pidfile)


def startDaemon(pidfile):
    """Start the daemon."""
    print("Starting...")
    # Check for a pidfile to see if the daemon already runs
    pid = None
    global simulated
    try:
        with open(pidfile, 'r') as pf:
            pid = int(pf.read().strip())
            logging.info(f'Found pid file with pid {str(pid)}')
    except IOError:
        pid = None

    if pid:
        if simulated or not isPidRunning(pid):
            delpid(pidfile)
            pid = str(os.getpid())
            with open(pidfile, 'w+') as f:
                f.write(pid + '\n')
        else:
            message = "pidfile {0} already exist. " + \
                      "Daemon already running? Stop it with sudo c8ydm.stop first.\n"
            sys.stderr.write(message.format(pidfile))
            sys.exit(1)
    else:
        pid = str(os.getpid())
        with open(pidfile, 'w+') as f:
            f.write(pid + '\n')


def isPidRunning(pid):
    """ Check For the existence of a unix pid. """
    try:
        logging.info('Checking if pid ' + str(pid) + ' is existing...')
        os.kill(pid, 0)
        logging.info('Pid ' + str(pid) + ' exists')
    except OSError:
        logging.info('Pid ' + str(pid) + ' does not exist')
        return False
    else:
        return True

if __name__ == '__main__':
    start()
