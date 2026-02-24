import cv2
import mediapipe as mp
from google import genai 
import threading
import time
import os
import pyttsx3
import math

# ==========================================
# PASTE YOUR NEW API KEY HERE
API_KEY = "AIzaSyDtpokfjmn1fhF3iTA_rlEp4x61wvwcyqU" 
# ==========================================

client = genai.Client(api_key=API_KEY)

def speak_text(text):
    def run():
        try:
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
        except: pass
    threading.Thread(target=run).start()

# --- OFFLINE MATH LOGIC (Backup) ---
def get_offline_gesture(lm):
    # Simple finger counting logic
    tips = [8, 12, 16, 20]
    knuckles = [6, 10, 14, 18]
    up_count = 0
    for t, k in zip(tips, knuckles):
        if lm[t].y < lm[k].y: up_count += 1
    
    # Thumb check
    thumb_open = math.sqrt((lm[4].x - lm[17].x)**2 + (lm[4].y - lm[17].y)**2) > \
                 math.sqrt((lm[3].x - lm[17].x)**2 + (lm[3].y - lm[17].y)**2)
    if thumb_open: up_count += 1

    if up_count == 5: return "Hello (Offline)"
    if up_count == 0: return "Fist (Offline)"
    if up_count == 2: return "Peace (Offline)"
    return f"{up_count} Fingers"

# Setup Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)

cap = cv2.VideoCapture(0)
last_response = "READY"
last_api_call = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    # UI
    cv2.rectangle(frame, (0, 0), (640, 60), (0, 0, 0), -1)
    cv2.putText(frame, last_response, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.imshow('Sign Language AI', frame)

    key = cv2.waitKey(1)
    if key & 0xFF == ord('q'): break
    
    elif key & 0xFF == 32: # SPACE
        if results.multi_hand_landmarks:
            last_response = "Thinking..."
            lm = results.multi_hand_landmarks[0].landmark
            
            # Try AI first
            try:
                # Use the 'latest' stable alias
                response = client.models.generate_content(
                    model="gemini-1.5-flash-latest", 
                    contents=f"Identify sign: {[f'({l.x:.2f},{l.y:.2f})' for l in lm]}"
                )
                res = response.text.strip()
                last_response = f"AI: {res}"
                speak_text(res)
            except Exception as e:
                # If AI fails, use Math backup immediately
                print(f"AI Failed ({e}), using Offline Mode...")
                res = get_offline_gesture(lm)
                last_response = f"Local: {res}"
                speak_text(res)
        else:
            last_response = "No hand detected"

cap.release()
cv2.destroyAllWindows()