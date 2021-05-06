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
import logging, time, json
from c8ydm.framework.modulebase import Initializer
from c8ydm.framework.smartrest import SmartRESTMessage

class SmartRestInitializer(Initializer):
    logger = logging.getLogger(__name__)

    def getMessages(self):
        self.logger.info(f'SmartRest Template Initializer called...')
        if not self.agent.rest_client.check_SmartRest_template_exists('ESP123'):
            with open('./config/DM_Agent.json') as f:
                payload = f.read()
            self.agent.rest_client.create_SmartRest_template(payload)
            msg = SmartRESTMessage('s/us', '400', ['c8y_SmartRestTemplateUpload', 'C8Y DM Agent Uploaded a SmartRest Template'])
        return []
    
    