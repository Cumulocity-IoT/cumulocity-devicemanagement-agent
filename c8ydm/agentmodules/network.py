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
import logging, time, uuid
import socket
import ipaddress
import requests
from c8ydm.framework.modulebase import Initializer
from c8ydm.framework.smartrest import SmartRESTMessage

class Network(Initializer):
    """ Network Module"""
    logger = logging.getLogger(__name__)
    net_message_id = 'dm100'
    pos_message_id = '402'
    xid = 'c8y-dm-agent-v1.0'
    def_adapter = None

    def getMessages(self):
        net_msg = None
        pos_msg = None
        try:
            self.logger.info(f'Network Initializer called...')
            ip = socket.gethostbyname(socket.gethostname())
            netmask = ipaddress.IPv4Network(ip).netmask
            name = None
            mac = self.get_mac()
            for interface in socket.if_nameindex():
                if_name = interface[1]
                if  if_name.startswith('eth'):
                    name = interface[1]
                    break
            enabled = 1
            net_msg = SmartRESTMessage('s/uc/'+self.xid, self.net_message_id, [self.serial, ip, netmask, name, enabled, mac])
            geo_data = self.get_geo_data()
            if geo_data and geo_data['latitude'] is not None and geo_data['longitude'] is not None:
                pos_msg = SmartRESTMessage('s/us', self.pos_message_id, [geo_data['latitude'], geo_data['longitude']])
            return [net_msg, pos_msg]
        except Exception as ex:
            self.logger.error(f'Error on retrieving Network Details: {ex}')
            return None
        
    def get_geo_data(self):
        """ Retrieves GEO-Data """
        try:
            geo_data = requests.get(f'https://ipapi.co/json/').json()
            self.logger.debug(f'Geo-Data: {geo_data}')
            return geo_data
        except Exception as ex:
            self.logger.error(f'Error retrieving Geodata: {ex}')
            return None
    
    def get_mac(self):
        """ Get Mac Address"""
        mac_num = hex(uuid.getnode()).replace('0x', '').replace('L', '').upper()
        mac_num = mac_num.zfill(12)
        mac = ':'.join(mac_num[i: i + 2] for i in range(0, 11, 2))
        return mac


