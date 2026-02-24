import cv2
import mediapipe as mp
import threading
import os
import math
import time

# --- ROBUST VOICE FUNCTION ---
def speak_text(text):
    def run():
        print(f"🎤 Speaking: {text}")
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty('rate', 150)
            engine.say(text)
            engine.runAndWait()
        except:
            try:
                safe_text = text.replace("'", "")
                cmd = f'powershell -Command "Add-Type –AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'{safe_text}\');"'
                os.system(cmd)
            except:
                pass
    threading.Thread(target=run).start()

# --- NUMBER LOGIC (0-9) ---
def get_digit(lm):
    tips = [8, 12, 16, 20]
    pips = [6, 10, 14, 18] 
    
    # Check 4 main fingers (Index, Middle, Ring, Pinky)
    f_up = []
    for t, p in zip(tips, pips):
        f_up.append(lm[t].y < lm[p].y)
    
    up_count = f_up.count(True)
    palm_size = math.sqrt((lm[5].x - lm[17].x)**2 + (lm[5].y - lm[17].y)**2)
    
    # Thumb Logic
    dx = lm[4].x - lm[2].x
    dy = lm[4].y - lm[2].y
    thumb_out = math.sqrt(dx**2 + dy**2) > palm_size * 0.5

    # User's Specific Number Rules
    if up_count == 0 and not thumb_out: return 0             # Feat/Fist = 0
    if up_count == 0 and thumb_out: return 1                 # Thumb only = 1
    if up_count == 1 and f_up[0]: return 1                   # Index only = 1 (Fallback)
    if up_count == 1 and f_up[3]: return 6                   # Small/Pinky only = 6
    if up_count == 2: return 2                               # Two fingers = 2
    if up_count == 3: return 3                               # Three fingers = 3
    if up_count == 4 and not thumb_out: return 4             # Four fingers = 4
    if up_count == 4 and thumb_out: return 5                 # All fingers = 5
    
    return None

# --- NORMAL GESTURE LOGIC ---
def get_normal_gesture(lm, actual_hand, up_count, thumb_out, f_up, dx, dy):
    if actual_hand == "Right": 
        if up_count == 0 and not thumb_out: return "Emergency" 
        if up_count == 0 and thumb_out:
            if abs(dy) > abs(dx):
                if dy < 0: return "OK"
                else: return "Bad"
            
        if up_count == 4 and not thumb_out: return "B"
        if up_count == 4 and thumb_out: return "Hello" 
        if up_count == 4 and not f_up[0] and f_up[1] and f_up[2] and f_up[3]: return "No / Stop" # Fingers glued
        if up_count == 3 and not f_up[0] and f_up[1] and f_up[2] and f_up[3]: return "Super"
        return "Searching..."

    elif actual_hand == "Left":
        if up_count == 0 and thumb_out: 
            if abs(dx) > abs(dy): 
                if dx > 0: return "Food"
                else: return "Washroom"
            else: 
                if dy < 0: return "Water"
                else: return "Sleep" 
        return "Searching..."
    return "Searching..."

# Setup MediaPipe
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7, min_tracking_confidence=0.7)
cap = cv2.VideoCapture(0)

current_sentence = []
pTime = 0 
current_mode = "NORMAL" # Can be "NORMAL" or "NUMBERS"
last_mode_switch = 0

print("------------------------------------------------")
print("  FINAL SIGN TRANSLATOR (WITH NUMBERS MODE)")
print("  SPACE: Add | B: Backspace | C: Clear | S: Save")
print("------------------------------------------------")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break
    
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    cTime = time.time()
    fps = 1 / (cTime - pTime) if (cTime - pTime) > 0 else 0
    pTime = cTime

    detected_words = []
    
    left_hand_lm = None
    right_hand_lm = None

    if results.multi_hand_landmarks and results.multi_handedness:
        for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
            actual_hand = handedness.classification[0].label 
            
            # Save landmarks for number logic
            if actual_hand == "Left": left_hand_lm = hand_landmarks.landmark
            if actual_hand == "Right": right_hand_lm = hand_landmarks.landmark

            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            # Bounding Box
            x_min, y_min = w, h
            x_max, y_max = 0, 0
            for lm in hand_landmarks.landmark:
                x, y = int(lm.x * w), int(lm.y * h)
                x_min, y_min = min(x_min, x), min(y_min, y)
                x_max, y_max = max(x_max, x), max(y_max, y)
            
            cv2.rectangle(frame, (x_min - 20, y_min - 20), (x_max + 20, y_max + 20), (255, 165, 0), 2)
            cv2.putText(frame, f"{actual_hand} Hand", (x_min - 20, y_min - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 165, 0), 2)
            
            # Extract basic data for gestures
            tips, pips = [8, 12, 16, 20], [6, 10, 14, 18]
            f_up = [hand_landmarks.landmark[t].y < hand_landmarks.landmark[p].y for t, p in zip(tips, pips)]
            up_count = f_up.count(True)
            palm_size = math.sqrt((hand_landmarks.landmark[5].x - hand_landmarks.landmark[17].x)**2 + (hand_landmarks.landmark[5].y - hand_landmarks.landmark[17].y)**2)
            dx = hand_landmarks.landmark[4].x - hand_landmarks.landmark[2].x
            dy = hand_landmarks.landmark[4].y - hand_landmarks.landmark[2].y
            thumb_out = math.sqrt(dx**2 + dy**2) > palm_size * 0.5
            
            # --- NORMAL MODE LOGIC ---
            if current_mode == "NORMAL":
                word = get_normal_gesture(hand_landmarks.landmark, actual_hand, up_count, thumb_out, f_up, dx, dy)
                if word != "Searching...":
                    detected_words.append(word)

    # --- MODE SWITCH LOGIC (Double Fist) ---
    if left_hand_lm and right_hand_lm:
        left_digit = get_digit(left_hand_lm)
        right_digit = get_digit(right_hand_lm)
        
        # If BOTH hands are 0 (Feat/Fist) -> Switch Mode!
        if left_digit == 0 and right_digit == 0:
            if cTime - last_mode_switch > 2.0: # 2-second cooldown so it doesn't flicker
                current_mode = "NUMBERS" if current_mode == "NORMAL" else "NORMAL"
                last_mode_switch = cTime
                speak_text(f"{current_mode} Mode Activated")

    # --- NUMBERS MODE LOGIC ---
    word_now = "Searching..."
    if current_mode == "NUMBERS":
        l_val = get_digit(left_hand_lm) if left_hand_lm else None
        r_val = get_digit(right_hand_lm) if right_hand_lm else None

        if l_val is not None and r_val is not None:
            word_now = str(l_val * 10 + r_val) # Tens + Units (e.g. 1 and 6 = 16)
        elif l_val is not None:
            word_now = str(l_val)
        elif r_val is not None:
            word_now = str(r_val)
            
    # --- NORMAL MODE TEXT BINDING ---
    elif current_mode == "NORMAL":
        word_now = " + ".join(detected_words) if detected_words else "Searching..."

    # ================= UI DESIGN =================
    
    # 1. Top Bar (Mode Indicator & Current Sign)
    bar_color = (100, 0, 0) if current_mode == "NUMBERS" else (40, 40, 40)
    cv2.rectangle(frame, (0, 0), (w, 70), bar_color, -1)
    
    mode_text = "[NUMBERS]" if current_mode == "NUMBERS" else "[NORMAL]"
    cv2.putText(frame, mode_text, (20, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    
    text_color = (0, 255, 0) if word_now != "Searching..." else (200, 200, 200)
    cv2.putText(frame, f"Sign: {word_now}", (20, 55), cv2.FONT_HERSHEY_SIMPLEX, 1, text_color, 2)
    cv2.putText(frame, f"FPS: {int(fps)}", (w - 120, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    
    # 2. Bottom Bar (Sentence)
    cv2.rectangle(frame, (0, h-80), (w, h), (0, 0, 0), -1)
    sentence_str = " ".join(current_sentence)
    cv2.putText(frame, f"Text: {sentence_str}", (20, h-30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    cv2.imshow('Sign Language AI - Master Edition', frame)

    # Keyboard Controls
    key = cv2.waitKey(1)
    if key & 0xFF == ord('q'): break
    
    elif key & 0xFF == 32: # SPACE
        if word_now != "Searching...":
            current_sentence.append(word_now)
            speak_text(word_now)

    elif key & 0xFF == ord('b'): # BACKSPACE
        if current_sentence: current_sentence.pop()

    elif key & 0xFF == ord('c'): # CLEAR
        current_sentence = []
        
    elif key & 0xFF == ord('s'): # SAVE
        if current_sentence:
            with open("conversation_log.txt", "a") as file:
                file.write(sentence_str + "\n")
            print("💾 Sentence saved to conversation_log.txt")
            speak_text("Sentence Saved")

cap.release()
cv2.destroyAllWindows()