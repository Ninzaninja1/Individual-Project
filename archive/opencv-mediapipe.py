# TODO: update it to compute the direction of the hand in counting fingers
# ----> so it detects fingers up based on palm pos (0) rather than purely just x and y axis 
# ----> make it using distance to knuckle
# TODO: make it show a percentage of openness based on landmark pos

import mediapipe as mp
import numpy as np
import cv2
import os
import time
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

os.environ["QT_QPA_PLATFORM"] = "xcb" # to make Qt use xwayland config (otherwise it crashes)

BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
HandLandmarkerResult = mp.tasks.vision.HandLandmarkerResult
VisionRunningMode = mp.tasks.vision.RunningMode

latest_result = None

def print_result(result: HandLandmarkerResult, output_image: mp.Image, timestamp_ms: int):
    global latest_result # create a global result to use in detection
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
        
        # Draw handedness (left or right hand) on the image.
        cv2.putText(annotated_image, f"{handedness[0].category_name}",
                    (text_x, text_y), cv2.FONT_HERSHEY_DUPLEX,
                    FONT_SIZE, HANDEDNESS_TEXT_COLOR, FONT_THICKNESS, cv2.LINE_AA)
      return annotated_image
  except:
    return rgb_image
  
def count_fingers_raised(rgb_image, detection_result: HandLandmarkerResult):
   """Iterate through each hand, checking if fingers (and thumb) are raised.
   Hand landmark enumeration (and weird naming convention) comes from
   https://developers.google.com/mediapipe/solutions/vision/hand_landmarker."""
   try:
      # Get Data
      hand_landmarks_list = detection_result.hand_landmarks

      # Code to count numbers of fingers raised will go here
      numRaised = [0,0,0,0,0] # index, middle, ring, little, thumb
      # for each hand...
      for idx in range(len(hand_landmarks_list)):
         # hand landmarks is a list of landmarks where each entry in the list has an x, y, and z in normalized image coordinates
         hand_landmarks = hand_landmarks_list[idx]
         # for each fingertip... (hand_landmarks 4, 8, 12, 16 and 20)
         for i in range(8,21,4):
            # make sure finger is higher in image the 3 proceeding values (2 finger segments and knuckle)
            tip_y = hand_landmarks[i].y
            dip_y = hand_landmarks[i-1].y
            pip_y = hand_landmarks[i-2].y
            mcp_y = hand_landmarks[i-3].y

            match i:
              case 8: # index finger
                if tip_y < min(dip_y,pip_y,mcp_y):
                   numRaised[0] += 1
              case 12: # middle finger
                if tip_y < min(dip_y,pip_y,mcp_y):
                   numRaised[1] += 1
              case 16: # ring finger
                if tip_y < min(dip_y,pip_y,mcp_y):
                   numRaised[2] += 1
              case 20: # little finger
                if tip_y < min(dip_y,pip_y,mcp_y):
                   numRaised[3] += 1

         # for the thumb
         # use direction vector from wrist to base of thumb to determine "raised"
         tip_x = hand_landmarks[4].x
         dip_x = hand_landmarks[3].x
         pip_x = hand_landmarks[2].x
         mcp_x = hand_landmarks[1].x
         palm_x = hand_landmarks[0].x
         if mcp_x > palm_x:
            if tip_x > max(dip_x,pip_x,mcp_x):
               numRaised[4] += 1
         else:
            if tip_x < min(dip_x,pip_x,mcp_x):
               numRaised[4] += 1

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
      return annotated_image
   except:
      return rgb_image

def main():

  with HandLandmarker.create_from_options(options) as landmarker:
    web = cv2.VideoCapture(0)
    web.set(cv2.CAP_PROP_FRAME_WIDTH, 600)
    web.set(cv2.CAP_PROP_FRAME_HEIGHT, 500)
    
    while web.isOpened():
      ret,frame = web.read()
  
      frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # mp_image needs to be in this format
      mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb) # make the frame into numpy to allow mediapipe to edit
  
      frame_timestamp_ms = int(time.time() * 1000)
      landmarker.detect_async(mp_image, frame_timestamp_ms) # async-ly compute hand landmark pos

      global latest_result # kinda need it to use it in main

      skeleton_hand_frame = draw_landmarks_on_image(mp_image.numpy_view(), latest_result)
      skeleton_hand_frame_bgr = cv2.cvtColor(skeleton_hand_frame, cv2.COLOR_RGB2BGR) # change back mp_image to normal view

      finger_count_frame = count_fingers_raised(mp_image.numpy_view(), latest_result)
      finger_count_frame_bgr = cv2.cvtColor(finger_count_frame, cv2.COLOR_RGB2BGR) # change back mp_image to normal view

      cv2.imshow("skeleton hand", skeleton_hand_frame_bgr)
      cv2.imshow("finger count", finger_count_frame_bgr)

      # print(HandLandmarkerResult)
      
      # Check for 'q' to quit
      if cv2.waitKey(1) & 0xFF == ord('q'):
        break

  web.release()
  cv2.destroyAllWindows()

# genuienly forgot what this is for
if __name__ == "__main__":
  main() 