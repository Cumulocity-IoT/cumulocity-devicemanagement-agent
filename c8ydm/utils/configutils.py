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
import configparser, logging, os
from shutil import copyfile
from configparser import NoOptionError, NoSectionError

class Configuration():
  logger = logging.getLogger(__name__)
  credentialsCategory = 'secret'
  bootstrapTenant = 'c8y.bootstrap.tenant'
  bootstrapUser = 'c8y.bootstrap.user'
  bootstrapPassword = 'c8y.bootstrap.password'
  tenant = 'c8y.tenant'
  user = 'c8y.username'
  password = 'c8y.password'

  def __init__(self, path):
    self.configPath = path + '/agent.ini'
    self.configuration = configparser.ConfigParser()
    self.readFromFile()
    self.overrideFromEnv()

  def readFromFile(self):
    self.configuration.read(self.configPath)

  def overrideFromEnv(self):
    """
    expands environment variables starting with `C8Y` in values.
    Mapping rules from environment variable name to config key:

    - Prefix C8YDM_<PREFIX>_ means what section the option belongs to
    - Upper case letters are mapped to lower case letters
    - Double underscore __ is mapped to .

    e.g. `C8YDM_SECRET_C8Y__TENANT` is mapped to `c8y.tenant` in [secret] section.
    """
    prefix = 'C8YDM_'
    envs = {k.replace(prefix, '', 1): v for k, v in os.environ.items() if k.startswith(prefix)}
    for key, value in envs.items():
      # note: '_' in category is not allowed
      category, key0 = key.lower().split('_', 1)
      key1 = key0.replace('__', '.')
      # todo: print override env in debug log. you need to modify main.py
      # because log level is known only after the creation of this object
      self.setValue(category, key1, value)

  def getValue(self, category, key):
    try:
      return self.configuration.get(category, key)
    except (NoOptionError, NoSectionError):
      return None
  
  def getBooleanValue(self, category, key):
    try:
      return self.configuration.getboolean(category, key)
    except (NoOptionError, NoSectionError):
      return None

  def setValue(self, category, key, value):
    if category not in self.configuration.sections():
      self.configuration.add_section(category)
    self.configuration.set(category, key, value)
    with open(self.configPath, 'w') as cfgfile:
      self.configuration.write(cfgfile)

  def getBootstrapCredentials(self):
    tenant = self.getValue(self.credentialsCategory, self.bootstrapTenant)
    user = self.getValue(self.credentialsCategory, self.bootstrapUser)
    password = self.getValue(self.credentialsCategory, self.bootstrapPassword)

    if tenant is not None and user is not None and password is not None:
      return [tenant, user, password]
    return None

  def getCredentials(self):
    tenant = self.getValue(self.credentialsCategory, self.tenant)
    user = self.getValue(self.credentialsCategory, self.user)
    # if the password contains % it needs to be escaped as % has special meaning in configparser
    password = self.getValue(self.credentialsCategory, self.password.replace('%','%%'))

    if tenant is not None and user is not None and password is not None:
      return [tenant, user, password]
    return None

  def writeCredentials(self, tenant, user, password):
    #TODO Write this in a secure storage.
    self.configuration.set(self.credentialsCategory, self.tenant, tenant)
    self.configuration.set(self.credentialsCategory, self.user, user)
    self.configuration.set(self.credentialsCategory, self.password, password.replace('%', '%%'))
    with open(self.configPath, 'w') as cfgfile:
      self.configuration.write(cfgfile)

  def getConfigString(self):
    configs = []
    for section in self.configuration.sections():
      if section == 'secret':
        continue
      for (key, val) in self.configuration.items(section):
        configs.append(section + '.' + key + '=' + val)
    return '\n'.join(configs)

  def writeConfigString(self, configString):
    configLines = configString.split('\n')
    newConfiguration = configparser.ConfigParser()
    newConfiguration.add_section('secret')
    for (key, val) in self.configuration.items('secret'):
      newConfiguration.set('secret', key, val.replace('%', '%%'))
    for configLine in configLines:
      splitted = configLine.split('.', 1)
      section = splitted[0]
      if section == 'secret':
        continue
      splitted = splitted[1].split('=', 1)
      key = splitted[0]
      value = splitted[1]
      if not newConfiguration.has_section(section):
        newConfiguration.add_section(section)
      newConfiguration.set(section, key, value)
    with open(self.configPath, 'w') as cfgfile:
      newConfiguration.write(cfgfile)
    self.configuration = newConfiguration

