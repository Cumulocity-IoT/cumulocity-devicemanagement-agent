from c8ydm.main import stop
import logging
from c8ydm.framework.modulebase import Listener, Sensor, Initializer
from c8ydm.framework.smartrest import SmartRESTMessage
import ShellyPy
import json
import time

class ShellyManagement(Sensor, Initializer, Listener):
    logger = logging.getLogger(__name__)
    xid = 'c8y-dm-agent-v1.0'
    shelly_message_id = 'dm200'
    shelly_command_id = 'dm502'
    fragment = 'shelly_command'

    def handleOperation(self, message):
        if message.messageId == self.shelly_command_id:
            device = ShellyPy.Shelly("192.168.0.200")
            self.logger.info('Received a Shelly Command operation')
            status = device.status()
            mac = status['mac']
            try:
                self._set_executing(mac)
                command = message.values[1]
                if command == 'up':
                    device.roller(0,go="open")
                if command == 'down':
                    device.roller(0,go="close")
                if command == 'stop':
                    device.roller(0,go="stop")
                iterations = 15
                counter = 0
                status = device.status()
                rollers = status['rollers'][0]
                state = rollers['state']
                while counter < iterations or state != 'stop':
                    time.sleep(1)
                    status = device.status()
                    rollers = status['rollers'][0]
                    current_pos = rollers['current_pos']
                    wifi_sta = status['wifi_sta']
                    ip = wifi_sta['ip']
                    state = rollers['state']
                    shelly_msg = SmartRESTMessage('s/uc/'+self.xid, self.shelly_message_id, [mac, state, ip, current_pos])
                    self.agent.publishMessage(shelly_msg)
                    #self.logger.info(f'Publishing shelly updates.. stauts: {status}')
                    counter += 1
                    if state == 'stop':
                        break
                self._set_success(mac)
            except Exception as e:
                self.logger.error(f'The following error occured:{e}')
                self._set_failed(mac, str(e))

    def _set_executing(self, id):
        executing = SmartRESTMessage(f's/us/{id}', '501', [self.fragment])
        self.agent.publishMessage(executing)

    def _set_success(self, id):
        success = SmartRESTMessage(f's/us/{id}', '503', [self.fragment])
        self.agent.publishMessage(success)

    def _set_failed(self, id, reason):
        failed = SmartRESTMessage(f's/us/{id}', '502', [self.fragment, reason])
        self.agent.publishMessage(failed)
    
    def getSensorMessages(self):
        #self.logger.info(f'Sensor Message')
        device = ShellyPy.Shelly("192.168.0.200")
        status = device.status()
        settings = device.settings()
        mac = status['mac']
        rollers = status['rollers'][0]
        temperature = status['temperature']
        voltage = status['voltage']
        temperature_msg = SmartRESTMessage(f's/us/{mac}', '200', ['Temperature', 'T', temperature])
        voltage_msg = SmartRESTMessage(f's/us/{mac}', '200', ['Voltage', 'V', voltage])
        current_pos = rollers['current_pos']
        power = rollers['power']
        state = rollers['state']
        current_pos_msg = SmartRESTMessage(f's/us/{mac}', '200', ['Shutter', 'Position', current_pos])
        power_msg = SmartRESTMessage(f's/us/{mac}', '200', ['Shutter', 'Power', power])
        wifi_sta = status['wifi_sta']
        rssi = wifi_sta['rssi']
        ip = wifi_sta['ip']
        signal_msg = SmartRESTMessage(f's/us/{mac}', '210', [rssi])
        shelly_msg = SmartRESTMessage('s/uc/'+self.xid, self.shelly_message_id, [mac, state, ip, current_pos])
        return [temperature_msg, voltage_msg, current_pos_msg, power_msg, signal_msg, shelly_msg] 
    
    def getMessages(self):
        #self.device.status()
        #TODO Get Shellys from Configuration
        #TODO Instantiate multiple devices
        device = ShellyPy.Shelly("192.168.0.200")
        settings = device.settings()
        status = device.status()
        mac = settings['device']['mac']
        type = settings['device']['type']
        name = settings['name']
        lat = settings['lat']
        lng = settings['lng']
        firmware = settings['fw']
        wifi_sta = status['wifi_sta']
        ip = wifi_sta['ip']
        rssi = wifi_sta['rssi']
        rollers = status['rollers'][0]
        state = rollers['state']
        hostname = settings['device']['hostname']
        self.logger.info(f'Initialize Message')
        self.logger.info(f'Shelly with name {name} and mac {mac}')
        child_device_msg = SmartRESTMessage(f's/us', '101', [mac, hostname, type])
        self.agent.publishMessage(child_device_msg, 2, wait_for_publish=True)
        position_msg = SmartRESTMessage(f's/us/{mac}', '112', [lat, lng])
        settings_msg = SmartRESTMessage(f's/us/{mac}', '113', ['"' + str(settings) + '"'])
       # self.logger.info(f'Settings MSG: {settings_msg.getMessage()}')
        #self.logger.info(f'Conig Msg: {settings_msg}')
        ops_msg = SmartRESTMessage(f's/us/{mac}', '114', ['c8y_Configuration'])
        fw = firmware.split('/')
        
        fw_msg = SmartRESTMessage(f's/us/{mac}', '115', [fw[0], fw[1]])
        req_av = SmartRESTMessage(f's/us/{mac}', '117', [10])
        return [position_msg, settings_msg, ops_msg, fw_msg, req_av]