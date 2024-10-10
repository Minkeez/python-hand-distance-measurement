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

# Movement Variables
speedX = random.choice([-3, 3])  # Initial X direction speed
speedY = random.choice([-3, 3])  # Initial Y direction speed

# Power-Up Variables
powerUpActive = False
powerUpType = None
powerUpStartTime = 0
powerUpDuration = 5  # Power-up effect lasts for 5 seconds
extraTimeActive = False  # Whether extra time has been activated
scoreMultiplierActive = False  # Whether the score multiplier is active
freezeTimeActive = False  # Whether the time is frozen

# Obstacle Variables
obstacleActive = False
obstacleX, obstacleY = 0, 0
obstacleSize = 40  # Size of the obstacle
obstacleColor = (0, 0, 0)  # Obstacle color (black)
obstaclePenaltyTime = 3  # Penalty duration in seconds
obstaclePenaltyStartTime = 0
canScore = True  # Whether the player is allowed to score

# Function to increase difficulty
def increase_difficulty(score):
    global circleSize, totalTime, difficultyLevel, speedX, speedY
    difficultyLevel = score // 5 + 1  # Increase difficulty level every 5 points
    circleSize = max(10, 30 - difficultyLevel * 2)  # Decrease circle size as difficulty increases
    totalTime = max(10, 20 - difficultyLevel)  # Reduce total time for each new round
    speedX = random.choice([-3, 3]) * difficultyLevel  # Increase speed based on difficulty
    speedY = random.choice([-3, 3]) * difficultyLevel  # Increase speed based on difficulty

# Function to move the circle
def move_circle():
    global cx, cy, speedX, speedY, imgWidth, imgHeight
    cx += speedX
    cy += speedY

    # Check for boundary collisions and reverse direction if necessary
    if cx - circleSize < 0 or cx + circleSize > imgWidth:
        speedX *= -1
    if cy - circleSize < 0 or cy + circleSize > imgHeight:
        speedY *= -1

# Function to spawn power-ups
def spawn_power_up():
    global powerUpActive, powerUpType, cxPowerUp, cyPowerUp, powerUpColor
    if random.randint(1, 100) <= 10:  # 10% chance to spawn a power-up
        powerUpActive = True
        cxPowerUp = random.randint(100, 1100)
        cyPowerUp = random.randint(100, 600)
        powerUpType = random.choice(['extra_time', 'score_multiplier', 'freeze_time'])
        if powerUpType == 'extra_time':
            powerUpColor = (0, 255, 0)  # Green power-up for extra time
        elif powerUpType == 'score_multiplier':
            powerUpColor = (255, 215, 0)  # Yellow power-up for score multiplier
        elif powerUpType == 'freeze_time':
            powerUpColor = (0, 0, 255)  # Blue power-up for freeze time

# Function to activate power-up effects
def activate_power_up():
    global totalTime, powerUpType, powerUpActive, powerUpStartTime, extraTimeActive, scoreMultiplierActive, freezeTimeActive
    if powerUpType == 'extra_time':
        totalTime += 10  # Add 10 seconds
        extraTimeActive = True
    elif powerUpType == 'score_multiplier':
        scoreMultiplierActive = True  # Double points for a limited time
    elif powerUpType == 'freeze_time':
        freezeTimeActive = True  # Freeze time for 5 seconds
    powerUpActive = False
    powerUpStartTime = time.time()

# Function to spawn an obstacle
def spawn_obstacle():
    global obstacleActive, obstacleX, obstacleY
    if random.randint(1, 100) <= 15:  # 15% chance to spawn an obstacle
        obstacleActive = True
        obstacleX = random.randint(100, 1100)
        obstacleY = random.randint(100, 600)

# Function to apply obstacle penalty
def apply_obstacle_penalty():
    global score, totalTime, canScore, obstaclePenaltyStartTime
    canScore = False  # Temporarily disable scoring
    obstaclePenaltyStartTime = time.time()  # Start penalty timer
    totalTime = max(0, totalTime - 5)  # Reduce game time by 5 seconds

# Loop
while True:
    success, img = cap.read()
    imgHeight, imgWidth, _ = img.shape  # Get image dimensions for centering

    # Handle freeze time power-up
    if freezeTimeActive:
        if time.time() - powerUpStartTime > powerUpDuration:
            freezeTimeActive = False  # End freeze time effect

    # Check if scoring is disabled due to obstacle penalty
    if not canScore and time.time() - obstaclePenaltyStartTime > obstaclePenaltyTime:
        canScore = True  # Re-enable scoring after penalty duration

    if not freezeTimeActive and time.time() - timeStart < totalTime:

        hands, img = detector.findHands(img, draw=False)

        # Move the circle
        move_circle()

        if hands:
            lmList = hands[0]['lmList']
            x, y, w, h = hands[0]['bbox']
            x1, y1, _ = lmList[5]  # Ignore the z value
            x2, y2, _ = lmList[17]  # Ignore the z value

            distance = int(math.sqrt((y2 - y1) ** 2 + (x2 - x1) ** 2))
            A, B, C = coff
            distanceCM = A * distance ** 2 + B * distance + C

            if distanceCM < 30:
                # Check if player clicked on the obstacle
                if obstacleActive and x < obstacleX < x + w and y < obstacleY < y + h:
                    apply_obstacle_penalty()
                    obstacleActive = False  # Remove the obstacle

                # Check if player clicked the circle and can score
                elif canScore and x < cx < x + w and y < cy < y + h:
                    counter = 1

            # Handle power-up click detection
            if powerUpActive:
                if x < cxPowerUp < x + w and y < cyPowerUp < y + h:
                    activate_power_up()

            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 3)  # Red bounding box
            cvzone.putTextRect(img, f'{int(distanceCM)} cm', (x + 5, y - 10), scale=2, colorT=(255, 255, 255), colorR=(0, 0, 255))  # White text with blue background

        if counter:
            counter += 1
            color = (0, 255, 0)  # Change color to green when clicked
            if counter == 3:
                cx = random.randint(100, 1100)
                cy = random.randint(100, 600)
                color = (0, 0, 255)  # Reset color to red
                if scoreMultiplierActive:
                    score += 2  # Double score during score multiplier
                else:
                    score += 1
                counter = 0
                increase_difficulty(score)  # Increase difficulty as score increases

        # Draw Moving Button
        cv2.circle(img, (cx, cy), circleSize, color, cv2.FILLED)  # Button in red/green
        cv2.circle(img, (cx, cy), 10, (255, 255, 255), cv2.FILLED)  # White center
        cv2.circle(img, (cx, cy), 20, (255, 255, 255), 2)
        cv2.circle(img, (cx, cy), circleSize, (50, 50, 50), 2)

        # Spawn and Draw Power-Up
        if powerUpActive:
            cv2.circle(img, (cxPowerUp, cyPowerUp), 25, powerUpColor, cv2.FILLED)  # Power-up circle

        # Spawn and Draw Obstacle
        if obstacleActive:
            cv2.circle(img, (obstacleX, obstacleY), obstacleSize, obstacleColor, cv2.FILLED)  # Obstacle circle

        # Try to spawn power-ups and obstacles randomly
        spawn_power_up()
        spawn_obstacle()

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
        speedX = random.choice([-3, 3])  # Reset speed for X
        speedY = random.choice([-3, 3])  # Reset speed for Y
        powerUpActive = False  # Reset power-up status
        scoreMultiplierActive = False
        extraTimeActive = False
        freezeTimeActive = False
        obstacleActive = False  # Reset obstacle status
        canScore = True  # Reset ability to score

# Release the webcam and close windows
cap.release()
cv2.destroyAllWindows()
