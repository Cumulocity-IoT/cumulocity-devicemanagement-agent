#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging, time
from c8ydm.framework.modulebase import Listener, Initializer
from c8ydm.framework.smartrest import SmartRESTMessage


class CommandHandler(Listener):
    availableCommands = ['set', 'get', 'revert', 'refresh']

    def __init__(self, serial, agent, configuration):
        self.configuration = configuration
        self.agent = agent
        self.serial = serial
        self.commandMap = {
            'set': self.executeSet,
            'get': self.executeGet,
            'revert': self.executeRevert,
            'refresh': self.executeRefresh
        }

    def handleOperation(self, message):
        try:
            if 's/ds' in message.topic and message.messageId == '511':
                ## When multiple operations received just take the first one for further processing
                logging.info('Command Operation received: ' + str(message.values))
                message.values = self.group(message.values, '\n511')[0]
                if not self.agent.snapdClient.isBusy:
                    self.agent.snapdClient.isBusy = True
                    executing = SmartRESTMessage('s/us', '501', ['c8y_Command'])
                    self.agent.publishMessage(executing)
                    fullCommand = message.values[1]
                    commandParts = fullCommand.split()
                    if commandParts[0] not in self.availableCommands:
                        result = SmartRESTMessage('s/us', '502',
                                                  ['c8y_Command', "\"Unknown command: '" + commandParts[0] + "'\""])
                    else:
                        if len(commandParts) > 1:
                            result = self.commandMap[commandParts[0]](commandParts[1:])
                        else:
                            result = self.commandMap[commandParts[0]]()
                    self.agent.publishMessage(result)
                    if commandParts[0] == 'revert' or commandParts[0] == 'refresh':
                        self.agent.publishMessage(self.getInstalledSoftware())
                    self.agent.snapdClient.isBusy = False
        except Exception as e:
            self.agent.snapdClient.isBusy = False
            logging.exception(e)
            SmartRESTMessage('s/us', '502',
                             ['c8y_Command', 'Error for executung '+message.values[1]])


    def getSupportedOperations(self):
        return ['c8y_Command']

    def getSupportedTemplates(self):
        return []

    def executeSet(self, parts):
        if len(parts) is 3:
            if parts[0] == 'secret':
                return SmartRESTMessage('s/us', '502', ['c8y_Command', "Cannot change 'secret' category"])
            self.configuration.setValue(parts[0], parts[1], parts[2])
            return SmartRESTMessage('s/us', '503',
                                    ['c8y_Command', '[' + parts[0] + '][' + parts[1] + '] = ' + parts[2]])
        else:
            return SmartRESTMessage('s/us', '502', ['c8y_Command', "'set' command expects '<category> <key> <value>'"])

    def executeGet(self, parts):
        if len(parts) is 2:
            if parts[0] == 'secret':
                return SmartRESTMessage('s/us', '502', ['c8y_Command', "Cannot read 'secret' category"])
            result = self.configuration.getValue(parts[0], parts[1])
            if result is None:
                return SmartRESTMessage('s/us', '502', ['c8y_Command', "category/key not found"])
            return SmartRESTMessage('s/us', '503', ['c8y_Command', '[' + parts[0] + '][' + parts[1] + '] = ' + result])
        else:
            return SmartRESTMessage('s/us', '502', ['c8y_Command', "'get' command expects '<category> <key>'"])

    def executeRevert(self, parts):
        try:
            if len(parts) is 1:
                # Without revision
                name = parts[0]
                response = self.agent.snapdClient.revertSnap(name)
                if response['status-code'] >= 400:
                    logging.info('Snap %s error: %s', name, response['result']['message'])
                    return SmartRESTMessage('s/us', '502', ['c8y_Command', 'Command revert failed: '+response['result']['message']])
                elif response['status-code'] == 202:
                    if name == 'pi-kernel':
                        return SmartRESTMessage('s/us', '503',
                                                ['c8y_Command', 'Command revert ' + parts[0] + ' successful'])
                    changeId = response['change']
                    changeStatus = self.getChangeStatus(changeId)
                    while not changeStatus['finished']:
                        time.sleep(3)
                        changeStatus = self.getChangeStatus(changeId)
                    logging.debug('Finished snap ' + name)
                    if changeStatus['error']:
                        return SmartRESTMessage('s/us', '502', ['c8y_Command', 'Command failed:' + changeStatus['error']])
                    else:
                        return SmartRESTMessage('s/us', '503',
                                                ['c8y_Command', 'Command revert' + parts[0] + ' successful'])
            else:
                return SmartRESTMessage('s/us', '502', ['c8y_Command', 'Command revert expects package name'])
        except Exception as e:
            logging.error(e)
            return SmartRESTMessage('s/us', '502', ['c8y_Command', 'Command failed:' + str(e)])

    def executeRefresh(self, parts=None):
        try:
            if parts is not None and len(parts) is 1:
                name = parts[0]
                if name == 'c8ycc':
                    success = SmartRESTMessage('s/us', '503',
                                     ['c8y_Command', 'Command refresh ' + parts[0] + 'successful'])
                    self.agent.publishMessage(success)
                    response = self.agent.snapdClient.updateSnap(name, 'edge', devmode=True, classic=False)
                else:
                    response = self.agent.snapdClient.updateSnap(name)
                if response['status-code'] >= 400:
                    logging.info('Snap %s error: %s', name, response['result']['message'])
                    return SmartRESTMessage('s/us', '502', ['c8y_Command', 'Command refresh failed: '+ response['result']['message']])
                elif response['status-code'] == 202:
                    if name == 'pi-kernel':
                        return SmartRESTMessage('s/us', '503',
                                                ['c8y_Command', 'Command refresh ' + parts[0] + ' successful'])
                    changeId = response['change']
                    changeStatus = self.getChangeStatus(changeId)
                    while not changeStatus['finished']:
                        time.sleep(3)
                        changeStatus = self.getChangeStatus(changeId)
                    logging.debug('Finished snap ' + name)
                    if changeStatus['error']:
                        return SmartRESTMessage('s/us', '502', ['c8y_Command', 'Command refresh failed:' + changeStatus['error']])
                    else:
                        return SmartRESTMessage('s/us', '503',
                                                ['c8y_Command', 'Command refresh ' + parts[0] + 'successful'])

            elif parts is None:
                response = self.agent.snapdClient.updateSnaps()
                if response['status-code'] >= 400:
                    logging.info('Snap error: %s', response['result']['message'])
                    return SmartRESTMessage('s/us', '502', ['c8y_Command', 'Command refresh failed: '+response['result']['message']])
                elif response['status-code'] == 202:
                    changeId = response['change']
                    changeStatus = self.getChangeStatus(changeId)
                    while not changeStatus['finished']:
                        time.sleep(3)
                        changeStatus = self.getChangeStatus(changeId)
                    if changeStatus['error']:
                        return SmartRESTMessage('s/us', '502',
                                                ['c8y_Command', 'Command refresh failed:' + changeStatus['error']])
                    else:
                        return SmartRESTMessage('s/us', '503', ['c8y_Command', 'Command refresh successful'])
            else:
                return SmartRESTMessage('s/us', '502', ['c8y_Command', 'Command refresh invalid'])
        except Exception as e:
            logging.error(e)
            return SmartRESTMessage('s/us', '502', ['c8y_Command', 'Command refresh failed:' + str(e)])

    def getInstalledSoftware(self):
        snapd = self.agent.snapdClient
        installedSnaps = snapd.getInstalledSnaps()
        logging.debug(installedSnaps)
        allInstalled = []

        for snap in installedSnaps['result']:
            snapInfo = []
            # Name
            snapInfo.append(snap['name'])
            # Version
            snapInfo.append(snap['version'] + '##' + snap['channel'])
            # URL
            snapInfo.append('')
            allInstalled.extend(snapInfo)

        return SmartRESTMessage('s/us', '116', allInstalled)

    def getChangeStatus(self, changeId):
        snapd = self.agent.snapdClient
        changeStatus = snapd.getChangeStatus(changeId)
        error = None
        finished = changeStatus['result']['status'] == 'Done'
        if not finished and changeStatus['result']['status'] == 'Error':
            finished = True
            error = changeStatus['result']['err']
        return {
            'finished': finished,
            'error': error
    }

    def group(self, seq, sep):
        result = [[]]
        for e in seq:
            if sep not in e:
                result[-1].append(e)
            else:
                result[-1].append(e[:e.find(sep)])
                result.append([])

        if result[-1] == []:
            result.pop() # thx iBug's comment
        return result