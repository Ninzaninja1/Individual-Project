# TODO: expand on the open and close, make it angle specific

import serial
import serial.tools.list_ports
import time

arduino = serial.Serial(port='/dev/ttyACM0', baudrate=9600)

class SerialComms:
    def __init__(self):
        pass
    def find_arduino(self,port=None):
        """Get the name of the port that is connected to Arduino."""
        """https://be189.github.io/lessons/10/control_of_arduino_with_python.html"""
        if port is None:
            ports = serial.tools.list_ports.comports()
            for p in ports:
                if p.manufacturer is not None and "Arduino" in p.manufacturer:
                    port = p.device
        print(port)
    def  writeMsg(self,msg):
        msg = (msg + '\n').encode()
        print(f"sending: {msg}")
        arduino.write(msg)
        time.sleep(0.05)
    def readMsg(self):
        # Verification to check that it did read correctly, just sends it back from arduino
        msgRD = arduino.readline()
        print(f'Arduino Says: {msgRD}\n')
        time.sleep(0.05)

controller = SerialComms()

controller.writeMsg("rc")
controller.readMsg()



