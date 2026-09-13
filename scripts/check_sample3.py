import cv2
import numpy as np

img = cv2.imread("data/raw_samples/feed/feed_20260913_183716_001.png")
# Look at row 950 to 980 in sample 3:
# The action bar has Like icon, comment count: 14, share icon
# Why didn't template match? Let's check coordinates around bottom:
strip = img[940:990, 610:720]
cv2.imwrite("data/raw_samples/feed/sample3_action_strip.png", strip)
print("Saved sample3_action_strip.png")
