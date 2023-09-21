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
    logger = logging.getLogger(__name__)
    DeviceStats = DeviceStats()

    def getSensorMessages(self):
        try:
            return self.sendStats()
        except Exception as e:
            self.logger.exception(f'Error in DeviceSensor getSensorMessages: {e}', e)

    def getMessages(self):
        try:
            return self.sendStats()
        except Exception as e:
            self.logger.exception(f'Error in DeviceSensor getMessages: {e}', e)
    
    def sendStats(self):
        stats = ['c8y_deviceStats','']
        #201,KamstrupA220Reading,2022-03-19T12:03:27.845Z,c8y_SinglePhaseEnergyMeasurement,A+:1,1234,kWh,c8y_SinglePhaseEnergyMeasurement,A-:1,2345,kWh,c8y_ThreePhaseEnergyMeasurement,A+:1,123,kWh,c8y_ThreePhaseEnergyMeasurement,A+:2,234,kWh,c8y_ThreePhaseEnergyMeasurement,A+:3,345,kWh
        for key,value in self._getCPU().items():
            stats.extend(['cpu', key, value, '' ])
        for key,value in self._getDisk().items():
            stats.extend(['disk', key, value, '' ])
        for key,value in self._getMemory().items():
            stats.extend(['memory', key, value, '' ])
        return [SmartRESTMessage('s/us', '201', stats)]
    
    def _getCPU(self):
        return self.DeviceStats.getCPUStats() 

    def _getDisk(self):
        return self.DeviceStats.getDiskStats() 
    
    def _getMemory(self):
        return self.DeviceStats.getMemoryStats()
