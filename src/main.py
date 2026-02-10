#!/usr/bin/env python3
"""
AI Drawing Board - Draw in the air using hand gestures!

Controls:
- Point with index finger to draw
- Two fingers up (peace sign) to move without drawing
- Open palm (all fingers up) to pause drawing
- Click on colors at the top to change color
- Click on CLEAR button to clear canvas
- Press 'c' to clear canvas
- Press 'q' to quit
- Press '+' or '-' to adjust brush size
"""

import cv2
import sys

from hand_tracker import HandTracker
from drawing import DrawingCanvas, ColorPalette


def main():
    # Initialize camera
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open camera.")
        print("Make sure your webcam is connected and not in use by another application.")
        sys.exit(1)

    # Get camera dimensions
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"Camera resolution: {width}x{height}")
    print("\n=== AI Drawing Board ===")
    print("Controls:")
    print("  - Point with index finger to draw")
    print("  - Two fingers (peace sign) to move without drawing")
    print("  - Open palm to pause drawing")
    print("  - Click colors at top to change color")
    print("  - Press 'c' to clear canvas")
    print("  - Press '+'/'-' to adjust brush size")
    print("  - Press 'q' to quit")
    print("========================\n")

    # Initialize components
    tracker = HandTracker(max_hands=1, detection_confidence=0.7, tracking_confidence=0.7)
    canvas = DrawingCanvas(width=width, height=height)
    palette = ColorPalette()

    # Selection cooldown to prevent rapid color changes
    selection_cooldown = 0

    # Set up fullscreen window
    cv2.namedWindow("AI Drawing Board", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("AI Drawing Board", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Could not read frame.")
                break

            # Flip frame horizontally for mirror effect
            frame = cv2.flip(frame, 1)

            # Detect hands
            frame = tracker.find_hands(frame, draw=True)
            
            # Get finger position
            index_pos = tracker.get_index_finger_pos(frame)

            # Determine current gesture mode
            is_drawing = tracker.is_drawing_gesture(frame)
            is_moving = tracker.is_move_gesture(frame)

            # Check for gestures and draw
            if is_drawing:
                # Check if selecting color from palette
                if selection_cooldown == 0:
                    selected_color = palette.check_color_selection(index_pos)
                    if selected_color:
                        canvas.set_color_bgr(selected_color)
                        canvas.stop_drawing()
                        selection_cooldown = 15
                    elif palette.check_clear_button(index_pos):
                        canvas.clear()
                        selection_cooldown = 15
                    else:
                        # Draw on canvas
                        canvas.draw(index_pos)
                else:
                    canvas.stop_drawing()
            elif is_moving:
                # Move mode - stop drawing stroke but show cursor
                canvas.stop_drawing()
                # Draw move cursor indicator
                if index_pos:
                    cv2.circle(frame, index_pos, 15, canvas.color, 2)
                    cv2.circle(frame, index_pos, 5, canvas.color, -1)
            else:
                # Not in drawing gesture - stop the stroke
                canvas.stop_drawing()

            # Decrease cooldown
            if selection_cooldown > 0:
                selection_cooldown -= 1

            # Overlay canvas on frame
            frame = canvas.overlay_on_frame(frame)
            
            # Draw color palette
            frame = palette.draw_palette(frame)

            # Draw current brush info
            cv2.putText(frame, f"Brush: {canvas.thickness}px", (10, height - 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, canvas.color, 2)

            # Draw gesture indicator
            if is_drawing:
                cv2.circle(frame, (width - 30, 30), 15, (0, 255, 0), -1)
                cv2.putText(frame, "Drawing", (width - 100, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            elif is_moving:
                cv2.circle(frame, (width - 30, 30), 15, (255, 255, 0), -1)
                cv2.putText(frame, "Moving", (width - 95, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
            else:
                cv2.circle(frame, (width - 30, 30), 15, (0, 0, 255), -1)
                cv2.putText(frame, "Paused", (width - 90, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

            # Show frame
            cv2.imshow("AI Drawing Board", frame)

            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('c'):
                canvas.clear()
            elif key == ord('+') or key == ord('='):
                canvas.set_thickness(canvas.thickness + 2)
            elif key == ord('-') or key == ord('_'):
                canvas.set_thickness(canvas.thickness - 2)

    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        # Cleanup
        tracker.release()
        cap.release()
        cv2.destroyAllWindows()
        print("Application closed.")


if __name__ == "__main__":
    main()
