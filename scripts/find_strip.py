import cv2

modal = cv2.imread("data/raw_samples/threads/sample_modal_crop.png")

# Let's crop a vertical strip of 200px height around Y = 200:400 to see where everything is
strip = modal[180:400, 70:450]
cv2.imwrite("data/raw_samples/threads/strip_comments.png", strip)
print("Saved strip_comments.png")
