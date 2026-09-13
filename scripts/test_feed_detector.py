import cv2
import numpy as np

# Load feed template and a full feed image
template = cv2.imread("data/raw_samples/feed/feed_template_like.png", 0)
feed_img = cv2.imread("data/raw_samples/feed/feed_20260913_183939_001.png")
gray = cv2.cvtColor(feed_img, cv2.COLOR_BGR2GRAY)

th, tw = template.shape

# Limit search region horizontally to feed column: X from 600 to 1270, Y from 180 to 1050
roi = gray[180:1050, 600:1270]
res = cv2.matchTemplate(roi, template, cv2.TM_CCOEFF_NORMED)

loc = np.where(res >= 0.70)
points = []
for pt in zip(*loc[::-1]):
    abs_pt = (pt[0] + 600, pt[1] + 180)
    if not any(abs(abs_pt[0] - p[0]) < 20 and abs(abs_pt[1] - p[1]) < 20 for p in points):
        points.append(abs_pt)

points = sorted(points, key=lambda p: p[1])
print(f"Found {len(points)} post anchors in feed_20260913_183939_001.png!")

vis = feed_img.copy()
for i, pt in enumerate(points):
    print(f"Post {i+1}: Action bar at X={pt[0]}, Y={pt[1]}")
    # Draw like icon
    cv2.rectangle(vis, pt, (pt[0] + tw, pt[1] + th), (0, 255, 0), 2)
    # Comment icon is at X + 41
    comment_btn_x = pt[0] + 41
    comment_btn_y = pt[1] + th // 2
    cv2.circle(vis, (comment_btn_x, comment_btn_y), 5, (0, 0, 255), -1)
    cv2.putText(vis, f"Post #{i+1} Comment Btn", (comment_btn_x + 15, comment_btn_y + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)

cv2.imwrite("data/raw_samples/feed/feed_detection_result.png", vis)
print("Saved feed_detection_result.png")
