#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
import signal
import subprocess
import sys
import time
import pathlib
from os.path import expanduser

import c8ydm.utils.systemutils as systemutils
from c8ydm.client import Agent
from c8ydm.client import Bootstrap
from c8ydm.utils import Configuration


def start():
    home = expanduser('~')
    path = pathlib.Path(home + '/.cumulocity')
    path.mkdir(parents=True, exist_ok=True)
    config = Configuration(str(path))
    simulated = False
    logging.basicConfig(filename=path/'agent.log', level=logging.DEBUG,
                        format='%(asctime)s %(threadName)s %(levelname)s %(message)s')
    containerId = None
    serial = None
    try:
        if os.getenv('docker') == 'container':
            containerId = subprocess.check_output(['bash', '-c', 'hostname'], universal_newlines=True)
            containerId = containerId.strip('\n')
            containerId = containerId.strip()
            logging.info('Container Id: %s', str(containerId))
    except Exception as e:
        logging.error('Could not retrieve container Id: ' + str(e))
        output = None

    if containerId is None:
        serial = systemutils.getSerial()
        logging.info('Output of SystemUtils Serial: %s', serial)
        simulated = False
    else:
        serial = containerId.strip()
        simulated = True

    startDaemon(str(path) + '/agent.pid')
    logging.info('Serial %s', serial)

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


def stop():
    path = expanduser('~') + '/.cumulocity'
    stopDaemon(path + '/agent.pid')


def stopDaemon(pidfile):
    """Stop the daemon."""
    print("Stopping...")
    # Get the pid from the pidfile
    try:
        with open(pidfile, 'r') as pf:
            pid = int(pf.read().strip())
    except IOError:
        pid = None

    if not pid:
        message = "pidfile {0} does not exist. " + \
                  "Daemon not running?\n"
        sys.stderr.write(message.format(pidfile))
        return  # not an error in a restart

    # Try killing the daemon process
    try:
        while 1:
            os.kill(pid, signal.SIGTERM)
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
    os.remove(pidfile)


def startDaemon(pidfile):
    """Start the daemon."""
    print("Starting...")
    # Check for a pidfile to see if the daemon already runs
    pid = None
    try:
        with open(pidfile, 'r') as pf:
            pid = int(pf.read().strip())
            logging.info('Found pid file with pid ' + str(pid))
    except IOError:
        pid = None

    if pid:
        if not isPidRunning(pid):
            delpid(pidfile)
            pid = str(os.getpid())
            with open(pidfile, 'w+') as f:
                f.write(pid + '\n')
        else:
            message = "pidfile {0} already exist. " + \
                      "Daemon already running? Stop it with sudo snap stop c8ycc first.\n"
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
