import logging, time, json, time
from c8ydm.framework.modulebase import Listener, Initializer
from c8ydm.framework.smartrest import SmartRESTMessage
import os


class Restart(Listener, Initializer):
    def handleOperation(self, message):
        if 's/ds' in message.topic and message.messageId == '510':
            executing = SmartRESTMessage('s/us', '501', ['c8y_Restart'])
            self.agent.publishMessage(executing)
            try:
                os.system('shutdown -r 1')

            except Exception as e:
                failed = SmartRESTMessage('s/us', '502', ['c8y_Restart', 'Error during Restart:' + str(e)])
                self.agent.publishMessage(failed)

    def getSupportedOperations(self):
        return ['c8y_Restart']

    def getSupportedTemplates(self):
        return []

    def getMessages(self):
        response = None
        if self.agent.simulated:
            response = SmartRESTMessage('s/us', '502', ['c8y_Restart', 'Restart Failed due to simulated Device'])
        else:
            response = SmartRESTMessage('s/us', '503', ['c8y_Restart', 'Restart Successful'])
        return [response]