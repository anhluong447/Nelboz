import cv2

img = cv2.imread("data/raw_samples/feed/feed_20260913_183706_001.png")

# Now look at Y:
# Action bar is at Y = 948 to 975!
# Like icon: X ~ 625 to 655
# Comment icon: X ~ 665 to 695
crop_like = img[948:975, 627:655]
cv2.imwrite("data/raw_samples/feed/feed_template_like.png", crop_like)

crop_comment = img[948:975, 668:695]
cv2.imwrite("data/raw_samples/feed/feed_template_comment.png", crop_comment)

# Both together:
crop_bar = img[945:976, 620:750]
cv2.imwrite("data/raw_samples/feed/feed_template_action_bar.png", crop_bar)

print("Saved clean feed templates!")
