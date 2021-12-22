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
from posixpath import dirname
from datetime import datetime
from c8ydm.framework.modulebase import Initializer, Listener
from c8ydm.framework.smartrest import SmartRESTMessage
from os.path import expanduser,exists,dirname
import pathlib
import subprocess

class DownloadConfigfileInitializer(Initializer, Listener):
    logger = logging.getLogger(__name__)
    fragment = 'c8y_DownloadConfigFile'
    

    def getMessages(self):
        return []

    def getSupportedOperations(self):
        return ['c8y_DownloadConfigFile']
    
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
            if 's/ds' in message.topic and message.messageId == '524':
                deviceid = message.values[0]
                binaryurl = message.values[1]
                configtype = message.values[2]
                self._set_executing()
                if 'cumulocity' in binaryurl:  
                    if configtype in configfiles:
                        path = pathlib.Path(configfiles[configtype])
                        self.logger.info(dirname(path))
                        if pathlib.Path(dirname(configfiles[configtype])).exists():
                            process = subprocess.Popen(["cp",str(path),f'{str(path)}_backup'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                            process.wait()
                            if self.agent.rest_client.download_c8y_binary(binaryurl,str(path)) is not None:
                                eventMsg = SmartRESTMessage('s/us', '400', ['c8y_ConfigDownloadEvent', f'Config {configtype} was downloaded to {str(path)}. Backup of old config file was created.'])
                                self.agent.publishMessage(eventMsg)
                                self._set_success(binaryurl)
                            else:
                                self._set_failed("Failed to download file from c8y binary")
                        else:
                            self._set_failed("Directory of config file does not exist")
                    else:
                        self._set_failed("Do not know config file type")
                else:
                    self._set_failed("Currently only c8y binary supported")
            self.logger.debug("download configfile handled")
        except Exception as e:
            self._set_failed(e)

