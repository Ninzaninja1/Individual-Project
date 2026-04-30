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
import random
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

arduino = serial.Serial(port='/dev/ttyACM0', baudrate=9600)

class SerialComms:
    def __init__(self):
        pass
    def find_arduino(self,port=None):
        """Get the name of the port that is connected to Arduino."""
        if port is None:
            ports = serial.tools.list_ports.comports()
            for p in ports:
                if p.manufacturer is not None and "Arduino" in p.manufacturer:
                    port = p.device
        print(port)
    def writeMsg(self,msg):
        msg = (msg + '\n').encode()
        print(f"sending: {msg}")
        arduino.write(msg)
    def readMsg(self):
        msgRD = arduino.readline()
        print(f'Arduino Says: {msgRD}\n')

# modified by AI
class RockPaperScissors:
    def __init__(self, serial_controller):
        self.controller = serial_controller
        self.robot_state = [0, 0, 0, 0, 0]  # Assumes hand starts closed (0 = closed, 1 = open)
        
        # Define the finger arrays for each move: [thumb, index, middle, ring, little]
        self.moves_map = {
            'ROCK': [0, 0, 0, 0, 0],
            'PAPER': [1, 1, 1, 1, 1],
            'SCISSORS': [0, 1, 1, 0, 0]
        }

    def pick_random_move(self):
        return random.choice(['ROCK', 'PAPER', 'SCISSORS'])

    def move_robot_hand(self, move):
        if move not in self.moves_map:
            return

        target_state = self.moves_map[move]
        finger_prefixes = ["t", "i", "m", "r", "l"]

        for i in range(5):
            if target_state[i] != self.robot_state[i]:
                state_char = "o" if target_state[i] == 1 else "c"
                command = finger_prefixes[i] + state_char
                self.controller.writeMsg(command)
                self.controller.readMsg()

        self.robot_state = target_state.copy()

    def classify_human_hand(self, num_raised):
        if num_raised == [0, 0, 0, 0, 0]:
            return 'ROCK'
        elif num_raised == [1, 1, 1, 1, 1] or num_raised == [0, 1, 1, 1, 1]:
            return 'PAPER'
        elif num_raised == [0, 1, 1, 0, 0] or num_raised == [1, 1, 1, 0, 0]:
            return 'SCISSORS'
        else:
            return 'NULL'

    def declare_winner(self, human_move, robot_move):
        if human_move == 'NULL':
            print("Human position unclear. Please form a distinct Rock, Paper, or Scissors.")
            return

        print(f"\n--- MATCH ---")
        print(f"Human: {human_move} vs Robot: {robot_move}")

        if human_move == robot_move:
            print("Outcome: TIE")
        elif (human_move == 'ROCK' and robot_move == 'SCISSORS') or \
             (human_move == 'PAPER' and robot_move == 'ROCK') or \
             (human_move == 'SCISSORS' and robot_move == 'PAPER'):
            print("Outcome: HUMAN WINS")
        else:
            print("Outcome: ROBOT WINS")
        print("-------------\n")

controller = SerialComms()
os.environ["QT_QPA_PLATFORM"] = "xcb"  # used to make it work with wayland in linux

BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
HandLandmarkerResult = mp.tasks.vision.HandLandmarkerResult
VisionRunningMode = mp.tasks.vision.RunningMode

latest_result = None

def print_result(result: HandLandmarkerResult, output_image: mp.Image, timestamp_ms: int):
    global latest_result 
    latest_result = result 

base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
options = HandLandmarkerOptions(
    base_options=base_options,
    running_mode=VisionRunningMode.LIVE_STREAM,
    result_callback=print_result,
    num_hands=2)

mp_hands = mp.tasks.vision.HandLandmarksConnections
mp_drawing = mp.tasks.vision.drawing_utils
mp_drawing_styles = mp.tasks.vision.drawing_styles

MARGIN = 10 
FONT_SIZE = 1
FONT_THICKNESS = 1
HANDEDNESS_TEXT_COLOR = (88, 205, 54) 

def draw_landmarks_on_image(rgb_image, detection_result):
  try:
    if detection_result.hand_landmarks == []:
      return rgb_image
    else:
      hand_landmarks_list = detection_result.hand_landmarks
      handedness_list = detection_result.handedness
      annotated_image = np.copy(rgb_image)

      for idx in range(len(hand_landmarks_list)):
        hand_landmarks = hand_landmarks_list[idx]
        handedness = handedness_list[idx]

        mp_drawing.draw_landmarks(
          annotated_image,
          hand_landmarks,
          mp_hands.HAND_CONNECTIONS,
          mp_drawing_styles.get_default_hand_landmarks_style(),
          mp_drawing_styles.get_default_hand_connections_style())

        height, width, _ = annotated_image.shape
        x_coordinates = [landmark.x for landmark in hand_landmarks]
        y_coordinates = [landmark.y for landmark in hand_landmarks]
        text_x = int(min(x_coordinates) * width)
        text_y = int(min(y_coordinates) * height) - MARGIN
        
        cv2.putText(annotated_image, f"{handedness[0].category_name}",
                    (text_x, text_y), cv2.FONT_HERSHEY_DUPLEX,
                    FONT_SIZE, HANDEDNESS_TEXT_COLOR, FONT_THICKNESS, cv2.LINE_AA)
      return annotated_image
  except:
    return rgb_image
  
def count_fingers_raised(rgb_image, detection_result: HandLandmarkerResult):
   if detection_result is None:
      return [0,0,0,0,0]

   hand_landmarks_list = detection_result.hand_landmarks
   numRaised = [0,0,0,0,0] 

   for idx in range(len(hand_landmarks_list)):
      hand_landmarks = hand_landmarks_list[idx]
      for i in range(8,21,4):
         tip_y = hand_landmarks[i].y
         dip_y = hand_landmarks[i-1].y
         pip_y = hand_landmarks[i-2].y
         mcp_y = hand_landmarks[i-3].y

         match i:
           case 8: 
             if tip_y < min(dip_y,pip_y,mcp_y):
                numRaised[1] += 1
           case 12: 
             if tip_y < min(dip_y,pip_y,mcp_y):
                numRaised[2] += 1
           case 16: 
             if tip_y < min(dip_y,pip_y,mcp_y):
                numRaised[3] += 1
           case 20: 
             if tip_y < min(dip_y,pip_y,mcp_y):
                numRaised[4] += 1

      tip_x = hand_landmarks[4].x
      dip_x = hand_landmarks[3].x
      pip_x = hand_landmarks[2].x
      mcp_x = hand_landmarks[1].x
      palm_x = hand_landmarks[0].x
      if mcp_x > palm_x:
         if tip_x > max(dip_x,pip_x,mcp_x):
            numRaised[0] += 1
      else:
         if tip_x < min(dip_x,pip_x,mcp_x):
            numRaised[0] += 1

   return numRaised

def finger_raised_image(rgb_image, numRaised):
   try:
      annotated_image = np.copy(rgb_image)
      height, width, _ = annotated_image.shape
      text_x = int(width) -610
      text_y = int(height) -30
      cv2.putText(img = annotated_image, text = str(numRaised) + " Fingers Raised",
          org = (text_x, text_y), fontFace = cv2.FONT_HERSHEY_DUPLEX,
          fontScale = 1, color = (0,0,255), thickness = 2, lineType = cv2.LINE_4)
      return annotated_image
   except:
      return rgb_image

def main():
  rps = RockPaperScissors(controller) # define object

  with HandLandmarker.create_from_options(options) as landmarker:
    web = cv2.VideoCapture(0)
    web.set(cv2.CAP_PROP_FRAME_WIDTH, 600)
    web.set(cv2.CAP_PROP_FRAME_HEIGHT, 500)

    while web.isOpened():
        ret, frame = web.read()
        if not ret:
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) 
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb) 

        frame_timestamp_ms = int(time.time() * 1000)
        landmarker.detect_async(mp_image, frame_timestamp_ms) 

        global latest_result 

        numRaised = count_fingers_raised(mp_image.numpy_view(), latest_result) 

        skeleton_hand_frame = draw_landmarks_on_image(mp_image.numpy_view(), latest_result)
        finger_count_frame = finger_raised_image(skeleton_hand_frame, numRaised) 
        finger_count_frame_bgr = cv2.cvtColor(finger_count_frame, cv2.COLOR_RGB2BGR) 

        cv2.imshow("finger count", finger_count_frame_bgr)
    
        key = cv2.waitKey(1) & 0xFF
        
        # Check for 'q' to quit
        if key == ord('q'):
          break
        
        # press p to play a round of RPS
        elif key == ord('p'):
            human_move = rps.classify_human_hand(numRaised)
            if human_move != 'NULL':
                robot_move = rps.pick_random_move()
                rps.move_robot_hand(robot_move)
                rps.declare_winner(human_move, robot_move)
            else:
                print("Warning: Please form a distinct Rock, Paper, or Scissors.")

  web.release()
  cv2.destroyAllWindows()

if __name__ == "__main__":
  main()
