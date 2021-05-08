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
import logging, time, json, time
import subprocess
from c8ydm.framework.modulebase import Listener, Initializer
from c8ydm.framework.smartrest import SmartRESTMessage
import os


class Restart(Listener, Initializer):
    logger = logging.getLogger(__name__)

    def handleOperation(self, message):
        if 's/ds' in message.topic and message.messageId == '510':
            executing = SmartRESTMessage('s/us', '501', ['c8y_Restart'])
            self.agent.publishMessage(executing)
            try:
                if self.agent.simulated:
                    process = subprocess.Popen(["docker","restart",self.serial],stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    process.wait()
                else:
                    os.system('shutdown -r 1')

            except Exception as e:
                failed = SmartRESTMessage('s/us', '502', ['c8y_Restart', 'Error during Restart:' + str(e)])
                self.agent.publishMessage(failed)

    def getSupportedOperations(self):
        return ['c8y_Restart']

    def getSupportedTemplates(self):
        return []

    def getMessages(self):
        response = SmartRESTMessage('s/us', '503', ['c8y_Restart', 'Restart Successful'])
        return [response]