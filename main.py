# ========================================
# ПРОГРАМА ДЛЯ МАЛЮВАННЯ РУКАМИ 🎨
# Версія 2.0 - Всі баги виправлено!
# ========================================

import cv2
import numpy as np
import os

# ========================================
# НАЛАШТУВАННЯ ТОВЩИНИ (можна змінювати)
# ========================================
brushThickness = 15  # початкова товщина пензля
eraserThickness = 100  # початкова товщина стирачки

# Мінімум та максимум
MIN_THICKNESS = 5
MAX_BRUSH = 50
MAX_ERASER = 200

# ========================================
# ЗАВАНТАЖЕННЯ ЗАГОЛОВКІВ
# ========================================

folderpath = 'Header'

if not os.path.exists(folderpath):
    print(f"❌ ПОМИЛКА: Папка '{folderpath}' не знайдена!")
    print("Спочатку запустіть: python create_header_images.py")
    exit()

mylist = sorted(os.listdir(folderpath))
print(f"📁 Знайдено файлів: {mylist}")

header_images = {}
for impath in mylist:
    image = cv2.imread(f'{folderpath}/{impath}')
    if image is not None:
        header_images[impath] = image
        print(f"   ✅ Завантажено: {impath}")
    else:
        print(f"   ⚠️ Не вдалося завантажити: {impath}")

if len(header_images) == 0:
    print("❌ ПОМИЛКА: Не знайдено картинок!")
    exit()

HEADERS = {
    'yell': 'yellow.png',
    'blue': 'blue.png',
    'red': 'red.png',
    'eraser': 'eraser.png'
}

COLORS = {
    'yell': (0, 255, 255),
    'blue': (255, 0, 0),
    'red': (0, 3, 255),
    'eraser': (0, 0, 0)
}

current_color_name = 'yell'
Header = header_images[HEADERS['yell']]
drawColor = COLORS['yell']

print(f"\n✅ Завантажено {len(header_images)} заголовків")
print(f"🎨 Початковий колір: {current_color_name}")

# ========================================
# НАЛАШТУВАННЯ КАМЕРИ
# ========================================

cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)

if not cap.isOpened():
    print("❌ Не можу відкрити камеру!")
    exit()

# Читаємо реальний розмір кадру з камери
ret_test, frame_test = cap.read()
if ret_test:
    CAM_H, CAM_W = frame_test.shape[:2]
else:
    CAM_W, CAM_H = 1280, 720
print(f"📷 Реальний розмір камери: {CAM_W}x{CAM_H}")

# ========================================
# ДЕТЕКТОР РУК
# ========================================

import mediapipe as mp


class SimpleHandDetector:
    def __init__(self, detectionCon=0.7):
        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=detectionCon,
            min_tracking_confidence=detectionCon
        )
        self.tipIds = [4, 8, 12, 16, 20]
        self.lmList = []

    def findHands(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)

        if self.results.multi_hand_landmarks:
            for hand in self.results.multi_hand_landmarks:
                if draw:
                    self.mp_draw.draw_landmarks(
                        img, hand, self.mp_hands.HAND_CONNECTIONS
                    )
        return img

    def findPosition(self, img, handNo=0, draw=False):
        self.lmList = []

        if self.results.multi_hand_landmarks:
            myHand = self.results.multi_hand_landmarks[handNo]

            for id, lm in enumerate(myHand.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                self.lmList.append([id, cx, cy])

                if draw:
                    cv2.circle(img, (cx, cy), 7, (255, 0, 0), cv2.FILLED)

        return self.lmList

    def fingersUp(self):
        fingers = []

        if len(self.lmList) == 0:
            return []

        if self.lmList[self.tipIds[0]][1] < self.lmList[self.tipIds[0] - 1][1]:
            fingers.append(1)
        else:
            fingers.append(0)

        for id in range(1, 5):
            if self.lmList[self.tipIds[id]][2] < self.lmList[self.tipIds[id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)

        return fingers


detector = SimpleHandDetector(detectionCon=0.85)

# ========================================
# ЗМІННІ ДЛЯ МАЛЮВАННЯ
# ========================================

xp, yp = 0, 0
# Canvas тепер точно такого ж розміру як кадр з камери
inCanvas = np.zeros((CAM_H, CAM_W, 3), np.uint8)

print("\n" + "=" * 60)
print("🎨 ВІРТУАЛЬНИЙ ХУДОЖНИК - КЕРУВАННЯ")
print("=" * 60)
print("✌️  2 пальці (вказівний + середній) → ВИБІР КОЛЬОРУ")
print("☝️  1 палець (тільки вказівний) → МАЛЮВАННЯ")
print("👍 Великий палець вгору → ЗБІЛЬШИТИ розмір")
print("👎 Великий палець вниз → ЗМЕНШИТИ розмір")
print("")
print("⌨️  Клавіші:")
print("   Q - вихід")
print("   C - очистити полотно")
print("   + - збільшити пензель")
print("   - - зменшити пензель")
print("=" * 60 + "\n")

# ========================================
# ГОЛОВНИЙ ЦИКЛ
# ========================================

while True:
    success, img = cap.read()

    if not success:
        print("❌ Не можу прочитати кадр")
        break

    img = cv2.flip(img, 1)
    img = detector.findHands(img)
    lmList = detector.findPosition(img, draw=False)

    if len(lmList) != 0:

        x1, y1 = lmList[8][1:]
        x2, y2 = lmList[12][1:]
        x_thumb = lmList[4][1]
        y_thumb = lmList[4][2]

        fingers = detector.fingersUp()

        # ========================================
        # РЕЖИМ РЕГУЛЮВАННЯ РОЗМІРУ (великий палець)
        # ========================================
        if fingers[0] and not fingers[1] and not fingers[2]:

            if y_thumb < 300:
                if drawColor == (0, 0, 0):
                    eraserThickness = min(eraserThickness + 2, MAX_ERASER)
                else:
                    brushThickness = min(brushThickness + 1, MAX_BRUSH)

                cv2.putText(img, f"SIZE UP! Brush:{brushThickness} Eraser:{eraserThickness}",
                            (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)

            elif y_thumb > 400:
                if drawColor == (0, 0, 0):
                    eraserThickness = max(eraserThickness - 2, MIN_THICKNESS)
                else:
                    brushThickness = max(brushThickness - 1, MIN_THICKNESS)

                cv2.putText(img, f"SIZE DOWN! Brush:{brushThickness} Eraser:{eraserThickness}",
                            (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

            xp, yp = 0, 0

        # ========================================
        # РЕЖИМ ВИБОРУ КОЛЬОРУ (2 пальці)
        # ========================================
        elif fingers[1] and fingers[2]:

            xp, yp = 0, 0

            cv2.rectangle(img, (x1, y1 - 25), (x2, y2 + 25), drawColor, cv2.FILLED)

            if y1 < 125:

                # Зони вибору кольору — динамічні відносно реальної ширини камери
                zone = CAM_W // 4  # ділимо екран на 4 рівні частини
                if 0 < x1 < zone:
                    current_color_name = 'yell'
                elif zone < x1 < zone * 2:
                    current_color_name = 'blue'
                elif zone * 2 < x1 < zone * 3:
                    current_color_name = 'red'
                elif zone * 3 < x1 < CAM_W:
                    current_color_name = 'eraser'

                drawColor = COLORS[current_color_name]
                Header = header_images[HEADERS[current_color_name]]

                cv2.putText(img, f"Selected: {current_color_name.upper()}",
                            (x1 - 50, y1 + 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 3)

        # ========================================
        # РЕЖИМ МАЛЮВАННЯ (1 палець)
        # ========================================
        elif fingers[1] and not fingers[2]:

            current_thickness = eraserThickness if drawColor == (0, 0, 0) else brushThickness
            cv2.circle(img, (x1, y1), current_thickness // 2, drawColor, 2)

            if xp == 0 and yp == 0:
                xp, yp = x1, y1

            if drawColor == (0, 0, 0):
                cv2.line(img, (xp, yp), (x1, y1), drawColor, eraserThickness)
                cv2.line(inCanvas, (xp, yp), (x1, y1), drawColor, eraserThickness)
            else:
                cv2.line(img, (xp, yp), (x1, y1), drawColor, brushThickness)
                cv2.line(inCanvas, (xp, yp), (x1, y1), drawColor, brushThickness)

            xp, yp = x1, y1

    # ========================================
    # НАКЛАДАННЯ МАЛЮНКА
    # ========================================

    # img і inCanvas тепер однакового розміру — помилки не буде
    imgGray = cv2.cvtColor(inCanvas, cv2.COLOR_BGR2GRAY)
    _, imgInv = cv2.threshold(imgGray, 50, 255, cv2.THRESH_BINARY_INV)
    imgInv = cv2.cvtColor(imgInv, cv2.COLOR_GRAY2BGR)

    img = cv2.bitwise_and(img, imgInv)
    img = cv2.bitwise_or(img, inCanvas)

    # Додаємо заголовок — підганяємо під реальну ширину
    header_resized = cv2.resize(Header, (CAM_W, 125))
    img[0:125, 0:CAM_W] = header_resized

    info_text = f"Color: {current_color_name.upper()} | Brush: {brushThickness}px | Eraser: {eraserThickness}px"
    cv2.putText(img, info_text, (10, CAM_H - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    cv2.imshow('Virtual Painter', img)
    cv2.imshow('Canvas', inCanvas)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        print("👋 Вихід...")
        break

    elif key == ord('c'):
        inCanvas = np.zeros((CAM_H, CAM_W, 3), np.uint8)
        print("🧹 Полотно очищено!")

    elif key == ord('+') or key == ord('='):
        if drawColor == (0, 0, 0):
            eraserThickness = min(eraserThickness + 5, MAX_ERASER)
            print(f"📏 Розмір гумки: {eraserThickness}")
        else:
            brushThickness = min(brushThickness + 2, MAX_BRUSH)
            print(f"📏 Розмір пензля: {brushThickness}")

    elif key == ord('-') or key == ord('_'):
        if drawColor == (0, 0, 0):
            eraserThickness = max(eraserThickness - 5, MIN_THICKNESS)
            print(f"📏 Розмір гумки: {eraserThickness}")
        else:
            brushThickness = max(brushThickness - 2, MIN_THICKNESS)
            print(f"📏 Розмір пензля: {brushThickness}")

cap.release()
cv2.destroyAllWindows()
print("✅ Програма завершена")