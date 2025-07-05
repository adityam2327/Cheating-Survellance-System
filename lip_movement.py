import cv2
import dlib
import numpy as np
from collections import deque
import time
import os

# Load face detector & landmarks predictor
try:
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor("model/shape_predictor_68_face_landmarks.dat")
except Exception as e:
    print(f"Error loading dlib models for lip detection: {e}")
    detector = None
    predictor = None

# Lip landmarks indices (based on the 68-point facial landmark model)
UPPER_LIP_INDICES = [50, 51, 52, 53, 54]  # Upper lip outer contour
LOWER_LIP_INDICES = [56, 57, 58, 59, 60]  # Lower lip outer contour

# Parameters for lip movement detection
LIP_MOVEMENT_THRESHOLD = 0.05  # Lowered from 0.2 to 0.05 for more sensitive detection
WHISPERING_THRESHOLD = 0.3     # Lowered from 0.5 to 0.3 for better whispering detection
HISTORY_SIZE = 5               # Reduced from 10 to 5 for faster response

# Smoothing filter for stable lip movement detection
lip_distance_history = deque(maxlen=HISTORY_SIZE)
lip_movement_history = deque(maxlen=HISTORY_SIZE)

# State variables
previous_lip_state = "No Movement"
lip_movement_start_time = None

def calculate_lip_distance(landmarks):
    """Calculate the average distance between upper and lower lip"""
    try:
        upper_lip_points = np.array([(landmarks.part(i).x, landmarks.part(i).y) for i in UPPER_LIP_INDICES])
        lower_lip_points = np.array([(landmarks.part(i).x, landmarks.part(i).y) for i in LOWER_LIP_INDICES])
        
        # Calculate distances between corresponding points
        distances = np.sqrt(np.sum((upper_lip_points - lower_lip_points)**2, axis=1))
        return np.mean(distances)
    except Exception as e:
        print(f"Error calculating lip distance: {e}")
        return 0.0

def calculate_lip_movement(current_distance, prev_distance):
    """Calculate the amount of lip movement between frames"""
    try:
        if prev_distance == 0:
            return 0
        return abs(current_distance - prev_distance) / prev_distance
    except Exception as e:
        print(f"Error calculating lip movement: {e}")
        return 0.0

def smooth_value(history, new_value):
    """Apply smoothing to a value using a history queue"""
    try:
        history.append(new_value)
        return np.mean(history)
    except Exception as e:
        print(f"Error smoothing value: {e}")
        return new_value

def process_lip_movement(frame, audio_level=0.0):
    """
    Process the frame to detect lip movements and whispering
    
    Parameters:
    frame (numpy.ndarray): The input video frame
    audio_level (float): Optional audio level from voice detection (0-1 range)
    
    Returns:
    tuple: (processed_frame, lip_state, is_whispering)
    """
    global previous_lip_state, lip_movement_start_time
    
    print(f"[DEBUG] process_lip_movement called with audio_level: {audio_level}")
    
    try:
        if detector is None or predictor is None:
            print("[DEBUG] Models not loaded, returning 'Models not loaded'")
            return frame, "Models not loaded", False
            
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = detector(gray)
        print(f"[DEBUG] Found {len(faces)} faces")
        
        # Default states
        lip_state = "No Movement"
        is_whispering = False
        
        # If no face is detected, return the original frame
        if len(faces) == 0:
            print("[DEBUG] No faces detected, returning 'No Movement'")
            return frame, lip_state, is_whispering
        
        # Process the first detected face
        face = faces[0]
        landmarks = predictor(gray, face)
        
        # Calculate current lip distance
        current_lip_distance = calculate_lip_distance(landmarks)
        print(f"[DEBUG] Current lip distance: {current_lip_distance}")
        
        # Get the previous distance from history (or use current if history is empty)
        prev_lip_distance = lip_distance_history[-1] if lip_distance_history else current_lip_distance
        
        # Calculate lip movement (change in distance)
        lip_movement = calculate_lip_movement(current_lip_distance, prev_lip_distance)
        print(f"[DEBUG] Lip movement: {lip_movement}")
        
        # Apply smoothing
        smoothed_lip_distance = smooth_value(lip_distance_history, current_lip_distance)
        smoothed_lip_movement = smooth_value(lip_movement_history, lip_movement)
        print(f"[DEBUG] Smoothed lip movement: {smoothed_lip_movement}")
        
        # Determine lip state based on movement
        if smoothed_lip_movement > LIP_MOVEMENT_THRESHOLD:
            # If there's significant lip movement
            if audio_level < WHISPERING_THRESHOLD and smoothed_lip_movement < WHISPERING_THRESHOLD * 1.5:
                # Low audio but visible lip movement indicates whispering
                lip_state = "Whispering"
                is_whispering = True
            else:
                # Higher movement or audio indicates normal speech
                lip_state = "Speaking"
        elif smoothed_lip_movement > LIP_MOVEMENT_THRESHOLD * 0.5:  # Even more sensitive threshold
            # Very small movements - could be whispering or subtle speech
            lip_state = "Subtle Movement"
            if audio_level < WHISPERING_THRESHOLD:
                is_whispering = True
        else:
            lip_state = "No Movement"
        
        print(f"[DEBUG] Lip state determined: {lip_state}, is_whispering: {is_whispering}")
        
        # Draw lip landmarks and status on the frame
        try:
            for i in UPPER_LIP_INDICES + LOWER_LIP_INDICES:
                pt = (landmarks.part(i).x, landmarks.part(i).y)
                cv2.circle(frame, pt, 1, (0, 255, 255), -1)
        except Exception as e:
            print(f"[DEBUG] Error drawing lip landmarks: {e}")
        
        # Draw lip distance value
        cv2.putText(frame, f"Lip Movement: {smoothed_lip_movement:.3f}", 
                    (10, frame.shape[0] - 70), cv2.FONT_HERSHEY_SIMPLEX, 
                    0.5, (0, 255, 255), 1)
        
        # Draw threshold information for debugging
        cv2.putText(frame, f"Threshold: {LIP_MOVEMENT_THRESHOLD:.3f}", 
                    (10, frame.shape[0] - 50), cv2.FONT_HERSHEY_SIMPLEX, 
                    0.4, (255, 255, 0), 1)
        
        # Draw lip state
        color = (0, 255, 255)  # Yellow for no movement
        if lip_state == "Whispering":
            color = (0, 0, 255)  # Red for whispering
        elif lip_state == "Speaking":
            color = (0, 255, 0)  # Green for speaking
        elif lip_state == "Subtle Movement":
            color = (255, 165, 0)  # Orange for subtle movement
        
        cv2.putText(frame, f"Lip State: {lip_state}", 
                    (10, frame.shape[0] - 30), cv2.FONT_HERSHEY_SIMPLEX, 
                    0.5, color, 1)
        
        # Update previous state
        previous_lip_state = lip_state
        
        return frame, lip_state, is_whispering
        
    except Exception as e:
        print(f"[DEBUG] Error in lip movement detection: {e}")
        return frame, "Detection error", False

def save_lip_movement_screenshot(frame, lip_state, log_dir="log"):
    """Save a screenshot when lip movement is detected"""
    try:
        filename = os.path.join(log_dir, f"lip_{lip_state}_{int(time.time())}.png")
        cv2.imwrite(filename, frame)
        print(f"Lip movement screenshot saved: {filename}")
        return filename
    except Exception as e:
        print(f"Error saving lip movement screenshot: {e}")
        return None
