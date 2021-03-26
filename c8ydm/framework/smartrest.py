#!/usr/bin/env python
# -*- coding: utf-8 -*-

class SmartRESTMessage:

  def __init__(self, topic, messageId, values):
    self.topic = topic
    self.messageId = messageId
    self.values = values

  def getMessage(self):
    return str(self.messageId) + ',' + ','.join(map(str,self.values))
