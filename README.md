# 3rd Year Individual Project - 5-DOF Tendon-Driven Robotic Hand: Vision-Based Teleoperation
This repository contains the software pipeline for a low-cost, 5-Degree of Freedom (DOF) tendon-driven robotic hand. The project provides a non-invasive teleoperation interface using computer vision to map human hand gestures in real-time and translate them into physical robotic actuation. This code was compiled and working on Arch Linux. The two files 'hand_tracking.py' and 'rock_paper_scissors.py' are both used in conjunction with the Arduino Leonardo microcontroller, connected to port '/dev/tty/ACM0'. This is used to control the robot hand created using MG996R motors and 3D printing. An image of the hand in the open and close state is shown below.

The software operates in two primary modes:
- Hand Tracking: Replicates the flexion and extension of the user's fingers in real-time.
- Rock-Paper-Scissors Mode: An automated entertainment system that detects the user's hand shape, categorises it into 'Rock', 'Paper', or 'Scissors', and actuates the robotic hand to play against the user, via the terminal.

## 2. Overview
This software sits between the webcam input and mechanical actuation. The system architecture follows a linear data flow described by the flowchart:

<img scr="https://github.com/Ninzaninja1/Individual-Project/blob/master/src/flowchart.png" alt="drawing" width="400"/>

1. Laptop: A standard webcam captures live video frames of the user's hand and runs the python script and sends a signal to the microcontroller.
2. Arduiono Leonordo: Processes the request sent by the computer and sets pins to be controlled.
3. Motor Drive Board: Manages the power input and powers the microcontroller and outputs the signals sent from the microcontroller.
4. Motors: The motors move between the software limits to extend or contract the fingers in the hand.

## 3. Installation Instructions

To prevent conflicts with other Python projects on your computer, it is highly recommended to install the required libraries inside an isolated Python Virtual Environment. Do not blindly follow these command as they may vary from system to system.

### Specifications:
This project was tested and is working with these parameters::
- Arch Linux (linux 6.19.14 aarch1-1)
- python (version 3.14.3)
- mediapipe (version 0.10.32)
- opencv (version 4.13.0.92)
- pyserial (version 3.5)

### Prerequisites 
Python 3.8+ installed on your system.
Arduino IDE for flashing the microcontroller.

### Setup and Installation
Download the git repository
```bash
git clone https://github.com/Ninzaninja1/Individual-Project.git
```
Set up your virtual python environment  
```bash
   cd path/to/your/repository
   python -m venv .venv
   source .venv/bin/activate
```
Update pip and install dependencies
```bash
   pip install --upgrade pip
   pip install mediapipe==0.10.32 opencv-python pyserial
```

## Usage

1. Hardware Setup: Connect the Arduino Leonardo to your computer via USB. Ensure the PCA9685 board is powered by the external 5V/6A power supply.
2. Flash the Arduino: Open the /servo_code/ folder, load the .ino sketch into the Arduino IDE, and upload it to the Leonardo board.
3. Configure the COM Port: Open the Python script (hand_tracking.py or rock_paper_scissors.py) and update the SERIAL_PORT variable to match the port your Arduino is connected to (e.g., COM3 on Windows or /dev/ttyACM0 on macOS/Linux).
4. Execute the Script: Ensure your virtual environment is activated and you are in the correct directory, then run:
```bash
./hand_tracking-time.py
```
or
```bash
./rock_paper_scissors.py
```
5. Press q on your keyboard while the webcam window is active to quit the program safely.

## Technical Details
Asynchronous Inference: To maintain a high camera framerate (preventing UI stutter), the MediaPipe hand-landmarking task is executed asynchronously (detect_async). The camera loop runs independently of the neural network computation, achieving a software processing latency of ~90ms.
Kinematic Mapping: The robotic fingers are underactuated (1-DOF per finger). The Python script abstracts the complex Denavit-Hartenberg (DH) geometric parameters into a linear string displacement ratio (smin​=0, smax​=50), which is directly mapped to the PWM duty cycle of the servos.
Communication Protocol: Serial communication operates at a baud rate of 9600 for low-latency transmission. The Python script awaits an acknowledgment string from the Arduino before sending the next frame to prevent buffer overflow.

## Known Issues and Future Improvements
Actuation Bottleneck: While the software computes the hand state in ~90ms, the physical time taken by the standard 6V servos takes ~450ms. Future improvements would include upgrading to higher-torque, high-speed servos.
Binary Actuation: The software currently only is able to decipher open and close fingers rather than a range of values for each finger position. Hence, this script is only able to open and close a finger. Alterations are to be able to be made to the script with changes to the code to allow for more precise control in future iterations.
Spool Geometry Constraints: The physical size of the 3D-printed palm limits the radius of the servo winches. Consequently, achieving the full 50mm of string displacement required for maximum theoretical flexion is currently restricted. Future iterations should focus on redesigning the spool mechanism to maximize displacement within the tight palm constraints.

<img src="https://github.com/Ninzaninja1/Individual-Project/blob/master/src/Full_Assembly_closed_real.jpg" alt="drawing" width="400"/>
<img src="https://github.com/Ninzaninja1/Individual-Project/blob/master/src/Full_Assembly_open_real.jpg" alt="drawing" width="400"/>



