#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

// called this way, it uses the default address 0x40, alternatively Adafruit_PWMServoDriver(0x40)
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

// needs tweaking to find min and max numbers
#define NUM_SERVO 5 // number of servos used
#define SERVOMIN  100 // This is the 'minimum' pulse length count (out of 4096) CALIBRATED
#define SERVOMAX  620 // This is the 'maximum' pulse length count (out of 4096) CALIBRATED
#define USMIN  400 // This is the rounded 'minimum' microsecond length based on the minimum pulse of 100
#define USMAX  2480 // This is the rounded 'maximum' microsecond length based on the maximum pulse of 620
#define SERVO_FREQ 60 // Analog servos run at ~50 Hz updates

int servoPins[NUM_SERVO] = {0, 1, 2, 3, 4};

/*---------------------------------------SETUP-------------------------------------------*/
void setup() {
  Serial.begin(9600);
  Serial.println("5 channel Servo test!");

  pwm.begin();
  pwm.setOscillatorFrequency(27000000);
  pwm.setPWMFreq(SERVO_FREQ);  // Analog servos run at ~50 Hz updates

  // init all servos to their min position during setup
  // for (int i = 0; i < NUM_SERVO; ++i){
  //   pwm.setPWM(servoPins[i], 0, SERVOMIN);
  // }

  delay(10);
}

// You can use this function if you'd like to set the pulse length in seconds
// e.g. setServoPulse(0, 0.001) is a ~1 millisecond pulse width. It's not precise!
void setServoPulse(uint8_t n, double pulse) {
  double pulselength;
  
  pulselength = 1000000;   // 1,000,000 us per second
  pulselength /= SERVO_FREQ;   // Analog servos run at ~60 Hz updates
  Serial.print(pulselength); Serial.println(" us per period"); 
  pulselength /= 4096;  // 12 bits of resolution
  Serial.print(pulselength); Serial.println(" us per bit"); 
  pulse *= 1000000;  // convert input seconds to us
  pulse /= pulselength;
  Serial.println(pulse);
  pwm.setPWM(n, 0, pulse);
}

/*---------------------------------------LOOP-------------------------------------------*/

uint8_t servonum = 0;
uint16_t open = USMIN;
uint16_t close = USMAX;

void loop() {

  if (Serial.available() > 0 ){
    String msg = Serial.readStringUntil('\n');
    msg.trim();

      if(msg == "to"){
        pwm.writeMicroseconds(0, open);
        Serial.println("thumb open: ");
      }
      else if (msg == "io"){
        pwm.writeMicroseconds(1, open);
        Serial.println("index open: ");
      }
      else if (msg == "mo"){
        pwm.writeMicroseconds(2, close);
        Serial.println("middle open: ");
      }
      else if(msg == "ro"){
        pwm.writeMicroseconds(4, open);
        Serial.println("ring open: ");
      }
      else if (msg == "lo"){
        pwm.writeMicroseconds(3, close);
        Serial.println("little open: ");
      }
      else if(msg == "tc"){
        pwm.writeMicroseconds(0, close);
        Serial.println("thumb close: ");
      }
      else if (msg == "ic"){
        pwm.writeMicroseconds(1, close);
        Serial.println("index close: ");
      }
      else if (msg == "mc"){
        pwm.writeMicroseconds(2, open);
        Serial.println("middle close: ");
      }
      else if(msg == "rc"){
        pwm.writeMicroseconds(4, close);
        Serial.println("ring close: ");
      }
      else if (msg == "lc"){
        pwm.writeMicroseconds(3, open);
        Serial.println("little close: ");
      }

      else {
        Serial.println("Invalid Command");
      }
      
    }


  }



  // Drive each servo one at a time using writeMicroseconds(), it's not precise due to calculation rounding!
  // The writeMicroseconds() function is used to mimic the Arduino Servo library writeMicroseconds() behavior. 
  // for (uint16_t microsec = USMIN; microsec < USMAX; microsec++) {
  //   pwm.writeMicroseconds(servonum, microsec);
  // }
  // delay(500);
  // for (uint16_t microsec = USMAX; microsec > USMIN; microsec--) {
  //   pwm.writeMicroseconds(servonum, microsec);
  // }
  // delay(500);
  // servonum++;
  // if (servonum > 4) servonum = 0; // Testing the first 5 servo channels
  // }
