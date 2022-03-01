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
import re
import logging
from operator import contains
import time
import subprocess as sp

from c8ydm.core.apt_package_manager import AptPackageManager
from c8ydm.framework.modulebase import Initializer, Listener
from c8ydm.framework.smartrest import SmartRESTMessage


class SoftwareManager(Listener, Initializer):
    """ Software Update Module"""
    logger = logging.getLogger(__name__)
    apt_package_manager = AptPackageManager()

    def group(self, seq, sep):
        result = [[]]
        for e in seq:
            #logging.info("e: "+str(e) +" sep: " + str(sep))
            if sep not in str(e):
                result[-1].append(e)
            else:
                result[-1].append(e[:e.find(sep)])
                result.append([])

        if result[-1] == []:
            result.pop()  # thx iBug's comment
        return result
    
    def get_filename_from_cd(self, cd):
        """
        Get filename from content-disposition
        """
        if not cd:
            return None
        fname = re.findall('filename=(.+)', cd)
        if len(fname) == 0:
            return None
        return fname[0]

    def handleOperation(self, message):
        try:
            if 's/ds' in message.topic and message.messageId == '528':
                # When multiple operations received just take the first one for further processing
                #self.logger.debug("message received :" + str(message.values))
                messages = self.group(message.values, '\n')[0]
                deviceId = messages.pop(0)
                binary_included = False
                self.logger.info('Software update for device ' +
                                 deviceId + ' with message ' + str(messages))
                executing = SmartRESTMessage(
                    's/us', '501', ['c8y_SoftwareUpdate'])
                self.agent.publishMessage(executing)
                softwareToInstall = [messages[x:x + 4]
                                     for x in range(0, len(messages), 4)]
                for software in softwareToInstall:
                    name = software[0]
                    version = software[1]
                    url = software[2]
                    action = software[3]
                    if 'binaries' in url:
                        # File provided
                        binary_included = True
                if not binary_included:
                    errors = self.apt_package_manager.install_software(
                        softwareToInstall, True)
                    self.logger.info('Finished all software update')
                    if len(errors) == 0:
                        # finished without errors
                        finished = SmartRESTMessage(
                            's/us', '503', ['c8y_SoftwareUpdate'])
                    else:
                        # finished with errors
                        finished = SmartRESTMessage(
                            's/us', '502', ['c8y_SoftwareUpdate', ' - '.join(errors)])
                    self.agent.publishMessage(finished)
                    self.agent.publishMessage(
                        self.apt_package_manager.getInstalledSoftware(False))
                else:
                    # Binary included in software update
                    self.logger.info(f'Software Updated with provided file {url}')
                    file = self.agent.rest_client.download_c8y_binary(url)
                    self.logger.info(f'File to be installed: {file}')
                    if action == 'install' or action == 'update':
                        #result = sp.run(["dpkg","-i", file], stdout=sp.PIPE, stderr=sp.PIPE)
                        result = sp.run(["apt-get","-y","install",file], stdout=sp.PIPE, stderr=sp.PIPE)
                        errors = result.stderr.decode("utf-8")
                        self.logger.info(f'Result of subprocess Error: {errors}')
                        if errors:
                            failed = SmartRESTMessage('s/us', '502', ['c8y_SoftwareUpdate', errors])
                            self.agent.publishMessage(failed)
                        else:
                            finished = SmartRESTMessage(
                                's/us', '503', ['c8y_SoftwareUpdate'])
                            self.agent.publishMessage(finished)
                            self.agent.publishMessage(
                                self.apt_package_manager.getInstalledSoftware(False))
                    
                
            if 's/ds' in message.topic and message.messageId == '516':
                # When multiple operations received just take the first one for further processing
                #self.logger.debug("message received :" + str(message.values))
                messages = self.group(message.values, '\n')[0]
                #self.logger.info("message processed:" + str(messages))
                deviceId = messages.pop(0)
                self.logger.info('Software update for device ' +
                                 deviceId + ' with message ' + str(messages))
                executing = SmartRESTMessage(
                    's/us', '501', ['c8y_SoftwareList'])
                self.agent.publishMessage(executing)
                softwareToInstall = [messages[x:x + 3]
                                     for x in range(0, len(messages), 3)]
                errors = self.apt_package_manager.installSoftware(
                    softwareToInstall, True)
                self.logger.info('Finished all software update')
                if len(errors) == 0:
                    # finished without errors
                    finished = SmartRESTMessage(
                        's/us', '503', ['c8y_SoftwareList'])
                else:
                    # finished with errors
                    finished = SmartRESTMessage(
                        's/us', '502', ['c8y_SoftwareList', ' - '.join(errors)])
                installed_software = self.apt_package_manager.get_installed_software_json(False)
                mo_id = self.agent.rest_client.get_internal_id(self.agent.serial)
                self.agent.rest_client.update_managed_object(mo_id, json.dumps(installed_software))
                self.agent.publishMessage(finished)
                #self.agent.publishMessage(
                #    self.apt_package_manager.getInstalledSoftware(False))
        except Exception as e:
            self.logger.exception(e)
            failed = SmartRESTMessage(
                's/us', '502', ['c8y_SoftwareList', str(e)])
            self.agent.publishMessage(failed)
            failed = SmartRESTMessage(
                's/us', '502', ['c8y_SoftwareUpdate', str(e)])
            self.agent.publishMessage(failed)

    def getSupportedOperations(self):
        return ['c8y_SoftwareUpdate', 'c8y_SoftwareList']

    def getSupportedTemplates(self):
        return []

    def getMessages(self):
        installed_software = self.apt_package_manager.get_installed_software_json(False)
        mo_id = self.agent.rest_client.get_internal_id(self.agent.serial)
        self.agent.rest_client.update_managed_object(mo_id, json.dumps(installed_software))
        return None
