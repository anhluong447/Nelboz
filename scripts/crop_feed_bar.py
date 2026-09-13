import cv2

img = cv2.imread("data/raw_samples/feed/feed_20260913_183927_001.png")

# The TikTok card action bar is around Y = 750 to 780, X = 620 to 1250
# Let's crop the entire action bar: Like icon, Comment icon, Share icon
crop_bar = img[760:790, 620:1250]
cv2.imwrite("data/raw_samples/feed/feed_action_bar.png", crop_bar)

# Let's crop specifically the Comment button icon in the feed action bar
# Like icon is on the left (~630)
# Comment icon is next (~660-680)
# Let's crop X from 620 to 720
crop_icons = img[760:790, 620:720]
cv2.imwrite("data/raw_samples/feed/feed_action_icons.png", crop_icons)

print("Saved feed_action_bar.png and feed_action_icons.png")
