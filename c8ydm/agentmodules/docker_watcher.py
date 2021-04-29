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
from c8ydm.framework.modulebase import Sensor, Initializer
from c8ydm.framework.smartrest import SmartRESTMessage
from c8ydm.core.docker_watcher import DockerWatcher

class DockerSensor(Sensor, Initializer):
    logger = logging.getLogger(__name__)
    docker_watcher = DockerWatcher()

    def getSensorMessages(self):
        self.logger.info(f'Docker Update Loop called...')
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