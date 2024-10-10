import cv2
from cvzone.HandTrackingModule import HandDetector
import math
import numpy as np
import cvzone
import random
import time
import pygame  # For sound effects

# Initialize sound system (pygame)
pygame.mixer.init()

# Load sound effects
click_sound = pygame.mixer.Sound('click.wav')  # Example sound for clicking the circle
powerup_sound = pygame.mixer.Sound('powerup.mp3')  # Example sound for collecting power-ups
obstacle_hit_sound = pygame.mixer.Sound('obstacle_hit.wav')  # Example sound for hitting obstacles
level_up_sound = pygame.mixer.Sound('level_up.mp3')  # Example sound for leveling up
background_music = 'background_music.mp3'

# Start background music (looped)
pygame.mixer.music.load(background_music)
pygame.mixer.music.play(-1)

# Webcam
cap = cv2.VideoCapture(0)
cap.set(3, 1280)  # Width
cap.set(4, 720)  # Height

# Hand Detector
detector = HandDetector(detectionCon=0.8, maxHands=1)

# Find Function
x = [300, 245, 200, 170, 145, 130, 112, 103, 93, 87, 80, 75, 70, 67, 62, 59, 57]
y = [20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100]
coff = np.polyfit(x, y, 2)  # y = Ax^2 + Bx + C

# Game Variables
cx = random.randint(100, 1100)
cy = random.randint(100, 600)
color = (0, 0, 255)
counter = 0
score = 0
timeStart = time.time()
totalTime = 20
circleSize = 30
difficultyLevel = 1
comboCounter = 0  # Combo system

# Movement Variables
speedX = random.choice([-3, 3])
speedY = random.choice([-3, 3])

# Power-Up Variables
powerUpActive = False
powerUpType = None
powerUpStartTime = 0
powerUpDuration = 5
extraTimeActive = False
scoreMultiplierActive = False
freezeTimeActive = False

# Obstacle Variables
obstacleActive = False
obstacleX, obstacleY = 0, 0
obstacleSize = 40
obstaclePenaltyTime = 3
obstaclePenaltyStartTime = 0
canScore = True

# Achievements System
achievements = []

# Function to increase difficulty
def increase_difficulty(score):
    global circleSize, totalTime, difficultyLevel, speedX, speedY
    difficultyLevel = score // 5 + 1
    circleSize = max(10, 30 - difficultyLevel * 2)
    totalTime = max(10, 20 - difficultyLevel)
    speedX = random.choice([-3, 3]) * difficultyLevel
    speedY = random.choice([-3, 3]) * difficultyLevel
    level_up_sound.play()  # Play sound when leveling up

# Function to move the circle
def move_circle():
    global cx, cy, speedX, speedY, imgWidth, imgHeight
    cx += speedX
    cy += speedY

    if cx - circleSize < 0 or cx + circleSize > imgWidth:
        speedX *= -1
    if cy - circleSize < 0 or cy + circleSize > imgHeight:
        speedY *= -1

# Function to spawn power-ups
def spawn_power_up():
    global powerUpActive, powerUpType, cxPowerUp, cyPowerUp, powerUpColor
    if random.randint(1, 100) <= 10:
        powerUpActive = True
        cxPowerUp = random.randint(100, 1100)
        cyPowerUp = random.randint(100, 600)
        powerUpType = random.choice(['extra_time', 'score_multiplier', 'freeze_time'])
        powerup_sound.play()  # Play power-up spawn sound
        if powerUpType == 'extra_time':
            powerUpColor = (0, 255, 0)
        elif powerUpType == 'score_multiplier':
            powerUpColor = (255, 215, 0)
        elif powerUpType == 'freeze_time':
            powerUpColor = (0, 0, 255)

# Function to activate power-up effects
def activate_power_up():
    global totalTime, powerUpType, powerUpActive, powerUpStartTime, extraTimeActive, scoreMultiplierActive, freezeTimeActive
    if powerUpType == 'extra_time':
        totalTime += 10
        extraTimeActive = True
    elif powerUpType == 'score_multiplier':
        scoreMultiplierActive = True
    elif powerUpType == 'freeze_time':
        freezeTimeActive = True
    powerUpActive = False
    powerUpStartTime = time.time()

# Function to spawn an obstacle
def spawn_obstacle():
    global obstacleActive, obstacleX, obstacleY
    if random.randint(1, 100) <= 15:
        obstacleActive = True
        obstacleX = random.randint(100, 1100)
        obstacleY = random.randint(100, 600)

# Function to apply obstacle penalty
def apply_obstacle_penalty():
    global score, totalTime, canScore, obstaclePenaltyStartTime
    canScore = False
    obstacle_hit_sound.play()  # Play sound when hitting obstacle
    obstaclePenaltyStartTime = time.time()
    totalTime = max(0, totalTime - 5)

# Combo System
def handle_combo(success):
    global comboCounter
    if success:
        comboCounter += 1
        if comboCounter % 5 == 0:  # Every 5 successful clicks, grant bonus
            print(f"Combo Bonus! +2 points!")
            return 2  # Bonus points for combo
    else:
        comboCounter = 0  # Reset combo if missed
    return 0

# Function to show achievements
def show_achievements():
    for achievement in achievements:
        print(f"Achievement Unlocked: {achievement}")

# Loop
while True:
    success, img = cap.read()
    imgHeight, imgWidth, _ = img.shape

    # Handle freeze time power-up
    if freezeTimeActive:
        if time.time() - powerUpStartTime > powerUpDuration:
            freezeTimeActive = False

    if not canScore and time.time() - obstaclePenaltyStartTime > obstaclePenaltyTime:
        canScore = True

    if not freezeTimeActive and time.time() - timeStart < totalTime:
        hands, img = detector.findHands(img, draw=False)
        move_circle()

        if hands:
            lmList = hands[0]['lmList']
            x, y, w, h = hands[0]['bbox']
            x1, y1, _ = lmList[5]
            x2, y2, _ = lmList[17]

            distance = int(math.sqrt((y2 - y1) ** 2 + (x2 - x1) ** 2))
            A, B, C = coff
            distanceCM = A * distance ** 2 + B * distance + C

            if distanceCM < 30:
                if obstacleActive and x < obstacleX < x + w and y < obstacleY < y + h:
                    apply_obstacle_penalty()
                    obstacleActive = False

                elif canScore and x < cx < x + w and y < cy < y + h:
                    counter = 1
                    click_sound.play()  # Play sound on successful click

            # Power-up click detection
            if powerUpActive and x < cxPowerUp < x + w and y < cyPowerUp < y + h:
                activate_power_up()

            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 3)
            cvzone.putTextRect(img, f'{int(distanceCM)} cm', (x + 5, y - 10), scale=2, colorT=(255, 255, 255), colorR=(0, 0, 255))

        if counter:
            counter += 1
            color = (0, 255, 0)
            if counter == 3:
                cx = random.randint(100, 1100)
                cy = random.randint(100, 600)
                color = (0, 0, 255)
                score += handle_combo(True) + (2 if scoreMultiplierActive else 1)
                counter = 0
                increase_difficulty(score)

                if score == 10:
                    achievements.append("Scored 10 points")
                elif score == 20:
                    achievements.append("Scored 20 points")

        cv2.circle(img, (cx, cy), circleSize, color, cv2.FILLED)
        cv2.circle(img, (cx, cy), 10, (255, 255, 255), cv2.FILLED)
        cv2.circle(img, (cx, cy), 20, (255, 255, 255), 2)
        cv2.circle(img, (cx, cy), circleSize, (50, 50, 50), 2)

        if powerUpActive:
            cv2.circle(img, (cxPowerUp, cyPowerUp), 25, powerUpColor, cv2.FILLED)

        if obstacleActive:
            cv2.circle(img, (obstacleX, obstacleY), obstacleSize, (0, 0, 0), cv2.FILLED)

        spawn_power_up()
        spawn_obstacle()

        cvzone.putTextRect(img, f'Time: {int(totalTime - (time.time() - timeStart))}', (1000, 75), scale=3, colorT=(255, 255, 255), colorR=(0, 0, 255), offset=20)
        cvzone.putTextRect(img, f'Score: {str(score).zfill(2)}', (60, 75), scale=3, colorT=(255, 255, 255), colorR=(0, 0, 255), offset=20)
        cvzone.putTextRect(img, f'Level: {difficultyLevel}', (550, 75), scale=3, colorT=(255, 255, 255), colorR=(0, 0, 255), offset=20)

    else:
        show_achievements()

    cv2.imshow("Image", img)
    key = cv2.waitKey(1)

    if key == ord('q'):
        break
    elif key == ord('r'):
        timeStart = time.time()
        score = 0
        cx = random.randint(100, 1100)
        cy = random.randint(100, 600)
        circleSize = 30
        difficultyLevel = 1
        totalTime = 20
        speedX = random.choice([-3, 3])
        speedY = random.choice([-3, 3])
        powerUpActive = False
        scoreMultiplierActive = False
        extraTimeActive = False
        freezeTimeActive = False
        obstacleActive = False
        canScore = True

cap.release()
cv2.destroyAllWindows()
pygame.mixer.quit()
