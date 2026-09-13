import cv2
import numpy as np

# Load strip_comments.png
strip = cv2.imread("data/raw_samples/threads/strip_comments.png")
# Find dark text pixels (text is dark grey/black, background is white/light grey)
gray = cv2.cvtColor(strip, cv2.COLOR_BGR2GRAY)

# Look at rows 30 to 70 (where Row 1 action bar is)
# Let's save slices with row markers
vis = strip.copy()
for y in range(0, strip.shape[0], 20):
    cv2.line(vis, (0, y), (strip.shape[1], y), (0, 0, 255), 1)
    cv2.putText(vis, str(y), (5, y - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

cv2.imwrite("data/raw_samples/threads/strip_grid.png", vis)
print("Saved strip_grid.png")
