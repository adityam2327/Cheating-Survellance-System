import cv2
import time
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from eye_movement import process_eye_movement
from head_pose import process_head_pose
from mobile_detection import process_mobile_detection
from lip_movement import process_lip_movement, save_lip_movement_screenshot
from emotion_detection import process_emotion_detection, initialize_emotion_detection, save_emotion_screenshot

# Import blockchain logging system
from blockchain_integration import initialize_blockchain_integration, get_blockchain_integration

# Initialize video capture from file
cap = cv2.VideoCapture(0)

# Check if video file opened successfully
if not cap.isOpened():
    print("Error: Could not open video file 'vdo.mp4'")
    exit()

# Get video properties
fps_video = cap.get(cv2.CAP_PROP_FPS)
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

print(f"Video Info: {frame_width}x{frame_height}, {fps_video:.2f} FPS, {total_frames} frames")

# Create a log directory for screenshots
log_dir = "log"
os.makedirs(log_dir, exist_ok=True)

# Initialize blockchain logging system
print("Initializing blockchain logging system...")
blockchain_integration = initialize_blockchain_integration()
print("Blockchain logging system initialized successfully!")

# Initialize emotion detection
emotion_detector = initialize_emotion_detection()

# Calibration for head pose
calibrated_angles = None
start_time = time.time()
calibration_complete = False

# Timers for each functionality
head_misalignment_start_time = None
eye_misalignment_start_time = None
mobile_detection_start_time = None

# Previous states
previous_head_state = "Looking at Screen"
previous_eye_state = "Looking at Screen"
previous_mobile_state = False
previous_lip_state = "No Movement"
previous_emotion_state = "Neutral"

# Initialize head_direction with a default value
head_direction = "Looking at Screen"

# Timer for lip movement detection
lip_movement_start_time = None

# Frame counter
frame_count = 0

# Performance optimization settings
PROCESS_EVERY_N_FRAMES = 2  # Process every 2nd frame instead of 3rd
MOBILE_DETECTION_INTERVAL = 8  # Check mobile every 8 frames (heavy operation)
EMOTION_DETECTION_INTERVAL = 4  # Check emotion every 4 frames

# Thread pool for parallel processing
executor = ThreadPoolExecutor(max_workers=3)

# Shared variables for thread safety
shared_results = {
    'mobile_detected': False,
    'current_emotion': 'Neutral',
    'stress_detected': False,
    'fear_detected': False,
    'overconfidence_detected': False,
    'audio_level': 0.0
}

print("Starting optimized video processing with blockchain logging...")
print("Press 'q' to quit during playback")
print(f"Performance settings: Process every {PROCESS_EVERY_N_FRAMES} frames")
print(f"Mobile detection: every {MOBILE_DETECTION_INTERVAL} frames")
print(f"Emotion detection: every {EMOTION_DETECTION_INTERVAL} frames")

def process_mobile_async(frame):
    """Process mobile detection asynchronously"""
    try:
        _, mobile_detected = process_mobile_detection(frame)
        return mobile_detected
    except Exception as e:
        print(f"Error in mobile detection: {e}")
        return False

def process_emotion_async(frame):
    """Process emotion detection asynchronously"""
    try:
        _, current_emotion, stress_detected, fear_detected, overconfidence_detected = process_emotion_detection(frame, emotion_detector)
        return current_emotion, stress_detected, fear_detected, overconfidence_detected
    except Exception as e:
        print(f"Error in emotion detection: {e}")
        return "Error", False, False, False

while True:
    ret, frame = cap.read()
    if not ret:
        print("End of video reached")
        break

    frame_count += 1
    
    # Skip frames to speed up processing
    if frame_count % PROCESS_EVERY_N_FRAMES != 0:
        continue

    # --- Performance Timers ---
    total_start_time = time.time()
    
    # Initialize timing variables
    eye_time = 0.0
    head_time = 0.0
    mobile_time = 0.0
    lip_time = 0.0
    emotion_time = 0.0
    
    # Start async tasks for heavy operations
    futures = {}
    
    # Mobile detection (heavy operation - run less frequently)
    if frame_count % MOBILE_DETECTION_INTERVAL == 0:
        futures['mobile'] = executor.submit(process_mobile_async, frame.copy())
    
    # Emotion detection (heavy operation - run less frequently)
    if frame_count % EMOTION_DETECTION_INTERVAL == 0:
        futures['emotion'] = executor.submit(process_emotion_async, frame.copy())
    
    # Process light operations synchronously (fast)
    try:
        # Process eye movement (fast)
        eye_start_time = time.time()
        frame, gaze_direction = process_eye_movement(frame)
        eye_time = time.time() - eye_start_time
        cv2.putText(frame, f"Gaze Direction: {gaze_direction}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    except Exception as e:
        print(f"Error in eye movement detection: {e}")
        gaze_direction = "Error"
        eye_time = 0.0

    try:
        # Process head pose (fast)
        head_start_time = time.time()
        if not calibration_complete and time.time() - start_time <= 5:  # Calibration time
            cv2.putText(frame, "Calibrating... Keep your head straight", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            _, new_calibrated_angles = process_head_pose(frame, None)
            if new_calibrated_angles is not None:
                calibrated_angles = new_calibrated_angles
                calibration_complete = True
                print("Head pose calibration completed!")
        else:
            if calibrated_angles is not None:
                frame, head_direction = process_head_pose(frame, calibrated_angles)
                cv2.putText(frame, f"Head Direction: {head_direction}", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            else:
                head_direction = "Calibration Failed"
                cv2.putText(frame, f"Head Direction: {head_direction}", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        head_time = time.time() - head_start_time
    except Exception as e:
        print(f"Error in head pose detection: {e}")
        head_direction = "Error"
        head_time = 0.0

    # Process lip movement (medium speed)
    try:
        lip_start_time = time.time()
        frame, lip_state, is_whispering = process_lip_movement(frame, 0.0)
        lip_time = time.time() - lip_start_time
        cv2.putText(frame, f"Lip State: {lip_state}", (20, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Whispering: {is_whispering}", (20, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    except Exception as e:
        print(f"Error in lip movement detection: {e}")
        lip_state = "Error"
        is_whispering = False
        lip_time = 0.0
    
    # Collect async results
    if 'mobile' in futures:
        try:
            mobile_start_time = time.time()
            mobile_detected = futures['mobile'].result(timeout=0.8)
            mobile_time = time.time() - mobile_start_time
            shared_results['mobile_detected'] = mobile_detected
        except Exception as e:
            print(f"Error getting mobile detection result: {e}")
            mobile_detected = shared_results['mobile_detected']
            mobile_time = 0.0
    
    if 'emotion' in futures:
        try:
            emotion_start_time = time.time()
            current_emotion, stress_detected, fear_detected, overconfidence_detected = futures['emotion'].result(timeout=0.8)
            emotion_time = time.time() - emotion_start_time
            shared_results['current_emotion'] = current_emotion
            shared_results['stress_detected'] = stress_detected
            shared_results['fear_detected'] = fear_detected
            shared_results['overconfidence_detected'] = overconfidence_detected
        except Exception as e:
            print(f"Error getting emotion detection result: {e}")
            current_emotion = shared_results['current_emotion']
            stress_detected = shared_results['stress_detected']
            fear_detected = shared_results['fear_detected']
            overconfidence_detected = shared_results['overconfidence_detected']
            emotion_time = 0.0
    
    # Use cached results if not processed this frame
    if 'mobile' not in futures:
        mobile_detected = shared_results['mobile_detected']
    if 'emotion' not in futures:
        current_emotion = shared_results['current_emotion']
        stress_detected = shared_results['stress_detected']
        fear_detected = shared_results['fear_detected']
        overconfidence_detected = shared_results['overconfidence_detected']
    
    # Display results
    cv2.putText(frame, f"Mobile Detected: {mobile_detected}", (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(frame, f"Emotion: {current_emotion}", (20, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # Display emotion alerts
    if stress_detected:
        cv2.putText(frame, "STRESS DETECTED!", (20, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    if fear_detected:
        cv2.putText(frame, "FEAR DETECTED!", (20, 270), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    if overconfidence_detected:
        cv2.putText(frame, "OVERCONFIDENCE DETECTED!", (20, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    # --- Performance Timers ---
    total_time = time.time() - total_start_time
    fps = 1 / total_time if total_time > 0 else 0
    print(f"Frame {frame_count} | FPS: {fps:.2f} | Eye: {eye_time:.3f}s | Head: {head_time:.3f}s | Mobile: {mobile_time:.3f}s | Lip: {lip_time:.3f}s | Emotion: {emotion_time:.3f}s")

    # Check for head misalignment and log to blockchain
    if head_direction != "Looking at Screen" and head_direction != "Calibration Failed" and head_direction != "Error":
        if head_misalignment_start_time is None:
            head_misalignment_start_time = time.time()
        elif time.time() - head_misalignment_start_time >= 3:
            filename = os.path.join(log_dir, f"head_{head_direction}_{int(time.time())}.png")
            cv2.imwrite(filename, frame)
            print(f"Screenshot saved: {filename}")
            
            # Log to blockchain
            try:
                blockchain_integration.log_head_misalignment(
                    direction=str(head_direction),
                    confidence=0.8,  # High confidence after 3 seconds
                    screenshot_path=filename,
                    metadata={
                        'frame_count': frame_count,
                        'duration': 3.0,
                        'previous_state': previous_head_state
                    }
                )
                print(f"Head misalignment logged to blockchain: {head_direction}")
            except Exception as e:
                print(f"Error logging to blockchain: {e}")
            
            head_misalignment_start_time = None  # Reset timer
    else:
        head_misalignment_start_time = None  # Reset timer

    # Check for eye misalignment and log to blockchain
    if gaze_direction != "Looking at Screen" and gaze_direction != "No face detected" and gaze_direction != "Error":
        if eye_misalignment_start_time is None:
            eye_misalignment_start_time = time.time()
        elif time.time() - eye_misalignment_start_time >= 3:
            filename = os.path.join(log_dir, f"eye_{gaze_direction}_{int(time.time())}.png")
            cv2.imwrite(filename, frame)
            print(f"Screenshot saved: {filename}")
            
            # Log to blockchain
            try:
                blockchain_integration.log_eye_misalignment(
                    direction=gaze_direction,
                    confidence=0.8,  # High confidence after 3 seconds
                    screenshot_path=filename,
                    metadata={
                        'frame_count': frame_count,
                        'duration': 3.0,
                        'previous_state': previous_eye_state
                    }
                )
                print(f"Eye misalignment logged to blockchain: {gaze_direction}")
            except Exception as e:
                print(f"Error logging to blockchain: {e}")
            
            eye_misalignment_start_time = None  # Reset timer
    else:
        eye_misalignment_start_time = None  # Reset timer

    # Check for mobile detection and log to blockchain
    if mobile_detected:
        if mobile_detection_start_time is None:
            mobile_detection_start_time = time.time()
        elif time.time() - mobile_detection_start_time >= 3:
            filename = os.path.join(log_dir, f"mobile_detected_{int(time.time())}.png")
            cv2.imwrite(filename, frame)
            print(f"Screenshot saved: {filename}")
            
            # Log to blockchain
            try:
                blockchain_integration.log_mobile_detection(
                    confidence=0.9,  # High confidence for mobile detection
                    screenshot_path=filename,
                    metadata={
                        'frame_count': frame_count,
                        'duration': 3.0,
                        'previous_state': previous_mobile_state
                    }
                )
                print("Mobile detection logged to blockchain")
            except Exception as e:
                print(f"Error logging to blockchain: {e}")
            
            mobile_detection_start_time = None  # Reset timer
    else:
        mobile_detection_start_time = None  # Reset timer
        
    # Check for lip movement/whispering detection and log to blockchain
    if lip_state != "No Movement" and lip_state != "Error":
        if lip_movement_start_time is None:
            lip_movement_start_time = time.time()
        elif time.time() - lip_movement_start_time >= 3:
            # If whispering is detected, save a screenshot
            if is_whispering:
                filename = save_lip_movement_screenshot(frame, "Whispering", log_dir)
            elif lip_state == "Speaking" and not mobile_detected:
                # If lips are moving but no mobile is detected, it might be whispering
                filename = save_lip_movement_screenshot(frame, "Possible_Whispering", log_dir)
            
            # Log to blockchain
            try:
                blockchain_integration.log_lip_movement(
                    lip_state=lip_state,
                    is_whispering=is_whispering,
                    confidence=0.7,  # Medium confidence for lip movement
                    screenshot_path=filename,
                    metadata={
                        'frame_count': frame_count,
                        'duration': 3.0,
                        'previous_state': previous_lip_state,
                        'mobile_detected': mobile_detected
                    }
                )
                print(f"Lip movement logged to blockchain: {lip_state} (Whispering: {is_whispering})")
            except Exception as e:
                print(f"Error logging to blockchain: {e}")
            
            lip_movement_start_time = None  # Reset timer
    else:
        lip_movement_start_time = None  # Reset timer

    # Check for concerning emotions and log to blockchain
    if stress_detected or fear_detected or overconfidence_detected:
        if emotion_detection_start_time is None:
            emotion_detection_start_time = time.time()
        elif time.time() - emotion_detection_start_time >= 3:
            # Save screenshot for concerning emotions
            if stress_detected:
                filename = save_emotion_screenshot(frame, "Stress", log_dir)
            elif fear_detected:
                filename = save_emotion_screenshot(frame, "Fear", log_dir)
            elif overconfidence_detected:
                filename = save_emotion_screenshot(frame, "Overconfidence", log_dir)
            
            # Log to blockchain
            try:
                blockchain_integration.log_emotion_detection(
                    emotion=current_emotion,
                    stress_detected=stress_detected,
                    fear_detected=fear_detected,
                    overconfidence_detected=overconfidence_detected,
                    confidence=0.8,  # High confidence for emotion detection
                    screenshot_path=filename,
                    metadata={
                        'frame_count': frame_count,
                        'duration': 3.0,
                        'previous_state': previous_emotion_state
                    }
                )
                print(f"Emotion detection logged to blockchain: {current_emotion}")
            except Exception as e:
                print(f"Error logging to blockchain: {e}")
            
            emotion_detection_start_time = None  # Reset timer
    else:
        emotion_detection_start_time = None  # Reset timer

    # Display the combined output
    cv2.imshow("Optimized Combined Detection with Blockchain Logging", frame)
    
    # Add delay to make video playback visible (adjust as needed)
    if cv2.waitKey(30) & 0xFF == ord('q'):  # 30ms delay, press 'q' to quit
        break

# Cleanup
executor.shutdown(wait=True)
cap.release()
cv2.destroyAllWindows()

# Flush any pending blockchain events before exit
try:
    blockchain_integration.flush_pending_events()
    print("Pending blockchain events flushed successfully")
except Exception as e:
    print(f"Error flushing pending events: {e}")

print("Optimized video processing with blockchain logging completed!")
print("Blockchain logs saved to database. Use the dashboard to view detailed statistics.")
