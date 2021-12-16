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

class LogfileInitializer(Initializer, Listener):
    logger = logging.getLogger(__name__)
    fragment = 'c8y_LogfileRequest'
    

    def getMessages(self):
        msg = SmartRESTMessage('s/us', '118', ['agentlog'])
        return [msg]

    def getSupportedOperations(self):
        return ['c8y_LogfileRequest']
    
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
        failed = SmartRESTMessage('s/us', '502', [self.fragment, reason])
        self.agent.publishMessage(failed)
    
    def handleOperation(self, message):
        mo_id = self.agent.rest_client.get_internal_id(self.agent.serial)  
        try:
            if 's/ds' in message.topic and message.messageId == '522':
                # When multiple operations received just take the first one for further processing
                #self.logger.debug("message received :" + str(message.values))
                deviceid = message.values[0]
                #logtype = message.values[1]
                starttime = message.values[2]
                endtime = message.values[3]
                searchtext = message.values[4]
                searchtext = searchtext.lower()
                maximumlines = message.values[5]
                #print('\n deviceid: {}\n starttime: {}\n endtime: {}\n searchtext:{}\n maximumlines:{} \n'.format(deviceid, starttime, endtime, searchtext, maximumlines))
                self._set_executing()
                #self.logger.info('LogFile HandleOperation Called for '+ deviceid)
                starttime = starttime.replace("T", " ")
                endtime = endtime.replace("T", " ")
                starttime = datetime.fromisoformat(starttime[:16])
                endtime = datetime.fromisoformat(endtime[:16])
                fileLines = []
                searchtextindata = False
                path = self.agent.path
                with open(path / 'agent.log', 'r') as f:
                    for line in f:
                        stripped_line = line.strip().lower()
                        fileLines.append(stripped_line)

                        if(searchtext in line and searchtext !=''):
                            searchtextindata = True

                    if searchtextindata == True:
                        num_lines = len(fileLines)
                        newOutput = ''
                        outputfound = False
                        while(outputfound == False):
                            for index, line in enumerate(fileLines):
                                linematch = re.match("[0-9][0-9][0-9][0-9][-][0-9][0-9]+", line[:16])
                                linehaslogtime = bool(linematch)
                                if(linehaslogtime == True and outputfound == False):
                                    logtime = datetime.fromisoformat(line[:16])
                                    # #self.logger.debug('Starttime: {}\nLogtime: {}\nEndtime:{}'.format(starttime,logtime,endtime))
                                    if starttime <logtime <endtime:
                                        if searchtext in line:
                                            i = 0
                                            while(i<int(maximumlines) and index+i < num_lines):
                                                newOutput+= fileLines[index+i] + '\n'
                                                i+=1
                                                outputfound = True
                        memFile = io.BytesIO(newOutput.encode('utf8'))
                        payload = {'object' : '{"name" : "logfile'+ deviceid+'", "type" : "text/plain" }'}
                        file = [('file' , memFile)]
                        binaryurl = self.agent.rest_client.upload_event_logfile(mo_id, payload, file)
                        if binaryurl:
                            self._set_success(binaryurl)
                            self.logger.debug("LogHandler uploaded Binary under following URL: "+binaryurl)
                        else:
                            self._set_failed('Could not upload logfile')
                                            
                    elif searchtext=='':
                        num_lines = len(fileLines)
                        newOutput = ''
                        outputfound = False
                        while(outputfound == False):
                            for index, line in enumerate(fileLines):
                                linematch = re.match("[0-9][0-9][0-9][0-9][-][0-9][0-9]+", line[:16])
                                linehaslogtime = bool(linematch)
                                if(linehaslogtime == True and outputfound == False):
                                    logtime = datetime.fromisoformat(line[:16])
                                    #self.logger.debug('Starttime: {}\nLogtime: {}\nEndtime:{}'.format(starttime,logtime,endtime))
                                    if starttime <logtime <endtime:
                                        i = 0
                                        while(i<int(maximumlines) and index+i < num_lines):
                                            newOutput+= fileLines[index+i] + '\n'
                                            i+=1
                                            outputfound = True
                        memFile = io.BytesIO(newOutput.encode('utf8'))
                        payload = {'object' : '{"name" : "logfile'+ deviceid+'", "type" : "text/plain" }'}
                        file = [('file' , memFile)]
                        binaryurl = self.agent.rest_client.upload_event_logfile(mo_id, payload, file)
                        if binaryurl:
                            self._set_success(binaryurl)
                            self.logger.debug("LogHandler uploaded Binary under following URL: "+binaryurl)
                        else:
                            self._set_failed('Could not upload logfile')
                    else:
                        #print('Searchstring is not inside file.')
                        self._set_failed('Searchstring is not inside file')
                #after the 'with' statement everything is closed to free the memorybuffer
                f.close()
                self.logger.debug("logfilerequest handled")
        except Exception as e:
            self._set_failed(e)

