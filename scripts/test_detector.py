import cv2
import numpy as np

# Load template and full modal image
template = cv2.imread("data/raw_samples/threads/template_like_clean.png", 0)
modal = cv2.imread("data/raw_samples/threads/sample_modal_crop.png")
gray_modal = cv2.cvtColor(modal, cv2.COLOR_BGR2GRAY)

th, tw = template.shape
res = cv2.matchTemplate(gray_modal, template, cv2.TM_CCOEFF_NORMED)

# Threshold for matching
threshold = 0.72
loc = np.where(res >= threshold)

points = []
for pt in zip(*loc[::-1]):
    # Non-maximum suppression / grouping points within 15px
    if not any(abs(pt[0] - p[0]) < 15 and abs(pt[1] - p[1]) < 15 for p in points):
        points.append(pt)

print(f"Found {len(points)} like/action anchors in sample modal!")
vis = modal.copy()
for pt in points:
    # pt is like icon (x, y)
    # The 'Trả lời' text is located ~ 70-80px to the right!
    reply_x = pt[0] + 75
    reply_y = pt[1] + th // 2
    # Check X indentation to classify Level:
    # Top level: pt[0] < 120
    # Nested reply (level 2): pt[0] >= 120
    level = 2 if pt[0] > 115 else 1
    color = (0, 255, 0) if level == 1 else (0, 165, 255)
    cv2.rectangle(vis, pt, (pt[0] + tw, pt[1] + th), color, 2)
    cv2.circle(vis, (reply_x, reply_y), 4, (0, 0, 255), -1)
    cv2.putText(vis, f"L{level} Reply", (reply_x + 10, reply_y + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)

cv2.imwrite("data/raw_samples/threads/detection_result.png", vis)
print("Saved detection_result.png")
