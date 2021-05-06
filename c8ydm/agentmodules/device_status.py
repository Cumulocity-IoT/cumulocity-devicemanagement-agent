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
from c8ydm.framework.modulebase import Sensor, Initializer
from c8ydm.framework.smartrest import SmartRESTMessage
from c8ydm.core.device_stats import DeviceStats

class DeviceSensor(Sensor, Initializer):
    xid = 'c8y-dm-agent-v1.0'
    logger = logging.getLogger(__name__)

    def __init__(self):
        self.DeviceStats = DeviceStats()

    def getSensorMessages(self):
        print(self.sendStats())
        return []

    def getMessages(self):
        print(self.sendStats())
        return []
    
    def sendStats(self):
        self.stats = []
        for key,value in self._getCPU():
            self.stats.append(SmartRESTMessage('s/us', '200', ['CPU', key, value]))
        for key,value in self._getDisk():
            self.stats.append(SmartRESTMessage('s/us', '200', ['Disk', key, value]))
        for key,value in self._getMemory():
            self.stats.append(SmartRESTMessage('s/us', '200', ['Memory', key, value]))
        return self.stats
    
    def _getCPU(self):
        return self.DeviceStats.getCPUStats() 

    def _getDisk(self):
        return self.DeviceStats.getDiskStats() 
    
    def _getMemory(self):
        return self.DeviceStats.getDiskStats()
    