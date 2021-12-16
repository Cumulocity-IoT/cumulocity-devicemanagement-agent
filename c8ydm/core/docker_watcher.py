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
import logging
import subprocess
import json
from c8ydm.framework.smartrest import SmartRESTMessage

class DockerWatcher:
    logger = logging.getLogger(__name__)

    def get_stats(self):
        try:
            rawStats = subprocess.Popen(["docker", "stats", "--no-stream","-a", "--format", "'{{.Container}};{{.Name}};{{.CPUPerc}};{{.MemUsage}}'"],stdout=subprocess.PIPE)
            list = rawStats.stdout.read().decode('utf-8').split('\n')
            a = []
            for i in list:
                dict = {}
                for counter,value in enumerate(i.split(';')):
                    if counter == 0:
                        dict["containerID"] = value.replace("'","")
                    if counter == 1:
                        dict["name"] = value
                        nameString = "name=" + str(value)
                        try:
                            rawStatus = subprocess.Popen(["docker", "ps", "-a", "--format", "'{{.Status}}'", "--filter", nameString ],stdout=subprocess.PIPE)
                            dict["status"] = rawStatus.stdout.read().decode('utf-8').replace("'","")
                        except:
                            self.logger.warning('Status from docker for container %s not valid.'% (str(value)))
                            dict["status"] = "Unknown"
                    if counter == 2:
                        dict["cpu"] = value.replace('%','')
                    if counter == 3:
                        dict["memory"] = value.replace('%','').replace("'","")
                a.append(dict)
            a = a[:-1]
            payload = {}
            payload['c8y_Docker'] = a
            self.logger.debug('The following Docker stats where found: %s'% (str(payload)))
            return json.dumps(payload)
        except Exception as e:
            self.logger.error('The following error occured: %s'% (str(e)))