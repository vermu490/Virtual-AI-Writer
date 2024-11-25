import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import random
import util
from pynput.mouse import Button, Controller

# Initialize Mediapipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7)
mouse = Controller()

# Get screen dimensions
screen_width, screen_height = pyautogui.size()

# Color palette and shape buttons for drawing
color_palette = [
    (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), 
    (255, 165, 0), (255, 255, 255), (128, 0, 128), (0, 255, 255)
]
shape_buttons = ['Line', 'Rectangle', 'Circle', 'Freestyle', 'Eraser']
current_shape = 'Line'
current_color = color_palette[0]
brush_thickness = 5

# Mode control: True for drawing mode, False for virtual mouse mode
drawing_mode = True

# Initialize variables
drawing = False
prev_x, prev_y = None, None
start_x, start_y = None, None
fingers_up = {}

# Start capturing video
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
h, w, _ = frame.shape
canvas = np.ones((h, w, 3), dtype=np.uint8) * 255  # White canvas

# Gesture Detection Helpers
def find_finger_tip(processed):
    if processed.multi_hand_landmarks:
        hand_landmarks = processed.multi_hand_landmarks[0]  # Assuming only one hand is detected
        index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
        return index_finger_tip
    return None

def move_mouse(index_finger_tip):
    if index_finger_tip is not None:
        x = int(index_finger_tip.x * screen_width)
        y = int(index_finger_tip.y * screen_height)
        pyautogui.moveTo(x, y)

def detect_thumbs_up_down(landmark_list):
    """Detects Thumbs Up and Thumbs Down gestures"""
    thumb_tip = landmark_list[mp_hands.HandLandmark.THUMB_TIP]
    thumb_mcp = landmark_list[mp_hands.HandLandmark.THUMB_CMC]  # Use the CMC joint to compare
    
    if thumb_tip.y < thumb_mcp.y:  # Thumbs Up (thumb tip higher than MCP)
        return "thumbs_up"
    elif thumb_tip.y > thumb_mcp.y:  # Thumbs Down (thumb tip lower than MCP)
        return "thumbs_down"
    return None

# Draw the color palette and shape buttons
def draw_color_palette(frame):
    palette_start_x = w // 2 - (len(color_palette) * 80) // 2
    for i, color in enumerate(color_palette):
        cv2.rectangle(frame, (palette_start_x + i * 80, 20), (palette_start_x + i * 80 + 70, 90), color, -1)
    
    # Display current drawing shape
    cv2.putText(frame, f"Mode: {current_shape}", (w // 2 - 100, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    # Draw shape selection buttons
    button_start_x = w // 2 - (len(shape_buttons) * 120) // 2
    for i, shape in enumerate(shape_buttons):
        cv2.rectangle(frame, (button_start_x + i * 120, h - 80), (button_start_x + i * 120 + 110, h - 30), (200, 200, 200), -1)
        cv2.putText(frame, shape, (button_start_x + i * 120 + 10, h - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

# Gesture Detection Logic
def detect_gesture(frame, landmark_list, processed):
    global drawing_mode
    if len(landmark_list) >= 21:
        index_finger_tip = find_finger_tip(processed)

        # Detect Thumbs Up and Down for mode switching
        thumb_gesture = detect_thumbs_up_down(landmark_list)
        if thumb_gesture == "thumbs_up":
            drawing_mode = True
            cv2.putText(frame, "Drawing Mode", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        elif thumb_gesture == "thumbs_down":
            drawing_mode = False
            cv2.putText(frame, "Virtual Mouse Mode", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        if drawing_mode:
            # Detect drawing gestures when in drawing mode
            if util.get_distance([landmark_list[4], landmark_list[5]]) < 0.1:  # Distance should be a small value since normalized
                move_mouse(index_finger_tip)
        else:
            # Detect virtual mouse actions when in virtual mouse mode
            if util.get_angle(landmark_list[5], landmark_list[6], landmark_list[8]) < 50:
                mouse.press(Button.left)
                mouse.release(Button.left)
                cv2.putText(frame, "Left Click", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            elif util.get_angle(landmark_list[9], landmark_list[10], landmark_list[12]) < 50:
                mouse.press(Button.right)
                mouse.release(Button.right)
                cv2.putText(frame, "Right Click", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

# Main Loop
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    draw_color_palette(frame)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            x, y = int(index_finger_tip.x * w), int(index_finger_tip.y * h)
            
            # Process fingers up state (index and middle fingers)
            fingers_up = {'index': False, 'middle': False}
            if hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y < hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_PIP].y:
                fingers_up['index'] = True
            if hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].y < hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_PIP].y:
                fingers_up['middle'] = True

            if fingers_up['index'] and fingers_up['middle']:
                drawing = False
            elif fingers_up['index'] and not fingers_up['middle']:
                if drawing_mode and not drawing:
                    start_x, start_y = x, y
                    drawing = True
                else:
                    if current_shape == 'Line':
                        canvas = np.ones((h, w, 3), dtype=np.uint8) * 255
                        cv2.line(canvas, (start_x, start_y), (x, y), current_color, brush_thickness)
                    elif current_shape == 'Freestyle':
                        if prev_x is not None and prev_y is not None:
                            cv2.line(canvas, (prev_x, prev_y), (x, y), current_color, brush_thickness)
                        prev_x, prev_y = x, y

            detect_gesture(frame, hand_landmarks.landmark, results)

            # Check color palette selection
            palette_start_x = w // 2 - (len(color_palette) * 80) // 2
            for i, color in enumerate(color_palette):
                if palette_start_x + i * 80 < x < palette_start_x + i * 80 + 70 and 20 < y < 90:
                    current_color = color

            # Check shape buttons selection
            button_start_x = w // 2 - (len(shape_buttons) * 120) // 2
            for i, shape in enumerate(shape_buttons):
                if button_start_x + i * 120 < x < button_start_x + i * 120 + 110 and h - 80 < y < h - 30:
                    current_shape = shape

            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    frame = cv2.addWeighted(frame, 0.5, canvas, 0.5, 0)
    cv2.imshow("Hand Drawing & Gesture Control", frame)

    if results.multi_hand_landmarks is None:
        prev_x, prev_y = None, None
        start_x, start_y = None, None
        drawing = False

    if cv2.waitKey(1) & 0xFF == 27:  # Press 'Esc' to exit
        break

cap.release()
cv2.destroyAllWindows()
