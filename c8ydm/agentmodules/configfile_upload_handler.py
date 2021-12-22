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
from os.path import expanduser,exists,isfile
import pathlib

class UploadConfigfileInitializer(Initializer, Listener):
    logger = logging.getLogger(__name__)
    fragment = 'c8y_UploadConfigFile'
    

    def getMessages(self):
        msg = SmartRESTMessage('s/us', '119', ['sshd','agent'])
        return [msg]

    def getSupportedOperations(self):
        return ['c8y_UploadConfigFile']
    
    def getSupportedTemplates(self):
        return []

    def _set_executing(self):
        executing = SmartRESTMessage('s/us', '501', [self.fragment])
        print("Executing MSG send")
        self.agent.publishMessage(executing)

    #datei anhängen
    def _set_success(self, url):
        success = SmartRESTMessage('s/us', '503', [self.fragment, url])
        print("Success MSG send")
        self.agent.publishMessage(success)

    def _set_failed(self, reason):
        failed = SmartRESTMessage('s/us', '502', [self.fragment,reason])
        self.logger.error(f'Operation failed, reason: {reason}')
        self.agent.publishMessage(failed)
    
    def handleOperation(self, message):
        mo_id = self.agent.rest_client.get_internal_id(self.agent.serial)
        home = expanduser('~')
        root = pathlib.Path(home + '/.cumulocity')
        configfiles = {'sshd': '/etc/ssh/sshd_config', 'agent': f'{root}/agent.ini'}   
        try:
            if 's/ds' in message.topic and message.messageId == '526':
                deviceid = message.values[0]
                configtype = message.values[1]
                self._set_executing()
                if configtype in configfiles:
                    path = pathlib.Path(configfiles[configtype])
                    if isfile(path):
                        f = open(path, "rb")
                        memFile = f.read()
                        payload = {'object' : '{"name" : "configfile'+ deviceid+'", "type" : "text/plain" }'}
                        file = [('file' , memFile)]
                        binaryurl = self.agent.rest_client.upload_event_configfile(mo_id, payload, file, configtype, str(path))
                        if binaryurl:
                            self._set_success(binaryurl)
                            self.logger.debug("UploadConfigHandler uploaded Binary under following URL: "+binaryurl)
                        else:
                            self._set_failed('Could not upload configfile')
                    else:
                       self._set_failed("Config file does not exist") 
                else:
                    self._set_failed("Do not know config file type")
            elif 's/ds' in message.topic and message.messageId == '520':
                self._set_executing()
                self._set_failed('Legacy configuration snapshot currently not supported')
            self.logger.debug("upload configfile handled")
        except Exception as e:
            self._set_failed(e)

