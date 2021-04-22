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
from c8ydm.framework.smartrest import SmartRESTMessage
from c8ydm.framework.modulebase import Listener
from c8ydm.core.apt_package_manager import AptPackageManager

class DeviceProfileListener(Listener):
    logger = logging.getLogger(__name__)
    fragment = 'c8y_DeviceProfile'
    device_profiles_message_id = '527'
    apt_package_manager = AptPackageManager()

    def _set_executing(self):
        executing = SmartRESTMessage('s/us', '501', [self.fragment])
        self.agent.publishMessage(executing)

    def _set_success(self):
        success = SmartRESTMessage('s/us', '503', [self.fragment])
        self.agent.publishMessage(success)

    def _set_failed(self, reason):
        failed = SmartRESTMessage('s/us', '502', [self.fragment, reason])
        self.agent.publishMessage(failed)
    
    def _apply_device_profile(self, id):
        msg = None
        if id == None:
            msg = SmartRESTMessage('s/us', '121', ['true'])
        else:
            msg = SmartRESTMessage('s/us', '121', ['true', id])
        self.agent.publishMessage(msg)
    
    def _install_software_packages(self, messages):
        softwareToInstall = [messages[x:x + 4]
                                     for x in range(0, len(messages), 4)]
        self.logger.info(f'Software will be changed: {softwareToInstall}')
        errors = self.apt_package_manager.install_software(
                    softwareToInstall, True)
        return errors
    
    def _process_device_profile_msg(self, message):
        operation_values = {'$FW': [], '$SW': [], '$CONF': []}
        active_operation = ''

        for value in message.values:
            active_operation = '$FW' if value == '$FW' else active_operation
            active_operation = '$SW' if value == '$SW' else active_operation
            active_operation = '$CONF' if value == '$CONF' else active_operation

            if active_operation and not value.startswith('$'):
                operation_values[active_operation].append(value)
                    
        
        # TODO Firmware Block 
               
        # Software Block
        if len(operation_values['$SW']) > 0:
            self.logger.debug(f'Software Operations of Device Profile: {operation_values["$SW"]}')
            errors = self._install_software_packages(operation_values['$SW'])
            if len(errors) == 0:
                self._set_success()
            else:
                # finished with errors
                self._set_failed(errors)
            self.agent.publishMessage(
                self.apt_package_manager.getInstalledSoftware(True))
                    
        #TODO Configuration Block

    
    def handleOperation(self, message):
        """Callback that is executed for any operation received

            Raises:
            Exception: Error when handling the operation
        """
        # Example Msg 527,1da499426b9e,$SW,nano,latest,test,install
        if 's/ds' in message.topic and self.device_profiles_message_id == message.messageId:
            try:
                messages = message.values
                self._set_executing()
                self.logger.info(f'Device Profile Message received: {messages}')
                
                self._apply_device_profile(None)
                self._process_device_profile_msg(message)
                self._set_success()
            except Exception as ex:
                self.logger.exception(ex)
                self._set_failed(str(ex))

    def getSupportedOperations(self):
        return [self.fragment]

    def getSupportedTemplates(self):
        return []


