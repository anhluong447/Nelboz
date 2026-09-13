import cv2

img = cv2.imread("data/raw_samples/feed/feed_20260913_183706_001.png")

# Look at bottom of Pham Ngoc card:
# Action bar is at Y ~ 860:900, X = 620:1250
# Let's crop:
crop_bar = img[860:895, 620:1250]
cv2.imwrite("data/raw_samples/feed/phamngoc_action_bar.png", crop_bar)

# Let's also crop the like icon, comment icon, and share icon:
# Like icon: X ~ 625 to 650
# Comment icon: X ~ 650 to 675
crop_icons = img[865:892, 625:675]
cv2.imwrite("data/raw_samples/feed/feed_like_comment_icons.png", crop_icons)

print("Saved phamngoc_action_bar.png and feed_like_comment_icons.png")
