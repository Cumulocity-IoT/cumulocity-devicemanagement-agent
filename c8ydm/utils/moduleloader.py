#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging, inspect, os, pkgutil, importlib
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
