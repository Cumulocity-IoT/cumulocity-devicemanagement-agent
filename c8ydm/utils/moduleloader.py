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
import inspect
import os
import pkgutil
import importlib
from c8ydm.framework.modulebase import Sensor, Listener, Initializer
import c8ydm.agentmodules as agentmodules

def findAgentModules():
    
    pkgpath = os.path.dirname(agentmodules.__file__)
    modules = {
        'sensors': [],
        'listeners': [],
        'initializers': []
    }
    for name in pkgutil.iter_modules([pkgpath]):
        logging.debug(name)
        currentModule = 'c8ydm.agentmodules.' + name[1]
        i = importlib.import_module(currentModule)
        for name, obj in inspect.getmembers(i):
            if inspect.isclass(obj) and obj.__module__ == currentModule:
                if issubclass(obj, Sensor):
                    logging.debug('Import sensor: ' + name)
                    modules['sensors'].append(obj)
                if issubclass(obj, Listener):
                    logging.debug('Import listener: ' + name)
                    modules['listeners'].append(obj)
                if issubclass(obj, Initializer):
                    logging.debug('Import initializer: ' + name)
                    modules['initializers'].append(obj)
    return modules
