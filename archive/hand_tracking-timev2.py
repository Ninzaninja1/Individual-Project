# TODO: update it to compute the direction of the hand in counting fingers
# ----> so it detects fingers up based on palm pos (0) rather than purely just x and y axis 
# ----> make it using distance to knuckle
# TODO: make it show a percentage of openness based on landmark pos
# TODO: expand on the open and close, make it angle specific

import serial
import mediapipe as mp
import serial.tools.list_ports
import time
import numpy as np
import cv2
import os
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Dictionary to store our latency measurements for the report
timing_stats = {
    'pre_image_processing': [],
    'async_callback': [],
    'serial_comm': [],
    'total_loop': []
}

class SerialComms:
    def __init__(self, serial_port='/dev/ttyACM0', baud_rate=9600):
        # Setup serial connection to Arduino
        try:
            self.arduino = serial.Serial(serial_port, baud_rate, timeout=1)
            time.sleep(2) # Give the Arduino time to reset after connection
            print("Successfully connected to the robotic hand.")
        except serial.SerialException:
            print("Warning: Arduino not detected.")
            self.arduino = None
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
        if self.arduino is None: return # Safety check if Arduino isn't plugged in
        msg = (msg + '\n').encode()
        # print(f"sending: {msg}")
        self.arduino.write(msg)
    def readMsg(self):
        if self.arduino is None: return "" # Safety check if Arduino isn't plugged in
        # Verification to check that it did read correctly, just sends it back from arduino
        msgRD = self.arduino.readline()
        # print(f'Arduino Says: {msgRD}\n')
        return msgRD

controller = SerialComms()

os.environ["QT_QPA_PLATFORM"] = "xcb" # to make Qt use xwayland config (otherwise it crashes)

BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
HandLandmarkerResult = mp.tasks.vision.HandLandmarkerResult
VisionRunningMode = mp.tasks.vision.RunningMode

latest_result = None

def print_result(result: HandLandmarkerResult, output_image: mp.Image, timestamp_ms: int):
    global latest_result # create a global result to use in detection
    global timing_stats
    
    # Calculate MediaPipe 'detect_async' callback delay
    callback_time_ms = int(time.time() * 1000)
    async_delay = callback_time_ms - timestamp_ms
    timing_stats['async_callback'].append(async_delay)
    
    latest_result = result # to update and use the latest result 
    # print('hand landmarker result: {}'.format(result))

base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
options = HandLandmarkerOptions(
    base_options=base_options,
    running_mode=VisionRunningMode.LIVE_STREAM,
    result_callback=print_result,
    num_hands=2)

# Google's implementation of some functions to visualize the hand landmark detection results. 

mp_hands = mp.tasks.vision.HandLandmarksConnections
mp_drawing = mp.tasks.vision.drawing_utils
mp_drawing_styles = mp.tasks.vision.drawing_styles

MARGIN = 10  # pixels
FONT_SIZE = 1
FONT_THICKNESS = 1
HANDEDNESS_TEXT_COLOR = (88, 205, 54) # vibrant green

def draw_landmarks_on_image(rgb_image, detection_result):
  try:
    if detection_result.hand_landmarks == []:
      return rgb_image
    else:
      hand_landmarks_list = detection_result.hand_landmarks
      handedness_list = detection_result.handedness
      annotated_image = np.copy(rgb_image)

      # Loop through the detected hands to visualize.
      for idx in range(len(hand_landmarks_list)):
        hand_landmarks = hand_landmarks_list[idx]
        handedness = handedness_list[idx]

        # Draw the hand landmarks.
        mp_drawing.draw_landmarks(
          annotated_image,
          hand_landmarks,
          mp_hands.HAND_CONNECTIONS,
          mp_drawing_styles.get_default_hand_landmarks_style(),
          mp_drawing_styles.get_default_hand_connections_style())

        # Get the top left corner of the detected hand's bounding box.
        height, width, _ = annotated_image.shape
        x_coordinates = [landmark.x for landmark in hand_landmarks]
        y_coordinates = [landmark.y for landmark in hand_landmarks]
        text_x = int(min(x_coordinates) * width)
        text_y = int(min(y_coordinates) * height) - MARGIN
        
        # EXTRACT CONFIDENCE SCORE: 
        # Get the score from the handedness object and format it as a percentage
        confidence_score = handedness[0].score
        display_text = f"{handedness[0].category_name} ({confidence_score:.1%})"
        
        # Draw handedness (left or right hand) and confidence on the image.
        cv2.putText(annotated_image, display_text,
                    (text_x, text_y), cv2.FONT_HERSHEY_DUPLEX,
                    FONT_SIZE, HANDEDNESS_TEXT_COLOR, FONT_THICKNESS, cv2.LINE_AA)
      return annotated_image
  except:
    return rgb_image

def count_fingers_raised(rgb_image, detection_result: HandLandmarkerResult):
   """Iterate through each hand, checking if fingers (and thumb) are raised.
   Hand landmark enumeration (and weird naming convention) comes from
   https://developers.google.com/mediapipe/solutions/vision/hand_landmarker."""

   if detection_result is None or not hasattr(detection_result, 'hand_landmarks') or not detection_result.hand_landmarks:
      return [0,0,0,0,0]

   # Get Data
   hand_landmarks_list = detection_result.hand_landmarks

   # Code to count numbers of fingers raised will go here
   numRaised = [0,0,0,0,0] # thumb, index, middle, ring, little
   # for each hand...
   for idx in range(len(hand_landmarks_list)):
      hand_landmarks = hand_landmarks_list[idx]
      
      # 1. Compute Hand Orientation Vectors
      wrist_x, wrist_y = hand_landmarks[0].x, hand_landmarks[0].y
      mcp9_x, mcp9_y = hand_landmarks[9].x, hand_landmarks[9].y
      
      # 'Up' vector (from wrist to middle knuckle)
      up_x = mcp9_x - wrist_x
      up_y = mcp9_y - wrist_y
      
      # 'Right' vector (perpendicular to up vector)
      right_x = -up_y
      right_y = up_x
      
      # 2. Helper functions to map landmarks to the hand's local coordinate space
      def get_local_y(lm):
          # Projects a landmark onto the hand's local 'up' axis
          return (lm.x - wrist_x) * up_x + (lm.y - wrist_y) * up_y
          
      def get_local_x(lm):
          # Projects a landmark onto the hand's local 'right/left' axis
          return (lm.x - wrist_x) * right_x + (lm.y - wrist_y) * right_y

      # for each fingertip... (hand_landmarks 8, 12, 16 and 20)
      for i in range(8,21,4):
         # check if finger is extended along the local Y (up) axis
         tip_y = get_local_y(hand_landmarks[i])
         dip_y = get_local_y(hand_landmarks[i-1])
         pip_y = get_local_y(hand_landmarks[i-2])
         mcp_y = get_local_y(hand_landmarks[i-3])

         # Because the local Y vector points towards the fingers, a higher value means further extended
         is_raised = tip_y > max(dip_y, pip_y, mcp_y)

         match i:
           case 8: # index finger
             if is_raised: numRaised[1] += 1
           case 12: # middle finger
             if is_raised: numRaised[2] += 1
           case 16: # ring finger
             if is_raised: numRaised[3] += 1
           case 20: # little finger
             if is_raised: numRaised[4] += 1

      # for the thumb
      # keep the exact same logic structure, but evaluate it on the hand-oriented local X axis
      tip_x = get_local_x(hand_landmarks[4])
      dip_x = get_local_x(hand_landmarks[3])
      pip_x = get_local_x(hand_landmarks[2])
      mcp_x = get_local_x(hand_landmarks[1])
      palm_x = 0 # wrist is the origin (0) of our local axes
      
      if mcp_x > palm_x:
         if tip_x > max(dip_x, pip_x, mcp_x):
            numRaised[0] += 1
      else:
         if tip_x < min(dip_x, pip_x, mcp_x):
            numRaised[0] += 1

   return numRaised

def finger_raised_image(rgb_image, numRaised):

   try:
      # Code to display the number of fingers raised will go here
      annotated_image = np.copy(rgb_image)
      height, width, _ = annotated_image.shape
      # place text near wrist
      # text_x = int(hand_landmarks[0].x * width) - 100
      # text_y = int(hand_landmarks[0].y * height) + 50
      # place text it bottom left corner
      text_x = int(width) -610
      text_y = int(height) -30
      cv2.putText(img = annotated_image, text = str(numRaised) + " Fingers Raised",
          org = (text_x, text_y), fontFace = cv2.FONT_HERSHEY_DUPLEX,
          fontScale = 1, color = (0,0,255), thickness = 2, lineType = cv2.LINE_4)
      
      ## Code to move the motors on the arduino

      return annotated_image
   except:
      return rgb_image
   

def arduinoMotors(currFingerState, numRaised):
      finger_prefixes = ["t", "i", "m", "r", "l"]
      global timing_stats

      for i in range(5):
         if numRaised[i] != currFingerState[i]:
            command = finger_prefixes[i] + ("o" if numRaised[i] == 1 else "c")
            
            # Measure Serial Communication latency
            start_serial = time.time()
            controller.writeMsg(command)
            controller.readMsg()
            end_serial = time.time()
            
            timing_stats['serial_comm'].append((end_serial - start_serial) * 1000)

def main():
  global timing_stats
  frame_count = 0

  with HandLandmarker.create_from_options(options) as landmarker:
    web = cv2.VideoCapture(0)
    web.set(cv2.CAP_PROP_FRAME_WIDTH, 600)
    web.set(cv2.CAP_PROP_FRAME_HEIGHT, 500)
    currFingerState = [0, 0, 0, 0, 0]

    while web.isOpened():
        loop_start = time.time()

        # --- Measure Pre-Image Processing ---
        pre_img_start = time.time()

        ret,frame = web.read()
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # mp_image needs to be in this format
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb) # make the frame into numpy to allow mediapipe to edit

        pre_img_end = time.time()
        timing_stats['pre_image_processing'].append((pre_img_end - pre_img_start) * 1000)

        frame_timestamp_ms = int(time.time() * 1000)
        landmarker.detect_async(mp_image, frame_timestamp_ms) # async-ly compute hand landmark pos

        global latest_result # kinda need it to use it in main

        numRaised = count_fingers_raised(mp_image.numpy_view(), latest_result) # calculate the No of fingers raised with the reference frame

        skeleton_hand_frame = draw_landmarks_on_image(mp_image.numpy_view(), latest_result)
        # skeleton_hand_frame_bgr = cv2.cvtColor(skeleton_hand_frame, cv2.COLOR_RGB2BGR) # change back mp_image to normal view
        finger_count_frame = finger_raised_image(skeleton_hand_frame, numRaised) # convert this to an annotated image to output
        finger_count_frame_bgr = cv2.cvtColor(finger_count_frame, cv2.COLOR_RGB2BGR) # change back mp_image to normal view

        # Uncommented this so the Serial Comm latency is actively measured
        arduinoMotors(currFingerState, numRaised)
        currFingerState = numRaised.copy() # needs to go after 

        # cv2.imshow("skeleton hand", skeleton_hand_frame_bgr)
        cv2.imshow("finger count", finger_count_frame_bgr)

        # --- Measure Total System Latency (Software side) ---
        loop_end = time.time()
        timing_stats['total_loop'].append((loop_end - loop_start) * 1000)

        frame_count += 1
        
        # Print averages to the console every 30 frames for easy recording
        if frame_count % 30 == 0:
            print("\n--- Latency Measurements (30-frame rolling average) ---")
            if timing_stats['pre_image_processing']:
                avg_pre = sum(timing_stats['pre_image_processing'][-30:]) / min(30, len(timing_stats['pre_image_processing']))
                print(f"Pre-Image Processing: {avg_pre:.2f} ms")
            if timing_stats['async_callback']:
                avg_async = sum(timing_stats['async_callback'][-30:]) / min(30, len(timing_stats['async_callback']))
                print(f"Async Frame Analysis: {avg_async:.2f} ms")
            if timing_stats['serial_comm']:
                avg_serial = sum(timing_stats['serial_comm'][-30:]) / min(30, len(timing_stats['serial_comm']))
                print(f"Communication Serial: {avg_serial:.2f} ms")
            if timing_stats['total_loop']:
                avg_loop = sum(timing_stats['total_loop'][-30:]) / min(30, len(timing_stats['total_loop']))
                print(f"Total Software Latency: {avg_loop:.2f} ms")
            print("-------------------------------------------------------")

        # Check for 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
          break

  web.release()
  cv2.destroyAllWindows()

# genuienly forgot what this is for
if __name__ == "__main__":
  main()