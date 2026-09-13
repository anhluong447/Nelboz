import cv2
import numpy as np

img = cv2.imread("data/raw_samples/feed/feed_20260913_183927_001.png")
# In feed_20260913_183927_001.png, there is a distinct gap between the TikTok post and Mickelly post!
# Let's inspect rows 700 to 850 at X = 650
# BGR of separator #F0F2F5: [245, 242, 240]
col_pixels = img[700:850, 650, :]

for idx, p in enumerate(col_pixels):
    y = 700 + idx
    # Print when color is not pure white
    if not (p[0] == 255 and p[1] == 255 and p[2] == 255):
        print(f"Y = {y}: BGR = {p.tolist()}")
