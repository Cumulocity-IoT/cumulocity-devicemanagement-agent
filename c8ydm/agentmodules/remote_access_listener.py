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
"""Cloud Remote Access Listener"""
import logging
from typing import List, Optional

from requests.auth import HTTPBasicAuth
from c8ydm.framework.modulebase import Listener
from c8ydm.framework.smartrest import SmartRESTMessage
from c8ydp.device_proxy import DeviceProxy, WebSocketFailureException
from c8ydm.utils import Configuration

class RemoteAccessListener(Listener):
    """Establishes Remote Access Connections"""
    xid = 'c8y-dm-agent-v1.0'
    logger = logging.getLogger(__name__)
    remote_access_op_template = 'dm600'
    remote_access_default_template = '530'
    fragment = 'c8y_RemoteAccessConnect'

    def _set_executing(self):
        executing = SmartRESTMessage('s/us', '501', [self.fragment])
        self.agent.publishMessage(executing)

    def _set_success(self):
        success = SmartRESTMessage('s/us', '503', [self.fragment])
        self.agent.publishMessage(success)

    def _set_failed(self, reason):
        failed = SmartRESTMessage('s/us', '502', [self.fragment, reason])
        self.agent.publishMessage(failed)

    def handleOperation(self, message):
        """Callback that is executed for any operation received

            Raises:
            Exception: Error when handling the operation
       """
        try:
            #self.logger.debug(
            #    f'Handling Cloud Remote Access operation: listener={__name__}, message={message}')

            if message.messageId == self.remote_access_default_template or message.messageId == self.remote_access_op_template:
                self._set_executing()
                self._proxy_connect(message)
            return

        except Exception as ex:
            self.logger.error(f'Handling operation error. exception={ex}')
            self._set_failed(str(ex))
            # raise

    def _proxy_connect(self, message):
        """
        Creates the Device Proxy and connects to WebSocket and TCP Port
        """
        tcp_host = message.values[1]
        tcp_port = int(message.values[2])
        connection_key = message.values[3]

        config = self.agent.configuration
        credentials = config.getCredentials()

        token = self.agent.token
        tenantuser = credentials[0]+'/'+ credentials[1]
        password = credentials[2]

        if token is None and tenantuser is None and password is None:
            raise WebSocketFailureException(
                'OAuth Token or tenantuser and password must be provided!')
        base_url = config.getValue('mqtt', 'url')
         # Not sure which buffer size is good, starting with 16 KB (16 x 1024)
        #buffer_size = self.utils.config.getint('remote-connect', 'tcp.buffer.size')
        self._device_proxy = DeviceProxy(
            tcp_host, tcp_port, None, connection_key, base_url, tenantuser, password, token, None)
        self._device_proxy.connect()
        self._set_success()

    def getSupportedOperations(self):
        return [self.fragment]

    def getSupportedTemplates(self):
        return [self.xid]
