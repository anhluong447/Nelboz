import cv2

img = cv2.imread("data/raw_samples/feed/feed_20260913_183716_001.png")
# Look at bottom-most rows: 960 to 1080
strip = img[950:1000, 610:750]
cv2.imwrite("data/raw_samples/feed/sample3_actual_action.png", strip)
print("Saved sample3_actual_action.png")
