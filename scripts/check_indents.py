import cv2
import numpy as np

# Let's inspect the X of each detected point in sample modal
template = cv2.imread("data/raw_samples/threads/template_like_clean.png", 0)
modal = cv2.imread("data/raw_samples/threads/sample_modal_crop.png")
gray_modal = cv2.cvtColor(modal, cv2.COLOR_BGR2GRAY)

th, tw = template.shape
res = cv2.matchTemplate(gray_modal, template, cv2.TM_CCOEFF_NORMED)

threshold = 0.72
loc = np.where(res >= threshold)

points = []
for pt in zip(*loc[::-1]):
    if not any(abs(pt[0] - p[0]) < 15 and abs(pt[1] - p[1]) < 15 for p in points):
        points.append(pt)

# Sort points top to bottom (by Y)
points = sorted(points, key=lambda p: p[1])

print(f"Total points detected: {len(points)}")
for i, pt in enumerate(points):
    print(f"Point {i+1}: X = {pt[0]}, Y = {pt[1]}")

# Looking at output:
# Du Du (top-level): X = ?
# Huong Voi (reply): X = ?
# Le Minh Tam (top-level): X = ?
# Hang Nguyen (reply): X = ?
# Le Thuy Diem (reply): X = ?
