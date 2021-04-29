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
from abc import ABCMeta, abstractmethod

class Sensor:
  __metaclass__ = ABCMeta

  def __init__(self, serial, agent):
    self.serial = serial
    self.agent = agent

  '''
  Returns a list of SmartREST messages. Will be called every iteration of the main loop.
  '''
  @abstractmethod
  def getSensorMessages(self): pass

class Listener:
  __metaclass__ = ABCMeta

  def __init__(self, serial, agent):
    self.serial = serial
    self.agent = agent

  '''
  Callback that is executed for any operation received
  '''
  @abstractmethod
  def handleOperation(self, message): pass

  '''
  Returns a list of supported operations
  '''
  @abstractmethod
  def getSupportedOperations(self): pass

  '''
  Returns a list of supported SmartREST templates (X-Ids)
  '''
  @abstractmethod
  def getSupportedTemplates(self): pass

class Initializer:
  __metaclass__ = ABCMeta

  def __init__(self, serial, agent):
    self.serial = serial
    self.agent = agent
  '''
  Returns a list of SmartREST messages. Will be called at the start of the agent
  '''
  @abstractmethod
  def getMessages(self): pass
