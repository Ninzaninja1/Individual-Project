# TODO: expand on the open and close, make it angle specific

import serial
import serial.tools.list_ports
import time


arduino = serial.Serial(port='/dev/ttyACM0', baudrate=9600)

def find_arduino(port=None):
    """Get the name of the port that is connected to Arduino."""
    """https://be189.github.io/lessons/10/control_of_arduino_with_python.html"""
    if port is None:
        ports = serial.tools.list_ports.comports()
        for p in ports:
            if p.manufacturer is not None and "Arduino" in p.manufacturer:
                port = p.device
    return port
port = find_arduino()
print(port)

# Message encoding pattern?
# thumb(t), index(i), middle(m), ring(r), little(l) 
# followed by
# open(O), closed(C)
while True:
    msgWR = input("Message to send: ")
    # msgWR = str.encode(msgWR)
    msgWR = (msgWR + '\n').encode()
    print(f'Sending: {msgWR}')
    arduino.write(msgWR)
    time.sleep(0.05)

    # Verification to check that it did read correctly, just sends it back from arduino
    msgRD = arduino.readline()
    print(f'Arduino Says: {msgRD}\n')


