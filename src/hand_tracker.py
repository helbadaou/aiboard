import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import os


class HandTracker:
    def __init__(self, max_hands=1, detection_confidence=0.7, tracking_confidence=0.7):
        # Get the model path relative to this file
        model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'hand_landmarker.task')
        
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_hands=max_hands,
            min_hand_detection_confidence=detection_confidence,
            min_hand_presence_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence
        )
        self.detector = vision.HandLandmarker.create_from_options(options)
        self.results = None
        self.hand_landmarks = None

    def find_hands(self, frame, draw=True):
        """Detect hands in the frame and optionally draw landmarks."""
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        self.results = self.detector.detect(mp_image)
        self.hand_landmarks = self.results.hand_landmarks
        
        if self.hand_landmarks and draw:
            for landmarks in self.hand_landmarks:
                self._draw_landmarks(frame, landmarks)
        
        return frame

    def _draw_landmarks(self, frame, landmarks):
        """Draw hand landmarks on the frame."""
        h, w, _ = frame.shape
        
        # Convert normalized landmarks to pixel coordinates
        points = []
        for lm in landmarks:
            x = int(lm.x * w)
            y = int(lm.y * h)
            points.append((x, y))
            cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
        
        # Draw connections
        connections = [
            (0, 1), (1, 2), (2, 3), (3, 4),  # Thumb
            (0, 5), (5, 6), (6, 7), (7, 8),  # Index
            (0, 9), (9, 10), (10, 11), (11, 12),  # Middle
            (0, 13), (13, 14), (14, 15), (15, 16),  # Ring
            (0, 17), (17, 18), (18, 19), (19, 20),  # Pinky
            (5, 9), (9, 13), (13, 17)  # Palm
        ]
        
        for start, end in connections:
            if start < len(points) and end < len(points):
                cv2.line(frame, points[start], points[end], (0, 200, 0), 2)

    def get_finger_positions(self, frame):
        """Get positions of all finger tips."""
        positions = {}
        h, w, _ = frame.shape

        if self.hand_landmarks and len(self.hand_landmarks) > 0:
            landmarks = self.hand_landmarks[0]
            
            # Finger tip landmarks: 4=thumb, 8=index, 12=middle, 16=ring, 20=pinky
            finger_tips = {
                'thumb': 4,
                'index': 8,
                'middle': 12,
                'ring': 16,
                'pinky': 20
            }
            
            for finger, landmark_id in finger_tips.items():
                lm = landmarks[landmark_id]
                positions[finger] = (int(lm.x * w), int(lm.y * h))

        return positions

    def get_index_finger_pos(self, frame):
        """Get index finger tip position."""
        positions = self.get_finger_positions(frame)
        return positions.get('index', None)

    def is_drawing_gesture(self, frame):
        """Check if index finger is up and other fingers are down (drawing gesture)."""
        if not self.hand_landmarks or len(self.hand_landmarks) == 0:
            return False

        landmarks = self.hand_landmarks[0]
        
        # Get y coordinates (lower y = higher on screen)
        index_tip = landmarks[8].y
        index_pip = landmarks[6].y
        
        middle_tip = landmarks[12].y
        middle_pip = landmarks[10].y
        
        ring_tip = landmarks[16].y
        ring_pip = landmarks[14].y
        
        pinky_tip = landmarks[20].y
        pinky_pip = landmarks[18].y

        # Index finger up, others down
        index_up = index_tip < index_pip
        middle_down = middle_tip > middle_pip
        ring_down = ring_tip > ring_pip
        pinky_down = pinky_tip > pinky_pip

        return index_up and middle_down and ring_down and pinky_down

    def is_move_gesture(self, frame):
        """Check if index and middle fingers are up (move/navigate gesture - peace sign)."""
        if not self.hand_landmarks or len(self.hand_landmarks) == 0:
            return False

        landmarks = self.hand_landmarks[0]
        
        # Get y coordinates (lower y = higher on screen)
        index_tip = landmarks[8].y
        index_pip = landmarks[6].y
        
        middle_tip = landmarks[12].y
        middle_pip = landmarks[10].y
        
        ring_tip = landmarks[16].y
        ring_pip = landmarks[14].y
        
        pinky_tip = landmarks[20].y
        pinky_pip = landmarks[18].y

        # Index and middle fingers up, ring and pinky down
        index_up = index_tip < index_pip
        middle_up = middle_tip < middle_pip
        ring_down = ring_tip > ring_pip
        pinky_down = pinky_tip > pinky_pip

        return index_up and middle_up and ring_down and pinky_down

    def is_erase_gesture(self, frame):
        """Check if all fingers are up (erase/clear gesture)."""
        if not self.hand_landmarks or len(self.hand_landmarks) == 0:
            return False

        landmarks = self.hand_landmarks[0]
        
        # Check if all fingers are extended
        fingers_up = 0
        
        # Thumb (comparing x for thumb)
        if landmarks[4].x < landmarks[3].x:  # For right hand
            fingers_up += 1
            
        # Other fingers (comparing y)
        tips = [8, 12, 16, 20]
        pips = [6, 10, 14, 18]
        
        for tip, pip in zip(tips, pips):
            if landmarks[tip].y < landmarks[pip].y:
                fingers_up += 1

        return fingers_up >= 4

    def release(self):
        """Release resources."""
        self.detector.close()
