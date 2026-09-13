import cv2

img = cv2.imread("data/raw_samples/feed/feed_20260913_183706_001.png")

# Let's save strip with grid around bottom of Pham Ngoc card: Y from 800 to 1000
strip = img[800:1000, 600:1300].copy()
for y in range(0, strip.shape[0], 20):
    cv2.line(strip, (0, y), (strip.shape[1], y), (0, 0, 255), 1)
    actual_y = 800 + y
    cv2.putText(strip, str(actual_y), (5, y - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

cv2.imwrite("data/raw_samples/feed/feed_grid.png", strip)
print("Saved feed_grid.png")
