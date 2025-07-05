import json
import cv2
import base64
import numpy as np
import time
from channels.generic.websocket import AsyncWebsocketConsumer
from concurrent.futures import ThreadPoolExecutor
from django.contrib.auth.models import AnonymousUser
from violations.models import Violation
from exam_sessions.models import ExamSession, SessionEvent
from django.utils import timezone
import asyncio
from asgiref.sync import sync_to_async
import mediapipe as mp
import dlib
from scipy.spatial import distance as dist

# Import your detection functions
from eye_movement import process_eye_movement
from head_pose import process_head_pose
from mobile_detection import process_mobile_detection
from lip_movement import process_lip_movement
from emotion_detection import process_emotion_detection, initialize_emotion_detection

class MonitoringConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.active_session = None
        self.calibrated_angles = None
        self.calibration_start_time = None
        self.calibration_duration = 3.0
        self.frame_count = 0
        self.frame_times = []
        self.max_frame_times = 30
        self.mobile_detected_cache = False
        self.mobile_detected_interval = 5  # Check mobile every 5 frames for better responsiveness
        self.violation_timers = {
            'head_misalignment': None,
            'eye_misalignment': None,
            'mobile_detection': None,
            'lip_movement': None,
            'emotion_detection': None
        }
        self.last_violation_time = {}
        self.violation_threshold = 2.0
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.emotion_detector = None
        
        # Initialize MediaPipe and dlib components
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        self.face_mesh = None
        self.predictor = None
        self.detector = None
        self.last_results = {}  # Store last valid results to prevent static values
        
    async def connect(self):
        await self.accept()
        print("WebSocket connection accepted.")

        try:
            # Initialize MediaPipe Face Mesh
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            
            # Initialize dlib face detector and predictor
            self.detector = dlib.get_frontal_face_detector()
            # Make sure you have the shape predictor file
            try:
                self.predictor = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')
            except:
                print("Warning: dlib shape predictor not found. Some features may be limited.")
                self.predictor = None
            
            self.executor = ThreadPoolExecutor(max_workers=4)
            self.emotion_detector = initialize_emotion_detection()
            if self.emotion_detector is None:
                print("Warning: Emotion detector initialization failed. Using fallback.")

            self.calibrated_angles = None
            self.calibration_start_time = time.time()
            self.calibration_duration = 3.0

            # Initialize tracking variables
            self.frame_times = []
            self.max_frame_times = 30
            self.frame_count = 0
            self.mobile_detected_cache = False
            self.mobile_detected_interval = 5
            self.last_results = {
                'gaze_direction': 'Center',
                'head_direction': 'Looking at Screen',
                'lip_state': 'No Movement',
                'mobile_detected': False,
                'emotion': 'Neutral'
            }

            # Violation tracking
            self.violation_timers = {
                'head_misalignment': None,
                'eye_misalignment': None,
                'mobile_detection': None,
                'lip_movement': None,
                'emotion_detection': None
            }
            self.violation_threshold = 2.0
            self.last_violation_time = {}

            # Get or create active session
            self.user = self.scope.get('user', AnonymousUser())
            if not isinstance(self.user, AnonymousUser):
                self.active_session, created = await self.get_or_create_session()
                if created:
                    print(f"Created new session: {self.active_session.session_id}")

            print("WebSocket resources initialized successfully.")
            await self.send(text_data=json.dumps({'status': 'connected'}))

        except Exception as e:
            print(f"Error during WebSocket initialization: {e}")
            await self.close(code=4001)

    def detect_eye_movement_realtime(self, frame):
        """Real-time eye movement detection using MediaPipe"""
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(rgb_frame)
            
            if results.multi_face_landmarks:
                face_landmarks = results.multi_face_landmarks[0]
                
                # Get eye landmarks
                LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
                RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
                
                h, w = frame.shape[:2]
                
                # Calculate eye centers
                left_eye_center = np.mean([[face_landmarks.landmark[i].x * w, 
                                          face_landmarks.landmark[i].y * h] for i in LEFT_EYE], axis=0)
                right_eye_center = np.mean([[face_landmarks.landmark[i].x * w, 
                                           face_landmarks.landmark[i].y * h] for i in RIGHT_EYE], axis=0)
                
                # Calculate gaze direction based on eye position relative to face
                face_center_x = (left_eye_center[0] + right_eye_center[0]) / 2
                frame_center_x = w / 2
                
                # Determine gaze direction
                if abs(face_center_x - frame_center_x) < 30:
                    return 'Center'
                elif face_center_x < frame_center_x - 30:
                    return 'Left'
                elif face_center_x > frame_center_x + 30:
                    return 'Right'
                else:
                    return 'Center'
            
            return self.last_results.get('gaze_direction', 'Center')
            
        except Exception as e:
            print(f"Eye movement detection error: {e}")
            return self.last_results.get('gaze_direction', 'Center')

    def detect_head_pose_realtime(self, frame):
        """Real-time head pose detection"""
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(rgb_frame)
            
            if results.multi_face_landmarks:
                face_landmarks = results.multi_face_landmarks[0]
                
                # Get key facial landmarks
                h, w = frame.shape[:2]
                
                # Nose tip, chin, left and right face points
                nose_tip = [face_landmarks.landmark[1].x * w, face_landmarks.landmark[1].y * h]
                chin = [face_landmarks.landmark[18].x * w, face_landmarks.landmark[18].y * h]
                left_face = [face_landmarks.landmark[234].x * w, face_landmarks.landmark[234].y * h]
                right_face = [face_landmarks.landmark[454].x * w, face_landmarks.landmark[454].y * h]
                
                # Calculate head orientation
                face_width = abs(right_face[0] - left_face[0])
                face_center_x = (left_face[0] + right_face[0]) / 2
                frame_center_x = w / 2
                
                # Vertical alignment (up/down)
                nose_chin_distance = abs(nose_tip[1] - chin[1])
                frame_center_y = h / 2
                
                # Determine head direction
                horizontal_threshold = face_width * 0.15
                vertical_threshold = 30
                
                if abs(face_center_x - frame_center_x) > horizontal_threshold:
                    if face_center_x < frame_center_x:
                        return 'Looking Left'
                    else:
                        return 'Looking Right'
                elif abs(nose_tip[1] - frame_center_y) > vertical_threshold:
                    if nose_tip[1] < frame_center_y - vertical_threshold:
                        return 'Looking Up'
                    else:
                        return 'Looking Down'
                else:
                    return 'Looking at Screen'
            
            return self.last_results.get('head_direction', 'Looking at Screen')
            
        except Exception as e:
            print(f"Head pose detection error: {e}")
            return self.last_results.get('head_direction', 'Looking at Screen')

    def detect_lip_movement_realtime(self, frame):
        """Real-time lip movement detection"""
        try:
            if self.predictor is None:
                return 'No Movement'
                
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.detector(gray)
            
            if len(faces) > 0:
                face = faces[0]
                landmarks = self.predictor(gray, face)
                
                # Get lip landmarks (points 48-67 are mouth landmarks)
                lip_points = []
                for i in range(48, 68):
                    x = landmarks.part(i).x
                    y = landmarks.part(i).y
                    lip_points.append([x, y])
                
                lip_points = np.array(lip_points)
                
                # Calculate mouth aspect ratio (MAR)
                # Vertical distances
                A = dist.euclidean(lip_points[13], lip_points[19])  # 61, 67
                B = dist.euclidean(lip_points[14], lip_points[18])  # 62, 66
                C = dist.euclidean(lip_points[15], lip_points[17])  # 63, 65
                
                # Horizontal distance
                D = dist.euclidean(lip_points[0], lip_points[12])   # 48, 60
                
                # Calculate MAR
                mar = (A + B + C) / (3.0 * D)
                
                # Determine lip movement based on MAR threshold
                if mar > 0.5:
                    return 'Speaking'
                elif mar > 0.3:
                    return 'Slight Movement'
                else:
                    return 'No Movement'
            
            return self.last_results.get('lip_state', 'No Movement')
            
        except Exception as e:
            print(f"Lip movement detection error: {e}")
            return self.last_results.get('lip_state', 'No Movement')

    def detect_mobile_phone_realtime(self, frame):
        """Real-time mobile phone detection using edge detection and contours"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Edge detection
            edges = cv2.Canny(blurred, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Look for rectangular shapes that could be phones
            for contour in contours:
                # Approximate contour to polygon
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # Check if it's roughly rectangular (4 corners) and has appropriate size
                if len(approx) == 4:
                    x, y, w, h = cv2.boundingRect(approx)
                    aspect_ratio = w / float(h)
                    area = cv2.contourArea(contour)
                    
                    # Phone-like characteristics: aspect ratio between 0.4-0.8, reasonable size
                    if 0.4 < aspect_ratio < 0.8 and 1000 < area < 50000:
                        return True
            
            return False
            
        except Exception as e:
            print(f"Mobile detection error: {e}")
            return self.last_results.get('mobile_detected', False)

    def detect_emotion_realtime(self, frame):
        """Real-time emotion detection fallback"""
        try:
            if self.emotion_detector is not None:
                # Use the initialized emotion detector
                _, emotion, _, _, _ = process_emotion_detection(frame, self.emotion_detector)
                return emotion
            else:
                # Simple brightness-based emotion estimation as fallback
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.detector(gray) if self.detector else []
                
                if len(faces) > 0:
                    face = faces[0]
                    face_roi = gray[face.top():face.bottom(), face.left():face.right()]
                    brightness = np.mean(face_roi)
                    
                    # Simple heuristic based on facial brightness patterns
                    if brightness > 120:
                        return 'Happy'
                    elif brightness < 80:
                        return 'Sad'
                    else:
                        return 'Neutral'
                else:
                    return 'Neutral'
                    
        except Exception as e:
            print(f"Emotion detection error: {e}")
            return self.last_results.get('emotion', 'Neutral')

    async def get_or_create_session(self):
        """Get or create an active exam session for the user"""
        try:
            active_session = await self.get_active_session()
            if active_session:
                return active_session, False
            
            session_id = f"session_{int(time.time())}_{self.user.id}"
            session = ExamSession(
                user=self.user,
                session_id=session_id,
                start_time=timezone.now(),
                is_active=True
            )
            await self.save_session(session)
            return session, True
        except Exception as e:
            print(f"Error creating session: {e}")
            return None, False

    async def get_active_session(self):
        """Get active session for the user"""
        try:
            def get_session():
                return ExamSession.objects.filter(user=self.user, is_active=True).first()
            
            return await sync_to_async(get_session)()
        except Exception as e:
            print(f"Error getting active session: {e}")
            return None

    async def save_session(self, session):
        """Save session to database"""
        try:
            await sync_to_async(session.save)()
        except Exception as e:
            print(f"Error saving session: {e}")

    async def disconnect(self, close_code):
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False, cancel_futures=True)
        if hasattr(self, 'face_mesh'):
            self.face_mesh.close()
        print(f"WebSocket disconnected with code: {close_code}")

    async def receive(self, text_data):
        processing_start_time = time.time()
        
        try:
            data = json.loads(text_data)
            image_data = data.get('image')

            if not image_data:
                return

            # Calculate FPS
            current_time = time.time()
            self.frame_times.append(current_time)
            
            if len(self.frame_times) > self.max_frame_times:
                self.frame_times.pop(0)
            
            if len(self.frame_times) > 1:
                time_diff = self.frame_times[-1] - self.frame_times[0]
                fps = (len(self.frame_times) - 1) / time_diff if time_diff > 0 else 0
            else:
                fps = 0

            # Decode the image
            try:
                header, encoded = image_data.split(",", 1)
                decoded_image = base64.b64decode(encoded)
                image = np.frombuffer(decoded_image, np.uint8)
                frame = cv2.imdecode(image, cv2.IMREAD_COLOR)
                
                if frame is None:
                    raise ValueError("Failed to decode frame")
                    
            except Exception as e:
                print(f"Error decoding image: {e}")
                await self.send(text_data=json.dumps({'status': 'error', 'message': 'Image decode error'}))
                return
            
            # Handle calibration phase
            if self.calibrated_angles is None:
                if time.time() - self.calibration_start_time < self.calibration_duration:
                    try:
                        head_direction = self.detect_head_pose_realtime(frame)
                        self.calibrated_angles = (0, 0, 0)  # Simple calibration
                        
                        await self.send(text_data=json.dumps({
                            'status': 'calibrating',
                            'fps': round(fps, 1),
                            'processing_time': 0,
                            'confidence': 100.0,
                            'calibration_progress': int((time.time() - self.calibration_start_time) / self.calibration_duration * 100)
                        }))
                        return
                    except Exception as e:
                        print(f"Calibration error: {e}")
                        await self.send(text_data=json.dumps({
                            'status': 'calibrating',
                            'fps': round(fps, 1),
                            'processing_time': 0,
                            'confidence': 100.0,
                            'calibration_progress': int((time.time() - self.calibration_start_time) / self.calibration_duration * 100)
                        }))
                        return
                
                # Complete calibration
                self.calibrated_angles = (0, 0, 0)
                print("Calibration completed, starting real-time detection...")

            # --- Run Real-time Detections ---
            results = {}
            detection_errors = []
            self.frame_count += 1
            
            try:
                # Real-time detections - run every frame for responsiveness
                results['gaze_direction'] = self.detect_eye_movement_realtime(frame)
                results['head_direction'] = self.detect_head_pose_realtime(frame)
                results['lip_state'] = self.detect_lip_movement_realtime(frame)
                results['emotion'] = self.detect_emotion_realtime(frame)

                # Mobile detection: run every N frames for performance
                if self.frame_count % self.mobile_detected_interval == 0:
                    results['mobile_detected'] = self.detect_mobile_phone_realtime(frame)
                    self.mobile_detected_cache = results['mobile_detected']
                else:
                    results['mobile_detected'] = self.mobile_detected_cache

                # Update last valid results
                for key, value in results.items():
                    if value is not None:
                        self.last_results[key] = value

                print(f"[REAL-TIME DEBUG] Detection results: {results}")

            except Exception as e:
                print(f"Detection Error: {e}")
                detection_errors.append(str(e))
                # Use last valid results to maintain continuity
                results = self.last_results.copy()

            # --- Check for Violations and Log to Database ---
            violations_detected = await self.check_and_log_violations(results, frame)

            # --- Calculate Processing Time ---
            processing_time = (time.time() - processing_start_time) * 1000
            
            # --- Calculate Confidence ---
            confidence = self.calculate_confidence(results)
            
            # --- Prepare Response ---
            response = {
                'status': 'ok',
                'gaze_direction': results.get('gaze_direction', 'Center'),
                'head_direction': results.get('head_direction', 'Looking at Screen'),
                'lip_state': results.get('lip_state', 'No Movement'),
                'mobile_detected': results.get('mobile_detected', False),
                'emotion': results.get('emotion', 'Neutral'),
                'confidence': round(confidence, 2),
                'fps': round(fps, 1),
                'processing_time': round(processing_time, 0),
                'violations_detected': violations_detected,
                'session_duration': int(time.time() - self.calibration_start_time) if self.calibration_start_time else 0,
                'frame_count': self.frame_count
            }
            
            if detection_errors:
                response['detection_errors'] = detection_errors
            
            print(f"[REAL-TIME MONITORING] Frame {self.frame_count}: {response}")
            await self.send(text_data=json.dumps(response))
            
        except Exception as e:
            print(f"Critical error in receive: {e}")
            await self.send(text_data=json.dumps({'status': 'error', 'message': str(e)}))

    async def check_and_log_violations(self, results, frame):
        """Check for violations and log them to database"""
        if isinstance(self.user, AnonymousUser):
            return []
        
        current_time = time.time()
        violations_detected = []
        
        # Check head misalignment
        if results.get('head_direction') != 'Looking at Screen':
            await self.handle_violation('head_misalignment', current_time, results['head_direction'], 0.8)
            violations_detected.append({
                'type': 'head_misalignment',
                'description': f"Head Pose: {results['head_direction']}",
                'severity': 'danger',
                'confidence': 0.8
            })
        else:
            self.violation_timers['head_misalignment'] = None
        
        # Check eye misalignment
        if results.get('gaze_direction') != 'Center':
            await self.handle_violation('eye_misalignment', current_time, results['gaze_direction'], 0.7)
            violations_detected.append({
                'type': 'eye_misalignment',
                'description': f"Eye Movement: {results['gaze_direction']}",
                'severity': 'warning',
                'confidence': 0.7
            })
        else:
            self.violation_timers['eye_misalignment'] = None
        
        # Check mobile detection
        if results.get('mobile_detected'):
            await self.handle_violation('mobile_detection', current_time, 'Mobile device detected', 0.9)
            violations_detected.append({
                'type': 'mobile_detection',
                'description': 'Mobile phone detected',
                'severity': 'danger',
                'confidence': 0.9
            })
        else:
            self.violation_timers['mobile_detection'] = None
        
        # Check lip movement
        if results.get('lip_state') != 'No Movement':
            await self.handle_violation('lip_movement', current_time, results['lip_state'], 0.6)
            violations_detected.append({
                'type': 'lip_movement',
                'description': f"Lip Movement: {results['lip_state']}",
                'severity': 'warning',
                'confidence': 0.6
            })
        else:
            self.violation_timers['lip_movement'] = None
        
        # Check emotion detection
        if results.get('emotion') not in ['Neutral', 'Happy']:
            await self.handle_violation('emotion_detection', current_time, results['emotion'], 0.7)
            violations_detected.append({
                'type': 'emotion_detection',
                'description': f"Unusual Emotion: {results['emotion']}",
                'severity': 'warning',
                'confidence': 0.7
            })
        else:
            self.violation_timers['emotion_detection'] = None
        
        return violations_detected

    async def handle_violation(self, violation_type, current_time, description, confidence):
        """Handle violation detection and logging"""
        if self.violation_timers[violation_type] is None:
            self.violation_timers[violation_type] = current_time
            self.last_violation_time[violation_type] = current_time
        else:
            if current_time - self.violation_timers[violation_type] >= self.violation_threshold:
                if violation_type not in self.last_violation_time or \
                   current_time - self.last_violation_time[violation_type] >= 10:
                    
                    await self.log_violation_to_database(violation_type, description, confidence)
                    self.last_violation_time[violation_type] = current_time

    async def log_violation_to_database(self, violation_type, description, confidence):
        """Log violation to database"""
        try:
            def create_violation():
                violation = Violation(
                    user=self.user,
                    violation_type=violation_type,
                    confidence=confidence,
                    description=description,
                    timestamp=timezone.now()
                )
                violation.save()
                
                if hasattr(self, 'active_session') and self.active_session:
                    session_event = SessionEvent(
                        session=self.active_session,
                        event_type=violation_type,
                        confidence=confidence,
                        metadata={'description': description}
                    )
                    session_event.save()
                
                return violation
            
            await sync_to_async(create_violation)()
            print(f"Logged violation to database: {violation_type} - {description}")
            
        except Exception as e:
            print(f"Error logging violation to database: {e}")

    def calculate_confidence(self, results):
        """Calculate confidence score based on detection results"""
        score = 100.0
        
        if results.get('head_direction') != 'Looking at Screen':
            score -= 25
        elif results.get('head_direction') == 'Looking at Screen':
            score += 10
        
        if results.get('gaze_direction') != 'Center':
            score -= 20
        elif results.get('gaze_direction') == 'Center':
            score += 10
        
        if results.get('mobile_detected'):
            score -= 40
        
        if results.get('lip_state') != 'No Movement':
            score -= 10
        elif results.get('lip_state') == 'No Movement':
            score += 5
        
        if results.get('emotion') not in ['Neutral', 'Happy']:
            score -= 5
        elif results.get('emotion') in ['Neutral', 'Happy']:
            score += 5
        
        return max(0, min(100, score))