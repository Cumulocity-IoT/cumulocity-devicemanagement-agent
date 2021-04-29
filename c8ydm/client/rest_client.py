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

import requests
import logging
import json
from base64 import b64encode

class RestClient():

    def __init__(self, agent):
        self.logger = logging.getLogger(__name__)
        self.serial = agent.serial
        self.configuration = agent.configuration
        self.base_url = agent.url
        if not self.base_url.startswith('http'):
            self.base_url = f'https://{self.base_url}'
        self.token = agent.token

    def get_auth_header(self):
        if self.token:
            return {'Authorization': 'Bearer '+self.token}
        else:
            credentials = self.configuration.getCredentials()
            self.tenant = credentials[0]
            self.user = credentials[1]
            self.password = credentials[2]
            auth_string = f'{self.tenant}/{self.user}:{self.password}'
            encoded_auth_string = b64encode(
                bytes(auth_string, 'utf-8')).decode('ascii')
            return {'Authorization': 'Basic '+encoded_auth_string,}

    def update_managed_object(self, internal_id, payload):
        self.logger.info('Update of managed Object')
        try:
            url = f'{self.base_url}/inventory/managedObjects/{internal_id}'
            headers = self.get_auth_header()
            headers['Content-Type'] ='application/json'
            self.logger.debug(f'Sending Request to url {url}')
            response = requests.request("PUT", url, headers=headers, data = payload)
            self.logger.debug('Response from request: ' + str(response.text))
            self.logger.debug('Response from request with code : ' + str(response.status_code))
            if response.status_code == 200 or response.status_code == 201:
                self.logger.info('Managed object updated in C8Y')
                return True
            else:
                self.logger.warning('Managed object not updated in C8Y')
                return False
        except Exception as e:
            self.logger.error('The following error occured: %s' % (str(e)))
    
    def get_internal_id(self, external_id):
        try:
            self.logger.info('Checking against indentity service what is internalID in C8Y')
            url = f'{self.base_url}/identity/externalIds/c8y_Serial/{external_id}'
            self.logger.debug(f'Sending Request to url {url}')
            headers = self.get_auth_header()
            headers['Content-Type'] ='application/json'
            headers['Accept'] = 'application/json'
            response = requests.request("GET", url, headers=headers)
            self.logger.debug('Response from request: ' + str(response.text))
            self.logger.debug('Response from request with code : ' + str(response.status_code))
            if response.status_code == 200:
                self.logger.info('Managed object exists in C8Y')
                json_data = json.loads(response.text)
                internalID = json_data['managedObject']['id']
                self.logger.info("The interalID for " + str(external_id) + " is " + str(internalID))
                self.logger.debug('Returning the internalID')
                return internalID
            else:
                self.logger.warning('Response from request: ' + str(response.text))
                self.logger.warning('Got response with status_code: ' +
                            str(response.status_code))
                return None
        except Exception as e:
            self.logger.error('The following error occured: %s' % (str(e)))
            return None
