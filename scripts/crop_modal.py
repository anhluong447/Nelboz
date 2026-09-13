import cv2
import numpy as np

img = cv2.imread("data/raw_samples/threads/threads_20260913_180324_001.png")
# Modal bounds: X=[608, 1263], Y=[184, 1055]
modal = img[184:1055, 608:1263]

# Let's inspect avatar locations
# Top-level comments have avatars at X roughly 620-660 (relative to screen) or 10-50 relative to modal
# Reply comments have avatars indented to the right!
# Let's crop a small strip of sample 4 to inspect where the "Trả lời" text or thumb up icons are located
cv2.imwrite("data/raw_samples/threads/sample_modal_crop.png", modal)
print("Saved sample_modal_crop.png")
