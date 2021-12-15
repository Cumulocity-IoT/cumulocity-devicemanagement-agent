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
import os
import platform
import distro

class FirmwareManager:
    logger = logging.getLogger(__name__)

    def get_current_kernel_version(self):
        if 'Windows' == platform.system():
            return platform.uname().version
        else:
            os_info = platform.uname()
            kernel = os_info.release
            return kernel
    
    def get_dist_name(self):
        if 'Windows' == platform.system():
            return platform.system()
        else:
            return self._get_linux_dist_name()

    def get_dist_version(self):
        if 'Windows' == platform.system():
            return platform.uname().release
        else:
            return self._get_linux_dist_version()

    def _get_linux_dist_name(self):
        return distro.id()
    
    def _get_linux_dist_version(self):
        return distro.version()