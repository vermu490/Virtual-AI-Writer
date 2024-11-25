from flask import Flask, render_template, Response
import cv2
from cvzone.HandTrackingModule import HandDetector
import numpy as np
import threading
import time

app = Flask(__name__)

# Initialize the webcam feed and set the dimensions
cap = cv2.VideoCapture(0)
cap.set(3, 1280)  # Width of the window
cap.set(4, 720)   # Height of the window

# Initialize the hand detector
detector = HandDetector(detectionCon=0.8, maxHands=1)

# List to store drawing points [(x, y, color, brush_thickness)]
draw_points = []

# Eraser mode toggle
eraser_mode = False

# Scroll variables
scroll_mode = False
scroll_start_y = None

# Color options for drawing
paint_colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0)]  # Red, Green, Blue
color_labels = ["Red", "Green", "Blue"]
current_color = paint_colors[0]  # Initial color: Red
brush_thickness = 10
eraser_thickness = 50  # Eraser thickness

# UI Elements for Color Selection + Brush Size Controls
button_positions = {
    "color_rects": [(50, 50, 150, 150), (200, 50, 300, 150), (350, 50, 450, 150)],  # Color boxes
    "brush_increase_button": (500, 50, 600, 150),  # Increase brush size
    "brush_decrease_button": (650, 50, 750, 150),  # Decrease brush size
    "eraser_button": (800, 50, 950, 150),  # Eraser button
}

# Variables for controlling the state of writing
drawing = False  # Flag to start drawing when the index finger is up

# Lock for thread-safe operations
lock = threading.Lock()

# Variable to store the latest frame
output_frame = None

# Event to stop the thread gracefully
stop_event = threading.Event()

def video_processing():
    global draw_points, eraser_mode, current_color, brush_thickness, scroll_mode, scroll_start_y, output_frame

    while not stop_event.is_set():
        success, img = cap.read()
        if not success:
            break

        # Flip the image horizontally for a mirror view
        img = cv2.flip(img, 1)

        # Detect the hand and get the landmarks
        hands, img = detector.findHands(img)

        # Draw the color selection buttons
        for i, (x1, y1, x2, y2) in enumerate(button_positions["color_rects"]):
            color = paint_colors[i]
            cv2.rectangle(img, (x1, y1), (x2, y2), color, cv2.FILLED)  # Color boxes
            cv2.putText(img, color_labels[i], (x1 + 10, y2 + 40), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3)

        # Draw the brush size control buttons
        cv2.rectangle(img, button_positions["brush_increase_button"][:2], button_positions["brush_increase_button"][2:], (0, 255, 255), cv2.FILLED)  # Yellow box for increasing size
        cv2.putText(img, "+ Size", (button_positions["brush_increase_button"][0] + 10, button_positions["brush_increase_button"][1] + 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 3)

        cv2.rectangle(img, button_positions["brush_decrease_button"][:2], button_positions["brush_decrease_button"][2:], (0, 255, 255), cv2.FILLED)  # Yellow box for decreasing size
        cv2.putText(img, "- Size", (button_positions["brush_decrease_button"][0] + 10, button_positions["brush_decrease_button"][1] + 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 3)

        # Eraser button
        cv2.rectangle(img, button_positions["eraser_button"][:2], button_positions["eraser_button"][2:], (255, 255, 255), cv2.FILLED)
        cv2.putText(img, "Eraser", (button_positions["eraser_button"][0] + 10, button_positions["eraser_button"][1] + 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 3)

        # If a hand is detected
        if hands:
            # Get the first hand detected
            hand = hands[0]

            # Get the landmarks for the detected hand
            lmList = hand["lmList"]

            # Get the index finger tip (Landmark 8 is the index finger tip)
            index_finger_tip = lmList[8][:2]

            # Get the status of all fingers (1: finger up, 0: finger down)
            fingers = detector.fingersUp(hand)

            # Scroll Mode: If fist is detected (all fingers down)
            if fingers == [0, 0, 0, 0, 0]:
                if not scroll_mode:
                    scroll_start_y = index_finger_tip[1]  # Start scrolling
                    scroll_mode = True
            else:
                scroll_mode = False

            # Handle scrolling
            if scroll_mode and scroll_start_y is not None:
                # Calculate how much to scroll
                scroll_delta = index_finger_tip[1] - scroll_start_y

                # Shift all drawing points vertically
                with lock:
                    for i in range(len(draw_points)):
                        if draw_points[i] is not None:
                            point, color, size = draw_points[i]
                            new_point = (point[0], point[1] + int(scroll_delta))  # Shift the y-coordinate by scroll_delta
                            draw_points[i] = (new_point, color, size)

                # Reset scroll_start_y to prevent continuous shifting
                scroll_start_y = index_finger_tip[1]

            # Drawing Mode: If only the index finger is up
            if fingers[1] == 1 and fingers[2] == 0:
                if eraser_mode:
                    # Erase the points under the eraser
                    with lock:
                        for i in range(len(draw_points) - 1, -1, -1):
                            if draw_points[i] is not None:
                                point, color, size = draw_points[i]
                                if point and np.linalg.norm(np.array(index_finger_tip) - np.array(point)) < eraser_thickness:
                                    draw_points.pop(i)  # Remove points within the eraser radius
                else:
                    with lock:
                        draw_points.append((index_finger_tip, current_color, brush_thickness))
                drawing = True
            else:
                with lock:
                    draw_points.append(None)  # Stop drawing if no finger is up
                drawing = False

            # Color Change: If index finger is inside color selection boxes
            for i, (x1, y1, x2, y2) in enumerate(button_positions["color_rects"]):
                if x1 < index_finger_tip[0] < x2 and y1 < index_finger_tip[1] < y2:
                    current_color = paint_colors[i]
                    eraser_mode = False  # Disable eraser when a color is selected

            # Brush Size Increase/Decrease Logic
            if (button_positions["brush_increase_button"][0] < index_finger_tip[0] < button_positions["brush_increase_button"][2] and 
                button_positions["brush_increase_button"][1] < index_finger_tip[1] < button_positions["brush_increase_button"][3]):
                brush_thickness += 2
                time.sleep(0.3)  # Add delay to prevent rapid changes
            if (button_positions["brush_decrease_button"][0] < index_finger_tip[0] < button_positions["brush_decrease_button"][2] and 
                button_positions["brush_decrease_button"][1] < index_finger_tip[1] < button_positions["brush_decrease_button"][3]):
                brush_thickness = max(2, brush_thickness - 2)
                time.sleep(0.3)  # Add delay to prevent rapid changes

            # Toggle Eraser Mode: If the index finger is inside the eraser button
            if (button_positions["eraser_button"][0] < index_finger_tip[0] < button_positions["eraser_button"][2] and 
                button_positions["eraser_button"][1] < index_finger_tip[1] < button_positions["eraser_button"][3]):
                eraser_mode = True
                time.sleep(0.3)  # Add delay to prevent rapid toggling

            # Clear Screen: Using thumbs-down gesture
            # When the thumb is down and all other fingers are up: [0, 1, 1, 1, 1]
            if fingers == [0, 1, 1, 1, 1]:
                with lock:
                    draw_points.clear()  # Clear all drawing points
                time.sleep(0.3)  # Add delay to prevent rapid clearing

        # Drawing points on the screen
        with lock:
            for i in range(1, len(draw_points)):
                if draw_points[i] is not None and draw_points[i - 1] is not None:
                    point1, color1, size1 = draw_points[i - 1]
                    point2, color2, size2 = draw_points[i]
                    cv2.line(img, point1, point2, color1, size1)

        # Show active color and brush size
        cv2.putText(img, "Active Color", (800, 340), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.circle(img, (1050, 250), brush_thickness, current_color, cv2.FILLED)
        cv2.putText(img, f"Brush Size: {brush_thickness}", (1000, 340), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # Encode the frame in JPEG format
        ret, buffer = cv2.imencode('.jpg', img)
        frame = buffer.tobytes()

        # Update the output frame
        with lock:
            output_frame = frame

        # Optional: Add a small delay to reduce CPU usage
        time.sleep(0.02)  # Approximately 50 FPS

def generate_frames():
    global output_frame
    while True:
        with lock:
            if output_frame is None:
                continue
            frame = output_frame
        # Yield the frame in byte format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    # Return the response generated along with the specific media type (mime type)
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

def release_resources():
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    # Start the video processing thread
    t = threading.Thread(target=video_processing)
    t.start()
    try:
        app.run(host='0.0.0.0', port=5000, threaded=False)
    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        t.join()
        release_resources()
