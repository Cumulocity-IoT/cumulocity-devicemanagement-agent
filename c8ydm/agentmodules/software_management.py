#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging, time, json, time
from c8ydm.framework.modulebase import Listener, Initializer
from c8ydm.framework.smartrest import SmartRESTMessage
import apt


class SoftwareManager(Listener, Initializer):
    logger = logging.getLogger(__name__)

    def group(self, seq, sep):
        result = [[]]
        for e in seq:
            #logging.info("e: "+str(e) +" sep: " + str(sep))
            if sep not in str(e):
                result[-1].append(e)
            else:
                result[-1].append(e[:e.find(sep)])
                result.append([])

        if result[-1] == []:
            result.pop() # thx iBug's comment
        return result

    def handleOperation(self, message):
        try:
            if 's/ds' in message.topic and message.messageId == '528':
                ## When multiple operations received just take the first one for further processing
                #self.logger.debug("message received :" + str(message.values))
                messages = self.group(message.values, '\n')[0]
                deviceId = messages.pop(0)
                self.logger.info('Software update for device ' + deviceId + ' with message ' + str(messages))
                executing = SmartRESTMessage('s/us', '501', ['c8y_SoftwareUpdate'])
                self.agent.publishMessage(executing)
                softwareToInstall = [messages[x:x + 4] for x in range(0, len(messages), 4)]
                errors = self.install_software(softwareToInstall, True)
                self.logger.info('Finished all software update')
                if len(errors) == 0:
                    # finished without errors
                    finished = SmartRESTMessage('s/us', '503', ['c8y_SoftwareUpdate'])
                else:
                    # finished with errors
                    finished = SmartRESTMessage('s/us', '502', ['c8y_SoftwareUpdate', ' - '.join(errors)])
                self.agent.publishMessage(finished)
                self.agent.publishMessage(self.getInstalledSoftware(True))

            if 's/ds' in message.topic and message.messageId == '516':
                ## When multiple operations received just take the first one for further processing
                #self.logger.debug("message received :" + str(message.values))
                messages = self.group(message.values, '\n')[0]
                #self.logger.info("message processed:" + str(messages))
                deviceId = messages.pop(0)
                self.logger.info('Software update for device ' + deviceId + ' with message ' + str(messages))
                executing = SmartRESTMessage('s/us', '501', ['c8y_SoftwareList'])
                self.agent.publishMessage(executing)
                softwareToInstall = [messages[x:x + 3] for x in range(0, len(messages), 3)]
                errors = self.installSoftware(softwareToInstall, True)
                self.logger.info('Finished all software update')
                if len(errors) == 0:
                    # finished without errors
                    finished = SmartRESTMessage('s/us', '503', ['c8y_SoftwareList'])
                else:
                    # finished with errors
                    finished = SmartRESTMessage('s/us', '502', ['c8y_SoftwareList', ' - '.join(errors)])
                self.agent.publishMessage(finished)
                self.agent.publishMessage(self.getInstalledSoftware(True))
        except Exception as e:
          self.logger.exception(e)
          failed = SmartRESTMessage('s/us', '502', ['c8y_SoftwareList', str(e)])
          self.agent.publishMessage(failed)
          failed = SmartRESTMessage('s/us', '502', ['c8y_SoftwareUpdate', str(e)])
          self.agent.publishMessage(failed)


    def getSupportedOperations(self):
        return ['c8y_SoftwareUpdate']


    def getSupportedTemplates(self):
        return []

    def getMessages(self):
        installedSoftware = self.getInstalledSoftware(True)
        return [installedSoftware]

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
            url = software[2]
            action = software[3]
            pkg = cache[name]
            if action == 'install':
                if version == 'latest':
                    self.logger.info('install ' + pkg.shortname + '=latest')
                    pkg.mark_install()
                else:
                    self.logger.info('install ' + pkg.shortname + '=' + version)
                    candidate = pkg.versions.get(version)
                    pkg.candidate = candidate
                    pkg.mark_install()
            # Software currently installed in the same version
            if action == 'update' and pkg.is_installed and pkg.installed.version == version:
                # no action needed
                self.logger.debug('existing ' + pkg.shortname + '=' + pkg.installed.version)
            if action == 'update' and pkg.is_installed and pkg.installed.version != version:
                self.logger.info('install ' + pkg.shortname + '=' + version)
                candidate = pkg.versions.get(version)
                pkg.candidate = candidate
                pkg.mark_install()
            if action == 'delete' and pkg.is_installed:
                self.logger.info('delete ' + pkg.shortname + '=' + pkg.installed.version)
                pkg.mark_delete()
        try:
            self.logger.info('Starting apt install/removal of Software..')
            cache.commit()
            self.logger.info("Install/Removal of Software finished!")
        except Exception as e:
            self.logger.error(e)

        return []

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
                self.logger.debug('existing ' + pkg.shortname + '=' + pkg.installed.version)
            else:
                self.logger.info('install ' + pkg.shortname + '=' + software[1])
                candidate = pkg.versions.get(software[1])
                pkg.candidate = candidate
                pkg.mark_install()

        # Check what needs to be uninstalled
        toBeInstalledSoftware = [i[0] for i in toBeInstalled]
        for pkg in cache:
            if not pkg.shortname.startswith('lib') and pkg.is_installed and pkg.shortname not in toBeInstalledSoftware:
                self.logger.info('delete ' + pkg.shortname + '=' + pkg.installed.version)
                pkg.mark_delete()

        try:
            self.logger.info('Starting apt install/removal of Software..')
            cache.commit()
            self.logger.info("Install/Removal of Software finished!")
        except Exception as e:
            self.logger.error(e)

        return []

