import cv2
import time
import numpy as np
import mediapipe as mp
import os
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

os.environ["QT_QPA_PLATFORM"] = "xcb"
# --- Constants and Hardcoded Connections ---
MARGIN = 10  # pixels
FONT_SIZE = 1
FONT_THICKNESS = 1
HANDEDNESS_TEXT_COLOR = (88, 205, 54) # vibrant green
LANDMARK_COLOR = (0, 0, 255) # Red
CONNECTION_COLOR = (255, 255, 255) # White

# Hardcoded tuples representing the connections between the 21 hand landmarks
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),         # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),         # Index finger
    (5, 9), (9, 10), (10, 11), (11, 12),    # Middle finger
    (9, 13), (13, 14), (14, 15), (15, 16),  # Ring finger
    (13, 17), (0, 17), (17, 18), (18, 19), (19, 20) # Pinky and palm base
]

# --- Drawing Logic ---
def draw_landmarks_on_image(rgb_image, detection_result):
    if not detection_result or not detection_result.hand_landmarks:
        return rgb_image

    hand_landmarks_list = detection_result.hand_landmarks
    handedness_list = detection_result.handedness
    annotated_image = np.copy(rgb_image)
    height, width, _ = annotated_image.shape

    # Loop through the detected hands to visualize.
    for idx in range(len(hand_landmarks_list)):
        hand_landmarks = hand_landmarks_list[idx]
        handedness = handedness_list[idx]

        # 1. Convert normalized coordinates to actual pixel coordinates
        pixel_landmarks = []
        for landmark in hand_landmarks:
            px = int(landmark.x * width)
            py = int(landmark.y * height)
            pixel_landmarks.append((px, py))

        # 2. Draw connections (lines between joints) using OpenCV
        for connection in HAND_CONNECTIONS:
            start_idx = connection[0]
            end_idx = connection[1]
            cv2.line(annotated_image, pixel_landmarks[start_idx], pixel_landmarks[end_idx], CONNECTION_COLOR, 2)

        # 3. Draw landmarks (circles at joints) using OpenCV
        for px, py in pixel_landmarks:
            cv2.circle(annotated_image, (px, py), 4, LANDMARK_COLOR, -1)

        # 4. Draw handedness (left or right hand) text
        text_x = min([p[0] for p in pixel_landmarks])
        text_y = min([p[1] for p in pixel_landmarks]) - MARGIN
        
        # Prevent text from going off the top of the screen
        text_y = max(text_y, MARGIN)

        cv2.putText(annotated_image, f"{handedness[0].category_name}",
                    (text_x, text_y), cv2.FONT_HERSHEY_DUPLEX,
                    FONT_SIZE, HANDEDNESS_TEXT_COLOR, FONT_THICKNESS, cv2.LINE_AA)

    return annotated_image

# --- Live Stream Setup ---
BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

# Global variable to pass the result from the callback to the main loop
latest_result = None

# The callback function required by LIVE_STREAM mode
def print_result(result: vision.HandLandmarkerResult, output_image: mp.Image, timestamp_ms: int):
    global latest_result

def main():
    options = HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path='hand_landmarker.task'),
        running_mode=VisionRunningMode.LIVE_STREAM,
        result_callback=print_result,
        num_hands=2)

    with HandLandmarker.create_from_options(options) as landmarker:
        web = cv2.VideoCapture(0)

        while web.isOpened():
            ret, frame = web.read()
            if not ret:
                break
            
            # Flip horizontally for a selfie-view
            frame = cv2.flip(frame, 1)

            # Convert to RGB for MediaPipe
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
            
            # LIVE_STREAM requires a monotonically increasing timestamp in milliseconds
            timestamp_ms = int(time.time() * 1000)
            
            # Run detection asynchronously
            landmarker.detect_async(mp_image, timestamp_ms)

            # Draw the landmarks using the latest result from the callback
            global latest_result
            annotated_image = draw_landmarks_on_image(frame_rgb, latest_result)
            
            # Convert back to BGR for OpenCV display
            annotated_image_bgr = cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR)
            cv2.imshow("webcam", annotated_image_bgr)
            
            # Check for 'q' to quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        web.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()