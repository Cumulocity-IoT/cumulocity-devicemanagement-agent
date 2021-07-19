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
import logging, time, os, io
from c8ydm.framework.modulebase import Initializer, Listener
from c8ydm.framework.smartrest import SmartRESTMessage

class LogfileInitializer(Initializer, Listener):
    logger = logging.getLogger(__name__)
    fragment = 'c8y_LogfileRequest'

    def getMessages(self):
        self.logger.info(f'\n\n*****LogListener Initializer called*****\n')
        msg = SmartRESTMessage('s/us', '118', ['agentlog'])
        return [msg]

    def getSupportedOperations(self):
        return ['c8y_LogfileRequest']
    
    def getSupportedTemplates(self):
        return []

    def _set_executing(self):
        executing = SmartRESTMessage('s/us', '501', [self.fragment])
        self.agent.publishMessage(executing)

    #datei anhängen
    def _set_success(self, url):
        success = SmartRESTMessage('s/us', '503', [self.fragment, url])
        #restclient url holen und mitschicken
        self.agent.publishMessage(success)

    def _set_failed(self, reason):
        failed = SmartRESTMessage('s/us', '502', [self.fragment, reason])
        self.agent.publishMessage(failed)
    
    def handleOperation(self, message):
         if 's/ds' in message.topic and message.messageId == '522':
            # When multiple operations received just take the first one for further processing
            #self.logger.debug("message received :" + str(message.values))
            deviceid = message.values[0]
            #logtype = message.values[1]
            starttime = message.values[2]
            endtime = message.values[3]
            searchtext = message.values[4]
            maximumlines = message.values[5]
            print('\n deviceid: {}\n starttime: {}\n endtime: {}\n searchtext:{}\n maximumlines:{} \n'.format(deviceid, starttime, endtime, searchtext, maximumlines))
          #self.logger.info('LogFile HandleOperation Called for '+ deviceid)
            with open('/root/.cumulocity/agent.log', 'r') as f:
                data = f.read()
                f.close()
            if searchtext in data and searchtext != '':
                print('Searchstring is inside file')

            elif searchtext=='':
                print('No Searchstring provided')
                #io.StringIO creates string file # bytesIO creates a binary file
                with io.BytesIO(data.encode('utf8')) as memFile:
                    print(memFile.read())
                    print('check')
                #after the 'with' statement the memFile gets closed to free the memorybuffer

                
            else:
                print('Searchstring is not inside file.')
                #need to know the fragmentname for a response that the request failed
                self._set_failed('Searchstring is not inside the file')
        
            # with the following lines you can view the current directory structure
            # entries = os.listdir()
            # for entry in entries:
            #     print(entry)
           