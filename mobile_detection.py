import cv2
import torch
from ultralytics import YOLO
import os
import time

# Load trained YOLO model with error handling
try:
    model_path = "model/best.pt"
    if not os.path.exists(model_path):
        print(f"Warning: Model file {model_path} not found. Mobile detection will be disabled.")
        model = None
    else:
        model = YOLO(model_path)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Mobile detection model loaded on {device}")
        model.to(device)
        # YOLO models are already optimized for inference
except Exception as e:
    print(f"Error loading mobile detection model: {e}")
    model = None

def process_mobile_detection(frame):
    print("[DEBUG] process_mobile_detection called")
    
    if model is None:
        print("[DEBUG] Model not loaded, returning False")
        return frame, False
    
    try:
        # Add timeout to prevent long processing
        start_time = time.time()
        timeout = 0.5  # 500ms timeout
        
        # Optimize frame size for faster processing
        height, width = frame.shape[:2]
        print(f"[DEBUG] Frame size: {width}x{height}")
        
        if width > 640 or height > 480:
            # Resize frame for faster processing
            scale = min(640/width, 480/height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            frame_resized = cv2.resize(frame, (new_width, new_height))
            print(f"[DEBUG] Resized frame to: {new_width}x{new_height}")
        else:
            frame_resized = frame
        
        # Run inference with optimized settings
        print("[DEBUG] Running YOLO inference...")
        results = model(frame_resized, verbose=False, conf=0.5, iou=0.45, max_det=5)
        
        # Check timeout
        if time.time() - start_time > timeout:
            print("[DEBUG] Mobile detection timeout, returning False")
            return frame, False
        
        mobile_detected = False
        print(f"[DEBUG] YOLO results: {len(results)} detections")

        for result in results:
            if result.boxes is None:
                print("[DEBUG] No boxes in result")
                continue
                
            for box in result.boxes:
                conf = box.conf[0].item()
                cls = int(box.cls[0].item())
                print(f"[DEBUG] Detection - class: {cls}, confidence: {conf}")

                # Check all classes for mobile-like objects (phones, tablets, etc.)
                # Lower confidence threshold for better detection
                if conf < 0.5:  # Reduced from 0.8
                    print(f"[DEBUG] Confidence {conf} below threshold 0.5, skipping")
                    continue

                # Scale bounding box back to original frame size if needed
                if width > 640 or height > 480:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    x1 = int(x1 / scale)
                    y1 = int(y1 / scale)
                    x2 = int(x2 / scale)
                    y2 = int(y2 / scale)
                else:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                
                label = f"Mobile ({conf:.2f})"
                print(f"[DEBUG] Drawing mobile detection: {label} at ({x1},{y1})-({x2},{y2})")

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                mobile_detected = True
        
        print(f"[DEBUG] Mobile detection result: {mobile_detected}")
        return frame, mobile_detected
    except Exception as e:
        print(f"[DEBUG] Error in mobile detection: {e}")
        return frame, False
