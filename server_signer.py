import base64
import cv2
import numpy as np
import mediapipe as mp
import math
import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# --- EXTRACTED LOGIC FROM SIGNER.PY ---

def get_digit(lm):
    tips = [8, 12, 16, 20]
    pips = [6, 10, 14, 18] 
    f_up = []
    for t, p in zip(tips, pips):
        f_up.append(lm[t].y < lm[p].y)
    
    up_count = f_up.count(True)
    palm_size = math.sqrt((lm[5].x - lm[17].x)**2 + (lm[5].y - lm[17].y)**2)
    dx = lm[4].x - lm[2].x
    dy = lm[4].y - lm[2].y
    thumb_out = math.sqrt(dx**2 + dy**2) > palm_size * 0.5

    if up_count == 0 and not thumb_out: return 0
    if up_count == 0 and thumb_out: return 1
    if up_count == 1 and f_up[0]: return 1
    if up_count == 1 and f_up[3]: return 6
    if up_count == 2: return 2
    if up_count == 3: return 3
    if up_count == 4 and not thumb_out: return 4
    if up_count == 4 and thumb_out: return 5
    return None

def get_normal_gesture(lm, actual_hand, up_count, thumb_out, f_up, dx, dy):
    if actual_hand == "Right": 
        if up_count == 0 and not thumb_out: return "Emergency" 
        if up_count == 0 and thumb_out:
            if abs(dy) > abs(dx):
                if dy < 0: return "OK"
                else: return "Bad"
        if up_count == 4 and not thumb_out: return "B"
        if up_count == 4 and thumb_out: return "Hello" 
        if up_count == 3 and not f_up[0] and f_up[1] and f_up[2] and f_up[3]: return "Super"
        # Adjusted "No / Stop" for easier detection
        if up_count == 4 and not f_up[0]: return "No / Stop"
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

# --- FASTAPI WRAPPER ---

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7, min_tracking_confidence=0.7)

print("🚀 FastAPI Sign Language Backend is initializing...")

@app.get("/")
async def root():
    return {"status": "ok", "message": "Sign Language Backend is running"}

@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    current_mode = "NORMAL"
    
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            if msg_type == "MODE":
                current_mode = data.get("mode", "NORMAL")
                continue
            
            if msg_type == "LANGUAGE":
                continue # Logic in signer.py is language-agnostic strings
            
            if msg_type == "IMAGE":
                img_data = data.get("image")
                if not img_data: continue
                
                # Decode image
                format, imgstr = img_data.split(';base64,')
                nparr = np.frombuffer(base64.b64decode(imgstr), np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                frame = cv2.flip(frame, 1)
                
                # Process landmarks
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = hands.process(rgb_frame)
                
                detected_words = []
                left_lm = None
                right_lm = None
                
                if results.multi_hand_landmarks and results.multi_handedness:
                    for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                        label = handedness.classification[0].label # "Left" or "Right"
                        lm = hand_landmarks.landmark
                        
                        if label == "Left": left_lm = lm
                        if label == "Right": right_lm = lm
                        
                        # Draw landmarks for visual feedback
                        mp.solutions.drawing_utils.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                        # Basic data for rules
                        tips, pips = [8, 12, 16, 20], [6, 10, 14, 18]
                        f_up = [lm[t].y < lm[p].y for t, p in zip(tips, pips)]
                        up_count = f_up.count(True)
                        palm_size = math.sqrt((lm[5].x - lm[17].x)**2 + (lm[5].y - lm[17].y)**2)
                        dx = lm[4].x - lm[2].x
                        dy = lm[4].y - lm[2].y
                        thumb_out = math.sqrt(dx**2 + dy**2) > palm_size * 0.5
                        
                        if current_mode == "NORMAL":
                            word = get_normal_gesture(lm, label, up_count, thumb_out, f_up, dx, dy)
                            if word != "Searching...":
                                detected_words.append(word)
                
                # Encode feedback frame
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
                feedback_img = base64.b64encode(buffer).decode('utf-8')
                
                word_now = None
                if current_mode == "NUMBERS":
                    l_val = get_digit(left_lm) if left_lm else None
                    r_val = get_digit(right_lm) if right_lm else None
                    if l_val is not None and r_val is not None:
                        word_now = str(l_val * 10 + r_val)
                    elif l_val is not None:
                        word_now = str(l_val)
                    elif r_val is not None:
                        word_now = str(r_val)
                else:
                    word_now = " + ".join(detected_words) if detected_words else None
                
                if word_now:
                    await websocket.send_json({"type": "WORD", "text": word_now, "image": feedback_img})
                else:
                    await websocket.send_json({"type": "FEEDBACK", "image": feedback_img})
                    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 3005))
    host = os.environ.get("HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)
