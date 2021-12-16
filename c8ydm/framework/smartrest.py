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
class SmartRESTMessage:

  def __init__(self, topic, messageId, values):
    self.topic = topic
    self.messageId = messageId
    self.values = values

  def getMessage(self):
    values = []
    # Applies the necessary SmartREST escaping to any string passed to the function
    for value in map(str, self.values):
      value = value.replace('"', '""')

      should_escape = '"' in value or ',' in value or '\n' in value or \
        '\r' in value or '\t' in value or value.startswith(' ') or \
          value.endswith(' ')

      if should_escape:
        value = '"{}"'.format(value)

      values.append(value)
    msg = str(self.messageId) + ',' + ','.join(map(str,values))
    return msg.rstrip(', ')
