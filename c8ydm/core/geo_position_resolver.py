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
import logging
import subprocess

class GeoPositionResolver:
    logger = logging.getLogger(__name__)

    def get_pos_by_ip(self, ip):
        lat_lng = {}
        try:
            if ip:
                self.logger.info(f'Getting GEO Data for IP {ip}...')
                geo_ip_data = subprocess.Popen(['geoiplookup', ip], stdout=subprocess.PIPE)
                output = geo_ip_data.stdout.read().decode('utf-8')
                if output:
                    self.logger.debug(f'Output of geoiplookup {output}')
                    geo_data_list = output.split('\n')
                    for line in geo_data_list:
                        if "GeoIP City Edition" in line:
                            geo_pos_list = line.split(', ')
                            self.logger.debug(f'list of Geo Data {geo_pos_list}')
                            lat_lng['lat'] = geo_pos_list[6]
                            lat_lng['lng'] = geo_pos_list[7]
            return lat_lng
        except Exception as ex:
            self.logger.error(f'Error on retrieving GEO Position Data from IP: {ex}')
            return lat_lng
