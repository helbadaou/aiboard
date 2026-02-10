import cv2
import numpy as np


class DrawingCanvas:
    def __init__(self, width=640, height=480):
        self.width = width
        self.height = height
        self.canvas = np.zeros((height, width, 3), dtype=np.uint8)
        self.prev_point = None
        self.color = (0, 255, 0)  # Green default
        self.thickness = 5
        self.colors = {
            'green': (0, 255, 0),
            'red': (0, 0, 255),
            'blue': (255, 0, 0),
            'yellow': (0, 255, 255),
            'white': (255, 255, 255),
            'purple': (255, 0, 255),
            'orange': (0, 165, 255)
        }

    def draw(self, point):
        """Draw a line from previous point to current point."""
        if point is None:
            self.prev_point = None
            return

        if self.prev_point is not None:
            cv2.line(self.canvas, self.prev_point, point, self.color, self.thickness)
        
        self.prev_point = point

    def stop_drawing(self):
        """Stop the current drawing stroke."""
        self.prev_point = None

    def clear(self):
        """Clear the canvas."""
        self.canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        self.prev_point = None

    def set_color(self, color_name):
        """Set drawing color by name."""
        if color_name in self.colors:
            self.color = self.colors[color_name]

    def set_color_bgr(self, bgr_color):
        """Set drawing color by BGR tuple."""
        self.color = bgr_color

    def set_thickness(self, thickness):
        """Set line thickness."""
        self.thickness = max(1, min(thickness, 50))

    def get_canvas(self):
        """Get the current canvas."""
        return self.canvas.copy()

    def overlay_on_frame(self, frame):
        """Overlay the canvas on a video frame."""
        # Ensure frame and canvas have the same size
        if frame.shape[:2] != (self.height, self.width):
            frame = cv2.resize(frame, (self.width, self.height))
        
        # Create mask where canvas has drawings
        gray = cv2.cvtColor(self.canvas, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
        mask_inv = cv2.bitwise_not(mask)
        
        # Black out the drawing area in frame
        frame_bg = cv2.bitwise_and(frame, frame, mask=mask_inv)
        
        # Take only drawing from canvas
        canvas_fg = cv2.bitwise_and(self.canvas, self.canvas, mask=mask)
        
        # Combine
        result = cv2.add(frame_bg, canvas_fg)
        return result


class ColorPalette:
    def __init__(self, x=10, y=10, size=40, spacing=10):
        self.x = x
        self.y = y
        self.size = size
        self.spacing = spacing
        self.colors = [
            ('green', (0, 255, 0)),
            ('red', (0, 0, 255)),
            ('blue', (255, 0, 0)),
            ('yellow', (0, 255, 255)),
            ('white', (255, 255, 255)),
            ('purple', (255, 0, 255)),
            ('orange', (0, 165, 255))
        ]
        self.clear_button = None

    def draw_palette(self, frame):
        """Draw color palette on frame."""
        for i, (name, color) in enumerate(self.colors):
            x1 = self.x + i * (self.size + self.spacing)
            y1 = self.y
            x2 = x1 + self.size
            y2 = y1 + self.size
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, -1)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 2)

        # Draw clear button
        clear_x = self.x + len(self.colors) * (self.size + self.spacing)
        self.clear_button = (clear_x, self.y, clear_x + self.size * 2, self.y + self.size)
        cv2.rectangle(frame, (clear_x, self.y), (clear_x + self.size * 2, self.y + self.size), (128, 128, 128), -1)
        cv2.putText(frame, "CLEAR", (clear_x + 5, self.y + 28), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        return frame

    def check_color_selection(self, point):
        """Check if point is on a color in the palette."""
        if point is None:
            return None

        x, y = point
        
        for i, (name, color) in enumerate(self.colors):
            x1 = self.x + i * (self.size + self.spacing)
            y1 = self.y
            x2 = x1 + self.size
            y2 = y1 + self.size
            
            if x1 <= x <= x2 and y1 <= y <= y2:
                return color

        return None

    def check_clear_button(self, point):
        """Check if point is on the clear button."""
        if point is None or self.clear_button is None:
            return False

        x, y = point
        x1, y1, x2, y2 = self.clear_button
        
        return x1 <= x <= x2 and y1 <= y <= y2
