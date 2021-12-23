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
from requests import get
from c8ydm.framework.modulebase import Initializer
from c8ydm.framework.smartrest import SmartRESTMessage
from c8ydm.core.geo_position_resolver import GeoPositionResolver

class Network(Initializer):
    logger = logging.getLogger(__name__)
    net_message_id = 'dm100'
    pos_message_id = '402'
    xid = 'c8y-dm-agent-v1.0'
    def_adapter = None
    geo_pos_resolver = GeoPositionResolver()

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
            pub_ip = self.get_public_ip()
            lat_lng = self.geo_pos_resolver.get_pos_by_ip(pub_ip)
            
            if lat_lng and lat_lng['lat'] is not None and lat_lng['lng'] is not None:
                pos_msg = SmartRESTMessage('s/us', self.pos_message_id, [lat_lng['lat'], lat_lng['lng']])
            return [net_msg, pos_msg]
        except Exception as ex:
            self.logger.error(f'Error on retrieving Network Details: {ex}')
            return None
        
    
    def get_public_ip(self):
        try:
            ip = get('https://api.ipify.org').text
            self.logger.debug(f'Public IP: {ip}')
            return ip
        except Exception as ex:
            self.logger.error(f'Error retrieving public IP: {ex}')
            return None
    
    def get_mac(self):
        mac_num = hex(uuid.getnode()).replace('0x', '').replace('L', '').upper()
        mac_num = mac_num.zfill(12)
        mac = ':'.join(mac_num[i: i + 2] for i in range(0, 11, 2))
        return mac


