import cv2
import numpy as np

img = cv2.imread("data/raw_samples/feed/feed_20260913_183927_001.png")

# Look at X = 600 to 1270
# The feed separator background color is EXACTLY [245, 242, 240] in BGR (#F0F2F5)!
# Let's inspect a horizontal slice across Y = 800 (which is inside the gap):
gap_row = img[802, 600:1270, :]
# Are all pixels in this row [245, 242, 240]?
is_feed_bg = np.all(np.abs(gap_row.astype(int) - np.array([245, 242, 240])) < 5, axis=1)
print(f"Percentage of feed background in gap row at Y=802: {np.mean(is_feed_bg)*100:.1f}%")

# Let's check card bounds:
# In the Mickelly card at Y = 850:
card_row = img[850, 600:1270, :]
is_card_bg = np.all(card_row > 250, axis=1)
print(f"Percentage of card white in row at Y=850: {np.mean(is_card_bg)*100:.1f}%")

# Find left and right bounds of the card:
white_cols = np.where(np.all(img[850:900, :, :] > 250, axis=2))
# cols are:
cols_in_card = white_cols[1][(white_cols[1] > 500) & (white_cols[1] < 1400)]
if len(cols_in_card) > 0:
    print(f"Card X bounds: from {np.min(cols_in_card)} to {np.max(cols_in_card)} (Width: {np.max(cols_in_card) - np.min(cols_in_card)}px)")
