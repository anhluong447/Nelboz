import cv2
import numpy as np

img = cv2.imread("data/raw_samples/threads/sample_modal_crop.png")

# Let's inspect:
# 1. Top-level comment avatar: Du Du at Y ~ 78, X ~ 16, diameter ~ 40px
# 2. Reply comment avatar: Hương Voi at Y ~ 283, X ~ 92, diameter ~ 32px
# Indent delta = 92 - 16 = 76px!
# 3. Nút "Trả lời":
# For top-level Du Du:
# Action row (Like, Dislike, Trả lời):
# Icon Like at X ~ 95, Y ~ 258
# Nút "Trả lời" at X ~ 210, Y ~ 258
# For reply Hương Voi:
# Action row (Like, Dislike, Trả lời):
# Icon Like at X ~ 147, Y ~ 334
# Nút "Trả lời" at X ~ 262, Y ~ 334
# Offset difference in X between top-level and reply action bar: 262 - 210 = 52px (matching indent!)

print("Avatar top-level X ~ 16 to 56 (width: 40px)")
print("Avatar reply level-2 X ~ 92 to 124 (width: 32px)")
print("Indentation difference ~ 76px for avatar, ~52px for action bar")
print("Action bar text: [Thích icon] [Dislike icon] 'Trả lời' [Chia sẻ / Reactions]")
