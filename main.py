import cv2
import mediapipe as mp

# 1. Setup MediaPipe (The "Brain" for hands)
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Initialize the Hands model
# min_detection_confidence: How sure the AI must be to say "That's a hand!"
# min_tracking_confidence: How sure it must be to keep tracking it.
hands = mp_hands.Hands(
    max_num_hands=2,  # Track up to 2 hands
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)

# 2. Setup Camera (The "Eyes")
cap = cv2.VideoCapture(0) # 0 is usually the default webcam

print("Press 'q' to quit the program.")

while cap.isOpened():
    success, image = cap.read()
    if not success:
        print("Ignoring empty camera frame.")
        continue

    # 3. Process the Image
    # Flip the image horizontally for a later selfie-view display
    image = cv2.flip(image, 1)
    
    # Convert the BGR image to RGB (MediaPipe needs RGB)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # The Magic: Detect the hands
    results = hands.process(image_rgb)

    # 4. Draw the Landmarks (The "Skeleton")
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Draw the connections (dots and lines) on the image
            mp_drawing.draw_landmarks(
                image, 
                hand_landmarks, 
                mp_hands.HAND_CONNECTIONS)
            
            # OPTIONAL: Get the coordinates of the Index Finger Tip (Point 8)
            # This is how we will trigger actions later!
            h, w, c = image.shape
            cx, cy = int(hand_landmarks.landmark[8].x * w), int(hand_landmarks.landmark[8].y * h)
            cv2.circle(image, (cx, cy), 15, (255, 0, 255), cv2.FILLED)

    # 5. Show the Output
    cv2.imshow('Sign Language AI - Test', image)

    # Break loop if 'q' is pressed
    if cv2.waitKey(5) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()