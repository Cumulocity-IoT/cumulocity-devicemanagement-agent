#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import time
from c8ydm.framework.modulebase import Listener, Initializer
from c8ydm.framework.smartrest import SmartRESTMessage


class CommandHandler(Listener):
    # TODO Extend list with more commands
    availableCommands = ['set', 'get']

    def __init__(self, serial, agent, configuration):
        self.configuration = configuration
        self.agent = agent
        self.serial = serial
        self.commandMap = {
            'set': self.executeSet,
            'get': self.executeGet}

    def handleOperation(self, message):
        try:
            if 's/ds' in message.topic and message.messageId == '511':
                # When multiple operations received just take the first one for further processing
                logging.info('Command Operation received: ' +
                             str(message.values))
                message.values = self.group(message.values, '\n511')[0]
                executing = SmartRESTMessage('s/us', '501', ['c8y_Command'])
                self.agent.publishMessage(executing)
                fullCommand = message.values[1]
                commandParts = fullCommand.split()
                if commandParts[0] not in self.availableCommands:
                    result = SmartRESTMessage('s/us', '502',
                                              ['c8y_Command', "\"Unknown command: '" + commandParts[0] + "'\""])
                else:
                    if len(commandParts) > 1:
                        result = self.commandMap[commandParts[0]](
                            commandParts[1:])
                    else:
                        result = self.commandMap[commandParts[0]]()
                self.agent.publishMessage(result)
        except Exception as e:
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

    def group(self, seq, sep):
        result = [[]]
        for e in seq:
            if sep not in e:
                result[-1].append(e)
            else:
                result[-1].append(e[:e.find(sep)])
                result.append([])

        if result[-1] == []:
            result.pop()  # thx iBug's comment
        return result
