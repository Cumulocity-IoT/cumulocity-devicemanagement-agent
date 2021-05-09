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
import logging, time
import subprocess
from c8ydm.framework.modulebase import Sensor, Initializer, Listener
from c8ydm.framework.smartrest import SmartRESTMessage
from c8ydm.core.docker_watcher import DockerWatcher

class DockerSensor(Sensor, Initializer, Listener):
    xid = 'c8y-dm-agent-v1.0'
    logger = logging.getLogger(__name__)
    docker_watcher = DockerWatcher()
    fragment = 'c8y_Docker'

    def getSensorMessages(self):
        #self.logger.info(f'Docker Update Loop called...')
        payload = self.docker_watcher.get_stats()
        internal_id = self.agent.rest_client.get_internal_id(self.agent.serial)
        self.agent.rest_client.update_managed_object(internal_id, payload)
        return []

    def getMessages(self):
        self.logger.info(f'Docker Initializer called...')
        payload = self.docker_watcher.get_stats()
        internal_id = self.agent.rest_client.get_internal_id(self.agent.serial)
        self.agent.rest_client.update_managed_object(internal_id, payload)
        return []
    
    def _set_executing(self):
        executing = SmartRESTMessage('s/us', '501', [self.fragment])
        self.agent.publishMessage(executing)

    def _set_success(self):
        success = SmartRESTMessage('s/us', '503', [self.fragment])
        self.agent.publishMessage(success)

    def _set_failed(self, reason):
        failed = SmartRESTMessage('s/us', '502', [self.fragment, reason])
        self.agent.publishMessage(failed)
    
    def handleOperation(self, message):
        if message.messageId == 'dm501':
            self.logger.info('Found a c8y_Docker operation')
            try:
                self._set_executing()
                command = message.values[1]
                create_name = message.values[2]
                image = message.values[3]
                ports = message.values[4]
                container_id = message.values[5]
                update_name = message.values[6]
                if command == 'create':
                    process = subprocess.Popen(["docker","run","-d","--name",create_name,"-p",ports,image],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                elif command == 'delete':
                    process = subprocess.Popen(["docker","rm",update_name],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                elif command == 'restart':
                    process = subprocess.Popen(["docker","restart",update_name],stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                elif command == 'stop':
                    process = subprocess.Popen(["docker","stop",update_name],stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                elif command == 'start':
                    process = subprocess.Popen(["docker","start",update_name],stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                process.wait()
                if process.returncode == 0:
                    self._set_success()
                    payload = self.docker_watcher.get_stats()
                    internal_id = self.agent.rest_client.get_internal_id(self.agent.serial)
                    self.agent.rest_client.update_managed_object(internal_id, payload)
                else:
                    stderr = str(process.stderr.read().decode('utf-8'))
                    self.logger.error(f'Following error raised for docker: {stderr}')
                    self._set_failed(stderr)
            except Exception as e:
                self.logger.error(f'The following error occured:{e}')
                self._set_failed(stderr)
    
    def getSupportedOperations(self):
        return [self.fragment]

    def getSupportedTemplates(self):
        return [self.xid]