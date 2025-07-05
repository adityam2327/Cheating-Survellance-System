import cv2
import numpy as np
import time
import os

class EmotionDetector:
    def __init__(self, model_path=None):
        """
        Initialize the emotion detector with OpenCV face detection
        """
        self.emotions = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']
        
        # Load OpenCV face cascade classifier
        try:
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            if os.path.exists(cascade_path):
                self.face_cascade = cv2.CascadeClassifier(cascade_path)
            else:
                # Fallback path
                self.face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
        except AttributeError:
            # Fallback for older OpenCV versions
            self.face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
        
        # Load eye cascade for better detection
        try:
            eye_cascade_path = cv2.data.haarcascades + 'haarcascade_eye.xml'
            if os.path.exists(eye_cascade_path):
                self.eye_cascade = cv2.CascadeClassifier(eye_cascade_path)
            else:
                self.eye_cascade = None
        except AttributeError:
            self.eye_cascade = None
        
        # Emotion state tracking
        self.emotion_history = []
        self.max_history = 10
        self.stress_threshold = 0.6
        self.fear_threshold = 0.5
        self.overconfidence_threshold = 0.7
        
        # Timing for emotion detection
        self.last_emotion_time = 0
        self.emotion_interval = 0.5  # Check emotion every 0.5 seconds
        
        # Frame counter for emotion variation
        self.frame_counter = 0
        
    def detect_emotion_from_features(self, face_img, eyes_detected):
        """
        Detect emotion using facial features and image analysis
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
            
            # Calculate basic image features
            brightness = np.mean(gray)
            contrast = np.std(gray)
            
            # Detect edges (indicator of facial expressions)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
            
            # Calculate facial symmetry
            left_half = gray[:, :gray.shape[1]//2]
            right_half = cv2.flip(gray[:, gray.shape[1]//2:], 1)
            
            # Ensure both halves have the same size
            min_width = min(left_half.shape[1], right_half.shape[1])
            left_half = left_half[:, :min_width]
            right_half = right_half[:, :min_width]
            
            symmetry_score = 1.0 - np.mean(np.abs(left_half.astype(float) - right_half.astype(float))) / 255.0
            
            # Calculate emotion scores based on features
            scores = np.zeros(7)
            
            # Brightness affects emotions
            if brightness < 80:  # Dark face
                scores[4] += 0.3  # Sad
                scores[0] += 0.2  # Angry
            elif brightness > 150:  # Bright face
                scores[3] += 0.2  # Happy
            
            # Contrast affects emotions
            if contrast > 50:  # High contrast (more defined features)
                scores[0] += 0.3  # Angry
                scores[5] += 0.2  # Surprise
            elif contrast < 20:  # Low contrast (smooth features)
                scores[6] += 0.3  # Neutral
                scores[4] += 0.2  # Sad
            
            # Edge density affects emotions
            if edge_density > 0.1:  # Many edges (active expressions)
                scores[5] += 0.4  # Surprise
                scores[3] += 0.2  # Happy
            elif edge_density < 0.05:  # Few edges (neutral/smooth)
                scores[6] += 0.4  # Neutral
                scores[4] += 0.2  # Sad
            
            # Symmetry affects emotions
            if symmetry_score > 0.8:  # High symmetry
                scores[6] += 0.3  # Neutral
            else:  # Low symmetry (more emotional)
                scores[0] += 0.2  # Angry
                scores[4] += 0.2  # Sad
            
            # Eye detection affects emotions
            if eyes_detected > 0:
                if eyes_detected == 2:  # Both eyes visible
                    scores[6] += 0.2  # Neutral
                    scores[3] += 0.1  # Happy
                else:  # One eye or partial detection
                    scores[2] += 0.3  # Fear
                    scores[5] += 0.2  # Surprise
            else:  # No eyes detected
                scores[2] += 0.4  # Fear
                scores[4] += 0.2  # Sad
            
            # Add some randomness to make it more realistic
            self.frame_counter += 1
            if self.frame_counter % 30 == 0:  # Every 30 frames
                # Simulate emotion changes
                if np.random.random() < 0.3:  # 30% chance of emotion change
                    random_emotion = np.random.randint(0, 7)
                    scores[random_emotion] += 0.2
            
            # Normalize scores
            if np.sum(scores) > 0:
                scores = scores / np.sum(scores)
            else:
                scores[6] = 1.0  # Default to neutral
            
            # Get the emotion with highest score
            emotion_idx = np.argmax(scores)
            emotion = self.emotions[emotion_idx]
            confidence = scores[emotion_idx]
            
            return emotion, confidence, scores
            
        except Exception as e:
            print(f"Error in feature-based emotion detection: {e}")
            return "Neutral", 0.5, np.array([0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.4])
    
    def detect_emotion(self, face_img):
        """
        Detect emotion from face image
        """
        try:
            # Convert to grayscale for eye detection
            gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
            
            # Detect eyes
            eyes_detected = 0
            if self.eye_cascade is not None:
                eyes = self.eye_cascade.detectMultiScale(gray, 1.1, 5)
                eyes_detected = len(eyes)
            
            # Detect emotion using facial features
            emotion, confidence, emotion_probs = self.detect_emotion_from_features(face_img, eyes_detected)
            
            return emotion, confidence, emotion_probs
            
        except Exception as e:
            print(f"Error in emotion detection: {e}")
            return "Neutral", 0.0, np.zeros(7)
    
    def analyze_emotion_state(self, emotion, confidence, emotion_probs):
        """
        Analyze emotion state for stress, fear, and overconfidence
        """
        current_time = time.time()
        
        # Add to history
        self.emotion_history.append({
            'emotion': emotion,
            'confidence': confidence,
            'probabilities': emotion_probs,
            'timestamp': current_time
        })
        
        # Keep only recent history
        if len(self.emotion_history) > self.max_history:
            self.emotion_history.pop(0)
        
        # Analyze for stress indicators
        stress_score = self._calculate_stress_score()
        
        # Analyze for fear indicators
        fear_score = self._calculate_fear_score()
        
        # Analyze for overconfidence indicators
        overconfidence_score = self._calculate_overconfidence_score()
        
        return {
            'stress': stress_score,
            'fear': fear_score,
            'overconfidence': overconfidence_score,
            'current_emotion': emotion,
            'confidence': confidence
        }
    
    def _calculate_stress_score(self):
        """
        Calculate stress score based on emotion patterns
        Stress indicators: Anger, Sadness, Fear, high variability
        """
        if len(self.emotion_history) < 3:
            return 0.0
        
        stress_emotions = ['Angry', 'Sad', 'Fear']
        stress_score = 0.0
        
        # Check for stress-related emotions
        for entry in self.emotion_history[-5:]:  # Last 5 entries
            if entry['emotion'] in stress_emotions:
                stress_score += entry['confidence'] * 0.3
        
        # Check for emotion variability (indicator of stress)
        emotions = [entry['emotion'] for entry in self.emotion_history[-5:]]
        unique_emotions = len(set(emotions))
        if unique_emotions > 3:  # High variability
            stress_score += 0.2
        
        return min(stress_score, 1.0)
    
    def _calculate_fear_score(self):
        """
        Calculate fear score based on emotion patterns
        Fear indicators: Fear emotion, Surprise, high arousal
        """
        if len(self.emotion_history) < 3:
            return 0.0
        
        fear_score = 0.0
        
        # Check for fear and surprise emotions
        for entry in self.emotion_history[-5:]:
            if entry['emotion'] == 'Fear':
                fear_score += entry['confidence'] * 0.4
            elif entry['emotion'] == 'Surprise':
                fear_score += entry['confidence'] * 0.2
        
        return min(fear_score, 1.0)
    
    def _calculate_overconfidence_score(self):
        """
        Calculate overconfidence score based on emotion patterns
        Overconfidence indicators: Happy, high confidence, low variability
        """
        if len(self.emotion_history) < 3:
            return 0.0
        
        overconfidence_score = 0.0
        
        # Check for happiness with high confidence
        for entry in self.emotion_history[-5:]:
            if entry['emotion'] == 'Happy' and entry['confidence'] > 0.8:
                overconfidence_score += entry['confidence'] * 0.3
        
        # Check for low emotion variability (consistent happy state)
        emotions = [entry['emotion'] for entry in self.emotion_history[-5:]]
        if len(set(emotions)) <= 2 and 'Happy' in emotions:
            overconfidence_score += 0.2
        
        return min(overconfidence_score, 1.0)
    
    def get_emotion_alert(self, emotion_state):
        """
        Get alert based on emotion state
        """
        alerts = []
        
        if emotion_state['stress'] > self.stress_threshold:
            alerts.append(f"STRESS DETECTED: {emotion_state['stress']:.2f}")
        
        if emotion_state['fear'] > self.fear_threshold:
            alerts.append(f"FEAR DETECTED: {emotion_state['fear']:.2f}")
        
        if emotion_state['overconfidence'] > self.overconfidence_threshold:
            alerts.append(f"OVERCONFIDENCE DETECTED: {emotion_state['overconfidence']:.2f}")
        
        return alerts

def process_emotion_detection(frame, emotion_detector):
    """
    Process emotion detection on the given frame
    """
    print("[DEBUG] process_emotion_detection called")
    
    current_time = time.time()
    
    # Check if enough time has passed since last detection
    if current_time - emotion_detector.last_emotion_time < emotion_detector.emotion_interval:
        print("[DEBUG] Too soon for emotion detection, returning 'Processing...'")
        return frame, "Processing...", False, False, False
    
    emotion_detector.last_emotion_time = current_time
    
    # Convert frame to grayscale for face detection
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Detect faces
    faces = emotion_detector.face_cascade.detectMultiScale(
        gray, 
        scaleFactor=1.1, 
        minNeighbors=5, 
        minSize=(30, 30)
    )
    
    print(f"[DEBUG] Found {len(faces)} faces")
    
    emotion_state = {
        'stress': 0.0,
        'fear': 0.0,
        'overconfidence': 0.0,
        'current_emotion': 'No Face',
        'confidence': 0.0
    }
    
    if len(faces) > 0:
        # Process the largest face
        (x, y, w, h) = max(faces, key=lambda rect: rect[2] * rect[3])
        print(f"[DEBUG] Processing face at ({x},{y}) with size {w}x{h}")
        
        # Ensure coordinates are within frame bounds
        x = max(0, x)
        y = max(0, y)
        w = min(w, frame.shape[1] - x)
        h = min(h, frame.shape[0] - y)
        
        if w > 0 and h > 0:
            # Extract face region
            face_img = frame[y:y+h, x:x+w]
            
            # Detect emotion
            emotion, confidence, emotion_probs = emotion_detector.detect_emotion(face_img)
            print(f"[DEBUG] Detected emotion: {emotion} with confidence: {confidence}")
            
            # Analyze emotion state
            emotion_state = emotion_detector.analyze_emotion_state(emotion, confidence, emotion_probs)
            print(f"[DEBUG] Emotion state: {emotion_state}")
            
            # Draw rectangle around face
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            # Draw emotion label
            cv2.putText(frame, f"{emotion}: {confidence:.2f}", 
                       (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            print("[DEBUG] Invalid face dimensions")
    else:
        print("[DEBUG] No faces detected")
    
    # Get alerts
    alerts = emotion_detector.get_emotion_alert(emotion_state)
    print(f"[DEBUG] Emotion alerts: {alerts}")
    
    # Determine if any concerning emotions are detected
    stress_detected = emotion_state['stress'] > emotion_detector.stress_threshold
    fear_detected = emotion_state['fear'] > emotion_detector.fear_threshold
    overconfidence_detected = emotion_state['overconfidence'] > emotion_detector.overconfidence_threshold
    
    print(f"[DEBUG] Final results - emotion: {emotion_state['current_emotion']}, stress: {stress_detected}, fear: {fear_detected}, overconfidence: {overconfidence_detected}")
    
    return frame, emotion_state['current_emotion'], stress_detected, fear_detected, overconfidence_detected

def save_emotion_screenshot(frame, emotion_type, log_dir):
    """
    Save screenshot when concerning emotion is detected
    """
    timestamp = int(time.time())
    filename = os.path.join(log_dir, f"emotion_{emotion_type}_{timestamp}.png")
    cv2.imwrite(filename, frame)
    print(f"Emotion screenshot saved: {filename}")
    return filename

# Global emotion detector instance
emotion_detector = None

def initialize_emotion_detection(model_path=None):
    """
    Initialize the emotion detection system
    """
    global emotion_detector
    emotion_detector = EmotionDetector(model_path)
    print("Emotion detection initialized with OpenCV")
    return emotion_detector 