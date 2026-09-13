import cv2
import numpy as np

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

points = sorted(points, key=lambda p: p[1])

vis = modal.copy()
for i, pt in enumerate(points):
    is_reply = pt[0] > 75
    level_str = "Reply (L2)" if is_reply else "Comment (L1)"
    box_color = (0, 165, 255) if is_reply else (0, 200, 0)
    
    # Bounding box around Like icon
    cv2.rectangle(vis, pt, (pt[0] + tw, pt[1] + th), box_color, 2)
    
    # Exact center of 'Trả lời' button:
    # "Trả lời" is about 80px to the right of Like icon center
    reply_btn_x = pt[0] + 82
    reply_btn_y = pt[1] + th // 2
    
    # Draw reply click point
    cv2.circle(vis, (reply_btn_x, reply_btn_y), 5, (0, 0, 255), -1)
    cv2.rectangle(vis, (reply_btn_x - 22, reply_btn_y - 10), (reply_btn_x + 22, reply_btn_y + 10), (255, 0, 0), 1)
    
    # Text label
    cv2.putText(vis, f"#{i+1} {level_str}", (pt[0] + 120, pt[1] + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1)

cv2.imwrite("data/raw_samples/threads/hierarchy_detected.png", vis)
print("Saved hierarchy_detected.png")
