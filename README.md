#  Air Canvas

Draw in the air using your hand — no mouse, no tablet, just your webcam and fingers!
The program tracks your hand in real time and lets you paint on a virtual canvas.

##  Demo

*(It`s must be a gif)*

##  How it works

| Gesture | Action |
|--------|--------|
| ☝️ Index finger up | Draw |
| ✌️ Index + middle fingers up | Select color / open palette |
| 👍 Thumb up (raised) | Increase brush size |
| 👍 Thumb down (lowered) | Decrease brush size |

## 🎨 Colors

Choose from 4 preset colors in the header panel, or open the full color palette for 16+ colors.
The current color is always shown in the bottom left corner.

## ⌨️ Keyboard shortcuts

| Key | Action |
|-----|--------|
| `C` | Clear canvas |
| `P` | Open / close color palette |
| `+` | Increase brush size |
| `-` | Decrease brush size |
| `Q` | Quit |

## 🔧 Technologies

- Python
- OpenCV
- MediaPipe

##  How to run

1. Install dependencies:
```
pip install opencv-python mediapipe numpy
```

2. Make sure the `Header` folder exists with these images:
```
Header/
  yellow.png
  blue.png
  red.png
  eraser.png
  palette.png
```

3. Run:
```
python virtual_painter.py
```

##  Plans

- Save canvas as image file
- Add shapes (circle, rectangle, line)
- Adjustable opacityr
