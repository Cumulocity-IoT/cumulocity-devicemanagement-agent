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
import apt
from c8ydm.framework.smartrest import SmartRESTMessage


class AptPackageManager:
    logger = logging.getLogger(__name__)

    def getInstalledSoftware(self, with_update):
        allInstalled = []

        cache = apt.cache.Cache()
        if with_update:
            self.logger.info('Starting apt update....')
            cache.update()
            self.logger.info('apt update finished!')
        cache.open()

        for pkg in cache:
            if (pkg.is_installed and not pkg.shortname.startswith('lib')):
                allInstalled.append(pkg.shortname)
                allInstalled.append(pkg.installed.version)
                allInstalled.append('')

        cache.close()

        return SmartRESTMessage('s/us', '116', allInstalled)

    def install_software(self, software_to_install, with_update):
        cache = apt.cache.Cache()
        if with_update:
            self.logger.info('Starting apt update....')
            cache.update()
            self.logger.info('apt update finished!')
        cache.open()
        for software in software_to_install:
            name = software[0]
            version = software[1]
            # url = software[2]
            action = software[3]
            pkg = cache[name]
            if action == 'install':
                if version == 'latest':
                    self.logger.info('install ' + pkg.shortname + '=latest')
                    pkg.mark_install()
                else:
                    self.logger.info(
                        'install ' + pkg.shortname + '=' + version)
                    candidate = pkg.versions.get(version)
                    pkg.candidate = candidate
                    pkg.mark_install()
            # Software currently installed in the same version
            if action == 'update' and pkg.is_installed and pkg.installed.version == version:
                # no action needed
                self.logger.debug('existing ' + pkg.shortname +
                                '=' + pkg.installed.version)
            if action == 'update' and pkg.is_installed and pkg.installed.version != version:
                self.logger.info('install ' + pkg.shortname + '=' + version)
                candidate = pkg.versions.get(version)
                pkg.candidate = candidate
                pkg.mark_install()
            if action == 'delete' and pkg.is_installed:
                self.logger.info('delete ' + pkg.shortname +
                                '=' + pkg.installed.version)
                pkg.mark_delete()
        try:
            self.logger.info('Starting apt install/removal of Software..')
            cache.commit()
            self.logger.info("Install/Removal of Software finished!")
        except Exception as e:
            self.logger.error(e)

        return []

    """ Old Deprecated Version of Software Updates """
    def installSoftware(self, toBeInstalled, with_update):
        cache = apt.cache.Cache()
        if with_update:
            self.logger.info('Starting apt update....')
            cache.update()
            self.logger.info('apt update finished!')
        cache.open()

        for software in toBeInstalled:
            pkg = cache[software[0]]
            # Software currently installed in the same version
            if pkg.is_installed and pkg.installed.version == software[1]:
                # no action needed
                self.logger.debug('existing ' + pkg.shortname +
                                    '=' + pkg.installed.version)
            else:
                self.logger.info(
                    'install ' + pkg.shortname + '=' + software[1])
                candidate = pkg.versions.get(software[1])
                pkg.candidate = candidate
                pkg.mark_install()

        # Check what needs to be uninstalled
        toBeInstalledSoftware = [i[0] for i in toBeInstalled]
        for pkg in cache:
            if not pkg.shortname.startswith('lib') and pkg.is_installed and pkg.shortname not in toBeInstalledSoftware:
                self.logger.info('delete ' + pkg.shortname +
                                    '=' + pkg.installed.version)
                pkg.mark_delete()

        try:
            self.logger.info('Starting apt install/removal of Software..')
            cache.commit()
            self.logger.info("Install/Removal of Software finished!")
        except Exception as e:
            self.logger.error(e)

        return []
