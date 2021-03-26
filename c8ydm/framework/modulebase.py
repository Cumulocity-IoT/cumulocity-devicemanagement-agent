#!/usr/bin/env python
# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod

class Sensor:
  __metaclass__ = ABCMeta

  def __init__(self, serial):
    self.serial = serial

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

  def __init__(self, serial):
    self.serial = serial

  '''
  Returns a list of SmartREST messages. Will be called at the start of the agent
  '''
  @abstractmethod
  def getMessages(self): pass
