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
            memory['free'] = psutil.virtual_memory().free
            memory['used'] = psutil.virtual_memory().used
            memory['total'] = psutil.virtual_memory().total
            memory['percent'] = psutil.virtual_memory().percent
            self.logger.debug("Collected the following memory stats: %s" % (memory))
        except Exception as e:
            self.logger.error('The following error occured: %s' % (str(e)))
        finally:
            return memory

    def getCPUStats(self):
        try:
            cpu = {}
            cpu['guest'] = psutil.cpu_times_percent(interval=1, percpu=False)[0]
            cpu['idle'] = psutil.cpu_times_percent(interval=1, percpu=False)[2]
            cpu['iowait'] = psutil.cpu_times_percent(interval=1, percpu=False)[3]
            cpu['irq'] = psutil.cpu_times_percent(interval=1, percpu=False)[4]
            cpu['system'] = psutil.cpu_times_percent(interval=1, percpu=False)[8]
            cpu['user'] = psutil.cpu_times_percent(interval=1, percpu=False)[9]
            self.logger.debug("Collected the following cpu stats: %s" % (cpu))
        except Exception as e:
            self.logger.error('The following error occured: %s' % (str(e)))
        finally:
            return cpu

    def getDiskStats(self):
        try:
            disk = {}
            disk['total'] = psutil.disk_usage('/').total
            disk['used'] = psutil.disk_usage('/').used
            disk['free'] = psutil.disk_usage('/').free
            disk['percent'] = psutil.disk_usage('/').percent
            self.logger.debug("Collected the following disk stats: %s" % (disk))
        except Exception as e:
            self.logger.error('The following error occured: %s' % (str(e)))
        finally:
            return disk