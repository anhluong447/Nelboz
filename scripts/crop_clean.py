import cv2

strip = cv2.imread("data/raw_samples/threads/strip_comments.png")

# Now we see exact coordinates from the grid!
# In row 2 (Huong Voi):
# Action row is from Y = 100 to 125!
# Let's crop:
# Like icon: Y=103:123, X=26:47
# Dislike icon: Y=103:123, X=67:86
# "Trả lời": Y=103:123, X=105:150
crop_tra_loi = strip[103:123, 105:148]
cv2.imwrite("data/raw_samples/threads/template_tra_loi_clean.png", crop_tra_loi)

crop_like = strip[103:123, 26:47]
cv2.imwrite("data/raw_samples/threads/template_like_clean.png", crop_like)

# Let's also crop for Row 1 (top level):
# "Trả lời" is from Y=43:63, X=68:110
crop_tra_loi_top = strip[43:63, 68:110]
cv2.imwrite("data/raw_samples/threads/template_tra_loi_top.png", crop_tra_loi_top)

print("Saved clean templates!")
