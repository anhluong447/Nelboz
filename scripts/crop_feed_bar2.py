import cv2

img = cv2.imread("data/raw_samples/feed/feed_20260913_183927_001.png")

# Let's crop slightly lower: Y = 750 to 800
crop_bar = img[755:790, 620:750]
cv2.imwrite("data/raw_samples/feed/feed_action_correct.png", crop_bar)
print("Saved feed_action_correct.png")
