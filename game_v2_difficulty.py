import cv2
from cvzone.HandTrackingModule import HandDetector
import math
import numpy as np
import cvzone
import random
import time

# Webcam
cap = cv2.VideoCapture(0)  # channel
cap.set(3, 1280)  # 3 = width
cap.set(4, 720)  # 4 = height

# Hand Detector
detector = HandDetector(detectionCon=0.8, maxHands=1)

# Find Function
# X is the raw distance y is the value in cm
x = [300, 245, 200, 170, 145, 130, 112, 103, 93, 87, 80, 75, 70, 67, 62, 59, 57]
y = [20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100]
coff = np.polyfit(x, y, 2)  # y = Ax^2 + Bx + C

# Game Variables
cx = random.randint(100, 1100)  # Random starting x position
cy = random.randint(100, 600)   # Random starting y position
color = (0, 0, 255)  # Red color for button
counter = 0
score = 0
timeStart = time.time()
totalTime = 20
circleSize = 30  # Initial circle size
difficultyLevel = 1  # Initial difficulty level

# Function to increase difficulty
def increase_difficulty(score):
    global circleSize, totalTime, difficultyLevel
    difficultyLevel = score // 5 + 1  # Increase difficulty level every 5 points
    circleSize = max(10, 30 - difficultyLevel * 2)  # Decrease circle size as difficulty increases
    totalTime = max(10, 20 - difficultyLevel)  # Reduce total time for each new round

# Loop
while True:
    success, img = cap.read()
    imgHeight, imgWidth, _ = img.shape  # Get image dimensions for centering

    if time.time() - timeStart < totalTime:

        hands, img = detector.findHands(img, draw=False)

        if hands:
            lmList = hands[0]['lmList']
            x, y, w, h = hands[0]['bbox']
            x1, y1, _ = lmList[5]  # Ignore the z value
            x2, y2, _ = lmList[17]  # Ignore the z value

            distance = int(math.sqrt((y2 - y1) ** 2 + (x2 - x1) ** 2))
            A, B, C = coff
            distanceCM = A * distance ** 2 + B * distance + C

            if distanceCM < 30:
                if x < cx < x + w and y < cy < y + h:
                    counter = 1

            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 3)  # Red bounding box
            cvzone.putTextRect(img, f'{int(distanceCM)} cm', (x + 5, y - 10), scale=2, colorT=(255, 255, 255), colorR=(0, 0, 255))  # White text with blue background

        if counter:
            counter += 1
            color = (0, 255, 0)  # Change color to green when clicked
            if counter == 3:
                cx = random.randint(100, 1100)
                cy = random.randint(100, 600)
                color = (0, 0, 255)  # Reset color to red
                score += 1
                counter = 0
                increase_difficulty(score)  # Increase difficulty as score increases

        # Draw Button
        cv2.circle(img, (cx, cy), circleSize, color, cv2.FILLED)  # Button in red/green
        cv2.circle(img, (cx, cy), 10, (255, 255, 255), cv2.FILLED)  # White center
        cv2.circle(img, (cx, cy), 20, (255, 255, 255), 2)
        cv2.circle(img, (cx, cy), circleSize, (50, 50, 50), 2)

        # Game HUD
        cvzone.putTextRect(img, f'Time: {int(totalTime - (time.time() - timeStart))}', (1000, 75), scale=3, colorT=(255, 255, 255), colorR=(0, 0, 255), offset=20)  # White text with blue background
        cvzone.putTextRect(img, f'Score: {str(score).zfill(2)}', (60, 75), scale=3, colorT=(255, 255, 255), colorR=(0, 0, 255), offset=20)  # White text with blue background
        cvzone.putTextRect(img, f'Level: {difficultyLevel}', (550, 75), scale=3, colorT=(255, 255, 255), colorR=(0, 0, 255), offset=20)  # Show current difficulty level

    else:
        # Center "Game Over" and other text based on image width and height
        gameOverText = "Game Over"
        scoreText = f'Your Score: {str(score)}'
        restartText = 'Press R to restart or Q to exit'

        # Calculate positions to center the text
        gameOverSize = cv2.getTextSize(gameOverText, cv2.FONT_HERSHEY_PLAIN, 5, 7)[0]
        scoreSize = cv2.getTextSize(scoreText, cv2.FONT_HERSHEY_PLAIN, 3, 5)[0]
        restartSize = cv2.getTextSize(restartText, cv2.FONT_HERSHEY_PLAIN, 2, 2)[0]

        gameOverX = (imgWidth - gameOverSize[0]) // 2
        scoreX = (imgWidth - scoreSize[0]) // 2
        restartX = (imgWidth - restartSize[0]) // 2

        # Game Over Text with red background and white text
        cvzone.putTextRect(img, gameOverText, (gameOverX, imgHeight // 2 - 50), scale=5, colorT=(255, 255, 255), colorR=(255, 0, 0), thickness=7)
        cvzone.putTextRect(img, scoreText, (scoreX, imgHeight // 2 + 50), scale=3, colorT=(255, 255, 255), colorR=(255, 0, 0))
        cvzone.putTextRect(img, restartText, (restartX, imgHeight // 2 + 150), scale=2, colorT=(255, 255, 255), colorR=(255, 0, 0))

    cv2.imshow("Image", img)
    key = cv2.waitKey(1)

    # Check if 'q' is pressed
    if key == ord('q'):
        break
    elif key == ord('r'):
        timeStart = time.time()
        score = 0
        cx = random.randint(100, 1100)  # Reset the circle to a random position after restart
        cy = random.randint(100, 600)
        circleSize = 30  # Reset circle size
        difficultyLevel = 1  # Reset difficulty level
        totalTime = 20  # Reset total time

# Release the webcam and close windows
cap.release()
cv2.destroyAllWindows()