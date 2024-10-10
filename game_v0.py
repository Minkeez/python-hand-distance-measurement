import cv2
from cvzone.HandTrackingModule import HandDetector
import math
import numpy as np
import cvzone
import random
import time

# Webcam
cap = cv2.VideoCapture(0) # channel
cap.set(3, 1280) # 3 = width
cap.set(4, 720) # 4 = height

# Hand Detector
detector = HandDetector(detectionCon=0.8, maxHands=1)

# Find Function
# X us the raw distance y is the value in cm
x = [300, 245, 200, 170, 145, 130, 112, 103, 93, 87, 80, 75, 70, 67, 62, 59, 57]
y = [20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100]
coff = np.polyfit(x, y, 2) # y = Ax^2 + Bx + C

# Game Variables
cx, cy = 250, 250
color = (255, 0, 255)
counter = 0
score = 0
timeStart = time.time()
totalTime = 2

# Loop
while True:
    success, img = cap.read()
    if time.time() - timeStart < totalTime:
        
        hands, img = detector.findHands(img, draw=False)
        
        if hands:
            lmList = hands[0]['lmList']
            x, y, w, h = hands[0]['bbox']
            x1, y1, _ = lmList[5] # Ignore the z value
            x2, y2, _ = lmList[17] # Ignore the z value
            
            distance = int(math.sqrt((y2-y1)**2 + (x2-x1)**2))
            A, B, C = coff
            distanceCM = A*distance**2 + B*distance + C
            
            if distanceCM < 30:
                if x < cx < x+w and y < cy < y+h:
                    counter = 1
            
            cv2.rectangle(img, (x,y), (x+w,y+h), (255,0,255), 3)
            cvzone.putTextRect(img, f'{int(distanceCM)} cm', (x+5,y-10))
        
        if counter:
            counter += 1
            color = (0, 255, 0)
            if counter == 3:
                cx = random.randint(100, 1100)
                cy = random.randint(100, 600)
                color = (255, 0, 255)
                score += 1
                counter = 0
        
        # Draw Button
        cv2.circle(img, (cx,cy), 30, color, cv2.FILLED)
        cv2.circle(img, (cx,cy), 10, (255,255,255), cv2.FILLED)
        cv2.circle(img, (cx,cy), 20, (255,255,255), 2)
        cv2.circle(img, (cx,cy), 30, (50,50,50), 2)
        
        # Game HUD
        cvzone.putTextRect(img, f'Time: {int(totalTime-(time.time()-timeStart))}', (1000,75), scale=3, offset=20)
        cvzone.putTextRect(img, f'Score: {str(score).zfill(2)}', (60,75), scale=3, offset=20)
    
    else:
        cvzone.putTextRect(img, 'Game Over', (400,300), scale=5, offset=30, thickness=7)
        cvzone.putTextRect(img, f'Your Score: {str(score)}', (450,400), scale=3, offset=20)
        cvzone.putTextRect(img, 'Press R to restart or Q to exit', (350,475), scale=2, offset=10)
    
    cv2.imshow("Image", img)
    key = cv2.waitKey(1)
    
    
    # Check if 'q' is pressed
    if key == ord('q'):
        break
    elif key == ord('r'):
        timeStart = time.time()
        score = 0
    
# Release the webcam and close windows
cap.release()
cv2.destroyAllWindows()