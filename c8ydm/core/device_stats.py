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
import psutil



class DeviceStats:
    logger = logging.getLogger(__name__)
    
    def __init__(self):
        pass

    def getMemoryStats(self):
        try:
            memory = {}
            memory['free'] = {"value": psutil.virtual_memory().free}
            memory['used'] = {"value": psutil.virtual_memory().used}
            memory['total'] = {"value": psutil.virtual_memory().total}
            memory['percent'] = {"value": psutil.virtual_memory().percent}
            self.logger.debug("Collected the following memory stats: %s" % (memory))
            return memory
        except Exception as e:
            self.logger.error('The following error occured: %s' % (str(e)))

    def getCPUStats(self):
        try:
            cpu = {}
            cpu['load'] = {'value': psutil.cpu_percent(0)}
            self.logger.debug("Collected the following cpu stats: %s" % (cpu))
            return cpu
        except Exception as e:
            self.logger.error('The following error occured: %s' % (str(e)))

    def getDiskStats(self):
        try:
            disk = {}
            disk['total'] = {'value': psutil.disk_usage('/').total}
            disk['used'] = {'value': psutil.disk_usage('/').used}
            disk['free'] = {'value': psutil.disk_usage('/').free}
            disk['percent'] = {'value': psutil.disk_usage('/').percent}
            self.logger.debug("Collected the following disk stats: %s" % (disk))
            return disk
        except Exception as e:
            self.logger.error('The following error occured: %s' % (str(e)))