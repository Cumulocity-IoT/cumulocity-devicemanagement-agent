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
import platform
import distro
from c8ydm.framework.smartrest import SmartRESTMessage

if 'Linux' == platform.system() and distro.id() in ['debian','ubuntu','raspbian']:
    import apt
else:
    apt = None

class AptPackageManager:
    logger = logging.getLogger(__name__)
    
    """
    DEPRECATED - will probably hit the 16 KB payload limit size of MQTT when used.
    """
    def getInstalledSoftware(self, with_update):
        allInstalled = []
        if apt:
            cache = apt.cache.Cache()
            if with_update:
                self.logger.info('Starting apt update....')
                cache.update()
                self.logger.info('apt update finished!')
            cache.open()

            for pkg in cache:
                if (pkg.is_installed and not pkg.shortname.startswith('lib') and not pkg.shortname.startswith('python')):
                    allInstalled.append(pkg.shortname)
                    allInstalled.append(pkg.installed.version)
                    allInstalled.append('apt')
                    #FIXME Bug in 10.14 Cumulocity that URL must not be null and is mandatory
                    allInstalled.append('test')

            cache.close()

        return [SmartRESTMessage('s/us', '140', allInstalled)]

    """
    Returns the software list as JSON to be sent to the new Adv. software management microservice
    """
    def get_installed_software_json(self, with_update):
        software_list = []
        #all_installed = {
        #    "c8y_SoftwareList": software_list
        #}
        if apt:
            cache = apt.cache.Cache()
            if with_update:
                self.logger.info('Starting apt update....')
                cache.update()
                self.logger.info('apt update finished!')
            cache.open()
            for pkg in cache:
                if (pkg.is_installed):
                    #FIXME Bug in 10.14 Cumulocity that URL must not be null and is mandatory
                    software = {
                        "name": pkg.shortname,
			            "version": pkg.installed.version,
                        "softwareType": "apt",
			            "url": "test"
                    }
                    software_list.append(software)
            cache.close()
        return software_list

    
    def install_software(self, software_to_install, with_update, with_type):
        errors = []
        software_installed = []
        try:
            if apt:
                cache = apt.cache.Cache()
                if with_update:
                    self.logger.info('Starting apt update....')
                    cache.update()
                    self.logger.info('apt update finished!')
                cache.open()
                for software in software_to_install:
                
                    if with_type:
                        name = software[0]
                        version = software[1]
                        #type = software[2]
                        #url = software[3]
                        action = software[4]
                    else:
                        name = software[0]
                        version = software[1]
                        #url = software[2]
                        action = software[3]
                    pkg = cache[name]
                    if pkg is None:
                        errors.append('No Software found with name '+ name)
                    else:
                        if action == 'install':
                            if version == 'latest':
                                self.logger.info('install ' + pkg.shortname + '=latest')
                                pkg_version = pkg.versions[0].version
                                pkg.mark_install()
                                software = {
                                    "name": pkg.shortname,
                                    "version": pkg_version,
                                    "type": "apt",
                                    "url": "",
                                    "action": "install"
                                }
                                software_installed.append(software)
                            else:
                                self.logger.info(
                                    'install ' + pkg.shortname + '=' + version)
                                candidate = pkg.versions.get(version)
                                if candidate == None:
                                    errors.append('Version '+ version +' not available in Repo!')
                                else:
                                    pkg.candidate = candidate
                                    pkg.mark_install()
                                    software = {
                                        "name": pkg.shortname,
                                        "version": version,
                                        "type": "apt",
                                        "url": "",
                                        "action": "install"
                                    }
                                    software_installed.append(software)
                        # Software currently installed in the same version
                        if action == 'update' and pkg.is_installed and pkg.installed.version == version:
                            # no action needed
                            self.logger.debug('existing ' + pkg.shortname +
                                            '=' + pkg.installed.version)
                        if action == 'update' and pkg.is_installed and pkg.installed.version != version:
                            self.logger.info('install ' + pkg.shortname + '=' + version)
                            candidate = pkg.versions.get(version)
                            if candidate == None:
                                    errors.append('Version '+ version +' not available in Repo!')
                            else:
                                pkg.candidate = candidate
                                pkg.mark_install()
                                software = {
                                        "name": pkg.shortname,
                                        "version": version,
                                        "type": "apt",
                                        "url": "",
                                        "action": "install"
                                    }
                                software_installed.append(software)

                        if action == 'delete':
                            if not pkg.is_installed:
                                errors.append(f'Package {name} is not installed!')
                            elif pkg.is_installed and pkg.installed.version != version:
                                errors.append(f'Package {name} with version {version} is not installed. Installed version is {pkg.installed.version}! ')
                            else:
                                self.logger.info('delete ' + pkg.shortname +
                                                '=' + pkg.installed.version)
                                pkg.mark_delete()
                                software = {
                                            "name": pkg.shortname,
                                            "version": pkg.installed.version,
                                            "type": "apt",
                                            "url": "",
                                            "action": "delete"
                                        }
                                software_installed.append(software)
                
                    self.logger.info('Starting apt install/removal of Software..')
                    cache.commit()
                    self.logger.info("Install/Removal of Software finished!")
        except Exception as e:
            self.logger.error(e)
            errors.append(str(e))

        return [errors, software_installed]

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
