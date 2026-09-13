import cv2
import numpy as np

img = cv2.imread("data/raw_samples/feed/feed_20260913_183654_001.png")
h, w, c = img.shape
print(f"Feed image shape: {w}x{h}")

# The Feed column is horizontally between sidebar left (~590) and right sidebar (~1270)
# Let's verify pixel colors across a horizontal line, e.g. Y = 500
# Feed column card background is pure white #FFFFFF: [255, 255, 255]
# Feed separator / background is light gray #F0F2F5: [245, 242, 240] in BGR [245, 242, 240]
# Sidebar background is also #F0F2F5 or white

# Let's inspect column 600 vs 900 vs 1250
# Let's look at the vertical column at X = 600 or X = 595 (just inside the card's left margin)
# Post cards in Facebook web have left margin at X ~ 615, right margin at X ~ 1255!
# Inside the card, background is white (255, 255, 255).
# Between cards, there is a gap of ~ 15-20px of #F0F2F5 (gray).

# Let's sample a vertical slice at X = 620 (inside the card text/header area)
slice_x = 620
col_pixels = img[180:1040, slice_x, :] # avoid browser top header
print(f"Sample colors at X={slice_x}:")
print("First 10 pixels:", col_pixels[:10])
