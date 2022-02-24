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
import logging, io, re
from datetime import datetime
from c8ydm.framework.modulebase import Initializer, Listener
from c8ydm.framework.smartrest import SmartRESTMessage
from c8ydm.core.device_stats import DeviceStats


class MeasurementRequestHandler(Initializer, Listener):
    logger = logging.getLogger(__name__)
    fragment = 'c8y_MeasurementRequestOperation'
    DeviceStats = DeviceStats()
    

    def getMessages(self):
        return []

    def getSupportedOperations(self):
        return ['c8y_MeasurementRequestOperation']
    
    def getSupportedTemplates(self):
        return []

    def _set_executing(self):
        executing = SmartRESTMessage('s/us', '501', [self.fragment])
        print("Executing MSG send")
        self.agent.publishMessage(executing)

    #datei anhängen
    def _set_success(self):
        success = SmartRESTMessage('s/us', '503', [self.fragment,'CPU:RAM:DISK'])
        print("Success MSG send")
        self.agent.publishMessage(success)

    def _set_failed(self, reason):
        failed = SmartRESTMessage('s/us', '502', [self.fragment,reason])
        self.logger.error(f'Operation failed, reason: {reason}')
        self.agent.publishMessage(failed)
    
    def _getCPU(self):
        return self.DeviceStats.getCPUStats() 

    def _getDisk(self):
        return self.DeviceStats.getDiskStats() 
    
    def _getMemory(self):
        return self.DeviceStats.getMemoryStats()
    
    def handleOperation(self, message):
        mo_id = self.agent.rest_client.get_internal_id(self.agent.serial)
        try:
            if 's/ds' in message.topic and message.messageId == '517':
                self._set_executing()
                self.logger.info("Sending device stats due to measurement request")
                self.stats = []
                for key,value in self._getCPU().items():
                    self.stats.append(SmartRESTMessage('s/us', '200', ['cpu', key, value]))
                for key,value in self._getDisk().items():
                    self.stats.append(SmartRESTMessage('s/us', '200', ['disk', key, value]))
                for key,value in self._getMemory().items():
                    self.stats.append(SmartRESTMessage('s/us', '200', ['memory', key, value]))
                for i in self.stats:
                    self.agent.publishMessage(i)
                self.logger.debug("Sended device stats due to measurment request")
                self._set_success()
            self.logger.debug("Measurement request handled")
        except Exception as e:
            self._set_failed(e)

