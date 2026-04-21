# with the help of https://medium.com/@oetalmage16/a-tutorial-on-finger-counting-in-real-time-video-in-python-with-opencv-and-mediapipe-114a988df46a

import cv2
import mediapipe as mp
import os
import time
import numpy as np

os.environ["QT_QPA_PLATFORM"] = "xcb"

class landmarker_and_result():
   def __init__(self):
      self.result = mp.tasks.vision.HandLandmarkerResult
      self.landmarker = mp.tasks.vision.HandLandmarker
      self.createLandmarker()
   
   def createLandmarker(self):
      # callback function
      def update_result(result: mp.tasks.vision.HandLandmarkerResult, output_image: mp.Image, timestamp_ms: int):
         self.result = result

      options = mp.tasks.vision.HandLandmarkerOptions( 
         base_options = mp.tasks.BaseOptions(model_asset_path="./hand_landmarker.task"), # path to model
         running_mode = mp.tasks.vision.RunningMode.LIVE_STREAM, # running on a live stream
         num_hands = 2, # track both hands
         min_hand_detection_confidence = 0.3, # lower than value to get predictions more often
         min_hand_presence_confidence = 0.3, # lower than value to get predictions more often
         min_tracking_confidence = 0.3, # lower than value to get predictions more often
         result_callback=update_result)
      
      # initialize landmarker
      self.landmarker = self.landmarker.create_from_options(options)
   
   def detect_async(self, frame):
      # convert np frame to mp image
      mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
      # detect landmarks
      self.landmarker.detect_async(image = mp_image, timestamp_ms = int(time.time() * 1000))

   def close(self):
      # close landmarker
      self.landmarker.close()


def main():
    # access webcam
    cap = cv2.VideoCapture(0)
   
    while True:
        # pull frame
        ret, frame = cap.read()
        # mirror frame
        frame = cv2.flip(frame, 1)
        hand_landmarker = landmarker_and_result()
        hand_landmarker.detect_async(frame)
        print(hand_landmarker.result)

        # display frame
        cv2.imshow('frame',frame)

        if cv2.waitKey(1) == ord('q'):
            hand_landmarker.close()
            break

    # release everything
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
   main()
