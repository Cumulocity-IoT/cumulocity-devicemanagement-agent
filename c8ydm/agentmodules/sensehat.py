import logging, time
import shlex
from c8ydm.framework.modulebase import Sensor, Initializer, Listener
from c8ydm.framework.smartrest import SmartRESTMessage
try:
    from sense_hat import SenseHat, ACTION_PRESSED
    SENSE = SenseHat()
except Exception as e:
    print('SenseHat not available')
    SENSE = None

class DeviceSensor(Sensor, Initializer, Listener):
    """ SenseHAT Module """
    logger = logging.getLogger(__name__)
    fragment = 'c8y_Message'
    message_id = 'dm502'
    xid = 'c8y-dm-agent-v1.0'

    def _set_executing(self):
        executing = SmartRESTMessage('s/us', '501', [self.fragment])
        self.agent.publishMessage(executing)

    def _set_success(self):
        success = SmartRESTMessage('s/us', '503', [self.fragment])
        self.agent.publishMessage(success)

    def _set_failed(self, reason):
        failed = SmartRESTMessage('s/us', '502', [self.fragment, reason])
        self.agent.publishMessage(failed)

    def handleOperation(self, message):
        """Callback that is executed for any operation received

            Raises:
            Exception: Error when handling the operation
       """
        try:
            #self.logger.debug(
            #    f'Handling Cloud Remote Access operation: listener={__name__}, message={message}')

            if message.messageId == self.message_id:
                self._set_executing()
                message = message.values[1]
                self.display_message(message)
                self._set_success()
    
        except Exception as ex:
            self.logger.error(f'Handling operation error. exception={ex}')
            self._set_failed(str(ex))
            # raise


    def getSensorMessages(self):
        try:
            return self.send_stats()
        except Exception as e:
            self.logger.exception(f'Error in SenseHAT getSensorMessages: {e}', e)

    def getMessages(self):
        try:
            self.listenForJoystick()
            return self.send_stats()
        except Exception as e:
            self.logger.exception(f'Error in SenseHAT getMessages: {e}', e)
    
    def send_stats(self):
        if SENSE:
            self.stats = []
            self.stats.append(SmartRESTMessage('s/us', '200', ['SenseHat', 'Temperature', SENSE.get_temperature()]))
            self.stats.append(SmartRESTMessage('s/us', '200', ['SenseHat', 'Humidity', SENSE.get_humidity()]))
            self.stats.append(SmartRESTMessage('s/us', '200', ['SenseHat', 'Pressure', SENSE.get_pressure()]))
            acceleration = SENSE.get_accelerometer_raw()
            acc_x = acceleration['x']
            acc_y = acceleration['y']
            acc_z = acceleration['z']
            self.stats.append(SmartRESTMessage('s/us', '200', ['SenseHat', 'Acceleration.xValue', acc_x]))
            self.stats.append(SmartRESTMessage('s/us', '200', ['SenseHat', 'Acceleration.yValue', acc_y]))
            self.stats.append(SmartRESTMessage('s/us', '200', ['SenseHat', 'Acceleration.zValue', acc_z]))
            gyroscope = SENSE.gyro_raw
            gyro_x = gyroscope["x"]
            gyro_y = gyroscope["y"]
            gyro_z = gyroscope["z"]
            self.stats.append(SmartRESTMessage('s/us', '200', ['SenseHat', 'Gyroscope.xValue', gyro_x]))
            self.stats.append(SmartRESTMessage('s/us', '200', ['SenseHat', 'Gyroscope.yValue', gyro_y]))
            self.stats.append(SmartRESTMessage('s/us', '200', ['SenseHat', 'Gyroscope.zValue', gyro_z]))
            compass = SENSE.compass_raw
            compass_x = compass["x"]
            compass_y = compass["y"]
            compass_z = compass["z"]
            self.stats.append(SmartRESTMessage('s/us', '200', ['SenseHat', 'Compass.xValue', compass_x]))
            self.stats.append(SmartRESTMessage('s/us', '200', ['SenseHat', 'Compass.yValue', compass_y]))
            self.stats.append(SmartRESTMessage('s/us', '200', ['SenseHat', 'Compass.zValue', compass_z]))
            return self.stats
        else:
            return []
    

    def display_message(self,message):
        if SENSE:
            messageArray =  shlex.shlex(message, posix=True)
            messageArray.whitespace =',' 
            messageArray.whitespace_split =True 
            msg = str(list(messageArray)[-1])
            self.logger.info(f'Display message: {msg}')
            SENSE.show_message(msg)
            SENSE.clear
    
    def joystick_up(self, event):
        if event.action == ACTION_PRESSED:
            msg = SmartRESTMessage('s/us', '400', ['c8y_SenseHATJoystickUpEvent', 'Joystick Up Event!'])
            self.agent.publishMessage(msg)
    
    def joystick_down(self, event):
        if event.action == ACTION_PRESSED:
            msg = SmartRESTMessage('s/us', '400', ['c8y_SenseHATJoystickDownEvent', 'Joystick Down Event!'])
            self.agent.publishMessage(msg)

    def joystick_left(self, event):
        if event.action == ACTION_PRESSED:
            msg = SmartRESTMessage('s/us', '400', ['c8y_SenseHATJoystickLeftEvent', 'Joystick Left Event!'])
            self.agent.publishMessage(msg)

    def joystick_right(self, event):
        if event.action == ACTION_PRESSED:
            msg = SmartRESTMessage('s/us', '400', ['c8y_SenseHATJoystickRightEvent', 'Joystick Right Event!'])
            self.agent.publishMessage(msg)

    def joystick_middle(self, event):
        if event.action == ACTION_PRESSED:
            msg = SmartRESTMessage('s/us', '400', ['c8y_SenseHATJoystickMiddleEvent', 'Joystick Middle Event!'])
            self.agent.publishMessage(msg)

    def listenForJoystick(self):
        if SENSE:
            SENSE.stick.direction_up = self.joystick_up
            SENSE.stick.direction_down = self.joystick_down
            SENSE.stick.direction_left = self.joystick_left
            SENSE.stick.direction_right = self.joystick_right
            SENSE.stick.direction_middle = self.joystick_middle
    
    def getSupportedOperations(self):
        return [self.fragment]
    
    def getSupportedTemplates(self):
        return [self.xid]