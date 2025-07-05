import cv2
import dlib
import numpy as np

# Load dlib's face detector and 68 landmarks model
try:
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor("model/shape_predictor_68_face_landmarks.dat")
except Exception as e:
    print(f"Error loading dlib models: {e}")
    detector = None
    predictor = None

def detect_pupil(eye_region):
    try:
        if eye_region.size == 0:
            return None, None
            
        gray_eye = cv2.cvtColor(eye_region, cv2.COLOR_BGR2GRAY)
        blurred_eye = cv2.GaussianBlur(gray_eye, (7, 7), 0)
        _, threshold_eye = cv2.threshold(blurred_eye, 50, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(threshold_eye, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            pupil_contour = max(contours, key=cv2.contourArea)
            px, py, pw, ph = cv2.boundingRect(pupil_contour)
            return (px + pw // 2, py + ph // 2), (px, py, pw, ph)
        return None, None
    except Exception as e:
        print(f"Error in pupil detection: {e}")
        return None, None

def process_eye_movement(frame):
    print("[DEBUG] process_eye_movement called")
    
    try:
        if detector is None or predictor is None:
            print("[DEBUG] Models not loaded, returning 'Models not loaded'")
            return frame, "Models not loaded"
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector(gray)
        print(f"[DEBUG] Found {len(faces)} faces")
        gaze_direction = "No face detected"

        for face in faces:
            try:
                landmarks = predictor(gray, face)
                
                # Extract left and right eye landmarks
                left_eye_points = np.array([(landmarks.part(n).x, landmarks.part(n).y) for n in range(36, 42)])
                right_eye_points = np.array([(landmarks.part(n).x, landmarks.part(n).y) for n in range(42, 48)])
                
                # Get bounding rectangles for the eyes
                left_eye_rect = cv2.boundingRect(left_eye_points)
                right_eye_rect = cv2.boundingRect(right_eye_points)
                
                # Check if eye regions are valid
                if (left_eye_rect[2] <= 0 or left_eye_rect[3] <= 0 or 
                    right_eye_rect[2] <= 0 or right_eye_rect[3] <= 0):
                    print("[DEBUG] Invalid eye regions, continuing")
                    continue
                
                # Extract eye regions
                left_eye = frame[left_eye_rect[1]:left_eye_rect[1] + left_eye_rect[3], 
                                left_eye_rect[0]:left_eye_rect[0] + left_eye_rect[2]]
                right_eye = frame[right_eye_rect[1]:right_eye_rect[1] + right_eye_rect[3], 
                                 right_eye_rect[0]:right_eye_rect[0] + right_eye_rect[2]]
                
                # Detect pupils
                left_pupil, left_bbox = detect_pupil(left_eye)
                right_pupil, right_bbox = detect_pupil(right_eye)
                
                print(f"[DEBUG] Left pupil: {left_pupil}, Right pupil: {right_pupil}")
                
                # Draw bounding boxes and pupils
                cv2.rectangle(frame, (left_eye_rect[0], left_eye_rect[1]), 
                              (left_eye_rect[0] + left_eye_rect[2], left_eye_rect[1] + left_eye_rect[3]), (0, 255, 0), 2)
                cv2.rectangle(frame, (right_eye_rect[0], right_eye_rect[1]), 
                              (right_eye_rect[0] + right_eye_rect[2], right_eye_rect[1] + right_eye_rect[3]), (0, 255, 0), 2)
                
                if left_pupil and left_bbox:
                    cv2.circle(frame, (left_eye_rect[0] + left_pupil[0], left_eye_rect[1] + left_pupil[1]), 5, (0, 0, 255), -1)
                if right_pupil and right_bbox:
                    cv2.circle(frame, (right_eye_rect[0] + right_pupil[0], right_eye_rect[1] + right_pupil[1]), 5, (0, 0, 255), -1)
                
                # Gaze Detection
                if left_pupil and right_pupil:
                    lx, ly = left_pupil
                    rx, ry = right_pupil
                    
                    eye_width = left_eye_rect[2]
                    eye_height = left_eye_rect[3]
                    
                    if eye_width <= 0 or eye_height <= 0:
                        print("[DEBUG] Invalid eye dimensions, continuing")
                        continue
                        
                    norm_ly, norm_ry = ly / eye_height, ry / eye_height
                    
                    if lx < eye_width // 3 and rx < eye_width // 3:
                        gaze_direction = "Looking Left"
                    elif lx > 2 * eye_width // 3 and rx > 2 * eye_width // 3:
                        gaze_direction = "Looking Right"
                    elif norm_ly < 0.3 and norm_ry < 0.3:
                        gaze_direction = "Looking Up"
                    elif norm_ly > 0.5 and norm_ry > 0.5:
                        gaze_direction = "Looking Down"
                    else:
                        gaze_direction = "Looking at Screen"
                else:
                    gaze_direction = "Pupils not detected"
                    
                print(f"[DEBUG] Gaze direction determined: {gaze_direction}")
                    
            except Exception as e:
                print(f"[DEBUG] Error processing face: {e}")
                gaze_direction = "Face processing error"
                continue
    
    except Exception as e:
        print(f"[DEBUG] Error in eye movement detection: {e}")
        gaze_direction = "Detection error"
    
    print(f"[DEBUG] Final gaze direction: {gaze_direction}")
    return frame, gaze_direction
