import serial
import serial.tools.list_ports
import time

arduino = serial.Serial(port='/dev/ttyACM1', baudrate=9600)

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

msgWR = input("Message to send: ")
msgWR = str.encode(msgWR)
print(f'Sending... {msgWR}')
arduino.write(msgWR)
time.sleep(0.05)

msgRD = arduino.readline()
print(f'Read MSG from Arduino: {msgRD}\n')



""" arduino ide code
void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
}

void loop() {
  // put your main code here, to run repeatedly:
  if(Serial.available() > 0){

    String message = Serial.readStringUntil('\n');
    Serial.print("Arduino Recieved: ");
    Serial.print(message);
    Serial.print("\n");
  }
}

"""