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
shield_sound = pygame.mixer.Sound('shield.mp3')  # Example sound for shield power-up
slow_motion_sound = pygame.mixer.Sound('slow_motion.mp3')  # Example sound for slow-motion power-up
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
cx, cy = random.randint(100, 1100), random.randint(100, 600)
color = (0, 0, 255)
counter = 0
score = 0
timeStart = time.time()
totalTime = 20
circleSize = 30
difficultyLevel = 1
comboCounter = 0
slowMotionActive = False
shieldActive = False

# Movement Variables
speedX = 0
speedY = 0
circleMoves = False  # Circle will start moving from level 3 onwards

# Power-Up Variables
powerUpActive = False
powerUpType = None
powerUpStartTime = 0
powerUpDuration = 5

# Achievements System
achievements = []

# Prevent spawning inside hand boundaries
def avoid_hand_collision(x, y, w, h, objX, objY, buffer=50):
    """Check if an object is colliding with the hand's bounding box."""
    return (x - buffer < objX < x + w + buffer) and (y - buffer < objY < y + h + buffer)

# Function to increase difficulty
def increase_difficulty(score):
    global circleSize, totalTime, difficultyLevel, speedX, speedY, circleMoves
    difficultyLevel = min(10, score // 5 + 1)  # Limit difficulty to level 10
    circleSize = max(15, 30 - difficultyLevel * 2)
    totalTime = max(15, 20 - difficultyLevel)

    # Start moving the circle at level 3, increase speed with difficulty
    if difficultyLevel >= 3:
        circleMoves = True
        speedX = random.choice([-3, 3]) * difficultyLevel
        speedY = random.choice([-3, 3]) * difficultyLevel
    else:
        circleMoves = False
        speedX, speedY = 0, 0

    # Play level up sound
    level_up_sound.play()

# Function to move the circle
def move_circle():
    global cx, cy, speedX, speedY, imgWidth, imgHeight
    if circleMoves:
        cx += speedX
        cy += speedY
        # Reverse direction upon hitting boundaries
        if cx - circleSize < 0 or cx + circleSize > imgWidth:
            speedX *= -1
        if cy - circleSize < 0 or cy + circleSize > imgHeight:
            speedY *= -1

# Power-Up Spawning Rules
def spawn_power_up():
    global powerUpActive, powerUpType, cxPowerUp, cyPowerUp, powerUpColor, difficultyLevel, powerUpStartTime
    if not powerUpActive and random.randint(1, 100) <= 20:  # 20% chance of spawning a power-up
        powerUpActive = True
        cxPowerUp = random.randint(100, 1100)
        cyPowerUp = random.randint(100, 600)
        powerUpType = random.choice(['extra_time', 'score_multiplier', 'slow_motion', 'shield'])
        powerup_sound.play()

        if powerUpType == 'extra_time':
            powerUpColor = (0, 255, 0)  # Green for extra time
        elif powerUpType == 'score_multiplier':
            powerUpColor = (255, 215, 0)  # Gold for score multiplier
        elif powerUpType == 'slow_motion':
            powerUpColor = (0, 0, 255)  # Blue for slow-motion
        elif powerUpType == 'shield':
            powerUpColor = (160, 32, 240)  # Purple for shield
        
        powerUpStartTime = time.time()

# Power-Up Effects
def activate_power_up():
    global totalTime, scoreMultiplierActive, slowMotionActive, shieldActive, powerUpType, powerUpActive, powerUpStartTime
    if powerUpType == 'extra_time':
        totalTime += 5  # Add 5 seconds to game time
    elif powerUpType == 'score_multiplier':
        scoreMultiplierActive = True
    elif powerUpType == 'slow_motion':
        slowMotionActive = True
        slow_motion_sound.play()  # Play slow-motion effect sound
    elif powerUpType == 'shield':
        shieldActive = True
        shield_sound.play()  # Play shield effect sound
    powerUpActive = False
    powerUpStartTime = time.time()

# Function to show game over screen
def game_over_screen(img):
    gameOverText = "Game Over"
    scoreText = f'Your Score: {str(score)}'
    restartText = 'Press R to restart or Q to quit'

    # Calculate text sizes
    gameOverSize = cv2.getTextSize(gameOverText, cv2.FONT_HERSHEY_PLAIN, 5, 7)[0]
    scoreSize = cv2.getTextSize(scoreText, cv2.FONT_HERSHEY_PLAIN, 3, 5)[0]
    restartSize = cv2.getTextSize(restartText, cv2.FONT_HERSHEY_PLAIN, 2, 2)[0]

    gameOverX = (imgWidth - gameOverSize[0]) // 2
    scoreX = (imgWidth - scoreSize[0]) // 2
    restartX = (imgWidth - restartSize[0]) // 2

    # Display game over text
    cvzone.putTextRect(img, gameOverText, (gameOverX, imgHeight // 2 - 50), scale=5, colorT=(255, 255, 255), colorR=(255, 0, 0), thickness=7)
    cvzone.putTextRect(img, scoreText, (scoreX, imgHeight // 2 + 50), scale=3, colorT=(255, 255, 255), colorR=(255, 0, 0))
    cvzone.putTextRect(img, restartText, (restartX, imgHeight // 2 + 150), scale=2, colorT=(255, 255, 255), colorR=(255, 0, 0))

# Main Loop
while True:
    success, img = cap.read()
    imgHeight, imgWidth, _ = img.shape

    # Handle freeze time power-up effect
    if slowMotionActive and time.time() - powerUpStartTime > powerUpDuration:
        slowMotionActive = False  # End slow motion after 5 seconds

    if shieldActive and time.time() - powerUpStartTime > powerUpDuration:
        shieldActive = False  # End shield effect after 5 seconds

    if not slowMotionActive and time.time() - timeStart < totalTime:
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
                # Check for collision with circle
                if avoid_hand_collision(x, y, w, h, cx, cy):
                    counter = 1
                    click_sound.play()

                # Check for power-up collection
                if powerUpActive and avoid_hand_collision(x, y, w, h, cxPowerUp, cyPowerUp):
                    activate_power_up()

            # Draw hand bounding box and distance
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 3)
            cvzone.putTextRect(img, f'{int(distanceCM)} cm', (x + 5, y - 10), scale=2, colorT=(255, 255, 255), colorR=(0, 0, 255))

        if counter:
            counter += 1
            color = (0, 255, 0)
            if counter == 3:
                cx, cy = random.randint(100, 1100), random.randint(100, 600)
                color = (0, 0, 255)
                score += (2 if scoreMultiplierActive else 1)
                counter = 0
                increase_difficulty(score)

        # Draw Circle
        cv2.circle(img, (cx, cy), circleSize, color, cv2.FILLED)
        cv2.circle(img, (cx, cy), 10, (255, 255, 255), cv2.FILLED)
        cv2.circle(img, (cx, cy), 20, (255, 255, 255), 2)
        cv2.circle(img, (cx, cy), circleSize, (50, 50, 50), 2)

        # Draw Power-Up
        if powerUpActive:
            cv2.circle(img, (cxPowerUp, cyPowerUp), 25, powerUpColor, cv2.FILLED)

        # Spawn Power-Up
        spawn_power_up()

        # Game HUD
        cvzone.putTextRect(img, f'Time: {int(totalTime - (time.time() - timeStart))}', (1000, 75), scale=3, colorT=(255, 255, 255), colorR=(0, 0, 255), offset=20)
        cvzone.putTextRect(img, f'Score: {str(score).zfill(2)}', (60, 75), scale=3, colorT=(255, 255, 255), colorR=(0, 0, 255), offset=20)
        cvzone.putTextRect(img, f'Level: {difficultyLevel}', (550, 75), scale=3, colorT=(255, 255, 255), colorR=(0, 0, 255), offset=20)

    else:
        # Game over screen
        game_over_screen(img)

    # Display Image
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
        speedX = 0
        speedY = 0
        powerUpActive = False
        slowMotionActive = False
        shieldActive = False

cap.release()
cv2.destroyAllWindows()
pygame.mixer.quit()
