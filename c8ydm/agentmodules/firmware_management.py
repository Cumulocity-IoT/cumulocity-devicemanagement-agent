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
import json
import logging
import time

from c8ydm.core.firmware_manager import FirmwareManager
from c8ydm.framework.modulebase import Initializer, Listener
from c8ydm.framework.smartrest import SmartRESTMessage


class FirmwareManagement(Listener, Initializer):
    logger = logging.getLogger(__name__)
    fragment = 'c8y_Firmware'
    firmware_manager = FirmwareManager()

    def group(self, seq, sep):
        result = [[]]
        for e in seq:
            if sep not in str(e):
                result[-1].append(e)
            else:
                result[-1].append(e[:e.find(sep)])
                result.append([])
        if result[-1] == []:
            result.pop()
        return result
    
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
        try:
            is_simulated = self.agent.simulated
            if 's/ds' in message.topic and message.messageId == '515':
                messages = self.group(message.values, '\n')[0]
                deviceId = messages.pop(0)
                self.logger.info('Firmware Update for device ' +
                                 deviceId + ' with message ' + str(messages))
                self._set_executing()
                firmwareToInstall = [messages[x:x + 3]
                                     for x in range(0, len(messages), 3)]
                #TODO Handle Firmware Update properly. Not working for Docker and Raspberry Pi.
                self._set_failed('Firmware Update triggered but not supported by this device type')
                alarmMsg = SmartRESTMessage('s/us', '304', ['c8y_FirmwareUpdateAlarm','Firmware Update triggered but not supported by this device type',''])
                #eventMsg = SmartRESTMessage('s/us', '400', ['c8y_FirmwareUpdateEvent', 'Firmware could not be updated as it is not supported by the current Device.'])
                self.agent.publishMessage(alarmMsg)
                """ if is_simulated:
                    #No Firmware Updates are currently supported for docker containers
                    self._set_failed('No Firmware Updates are currently supported for docker containers!')
                else:
                    #TODO Update Firmware for specific devices!
                    self.logger.info('Finished firmware update')
                    #TODO Update Firmware Version
                """
        except Exception as e:
            self._set_failed(e)

    def getSupportedOperations(self):
        return ['c8y_Firmware']

    def getSupportedTemplates(self):
        return []

    def getMessages(self):
        #TODO Check current Firmware version, Update Operation, Update Fragment
        return self.get_firmware_msg()
    
    def get_firmware_msg(self):
        current_kernel_version = self.firmware_manager.get_current_kernel_version()
        dist_name = self.firmware_manager.get_dist_name()
        dist_version = self.firmware_manager.get_dist_version()
        firmware_name = dist_name + "-" + dist_version
        firmware_version = current_kernel_version
        firmware_msg = SmartRESTMessage('s/us', '115', [firmware_name, firmware_version, ''])
        return [firmware_msg]
