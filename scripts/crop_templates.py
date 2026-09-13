import cv2

strip = cv2.imread("data/raw_samples/threads/strip_comments.png")

# In strip_comments.png:
# Row 1 action bar: "Like, Dislike, Trả lời" is around Y=40 to 60
# Row 2 action bar: "Like, Dislike, Trả lời" is around Y=115 to 135

# Let's crop the action bar for Hương Voi (Row 2):
# X from 15 to 150 of strip
crop_action2 = strip[115:135, 18:140]
cv2.imwrite("data/raw_samples/threads/huongvoi_action.png", crop_action2)

# In this action bar:
# Like icon: X ~ 0 to 22
# Dislike icon: X ~ 45 to 65
# "Trả lời": X ~ 75 to 120
crop_tra_loi_btn = crop_action2[0:20, 70:120]
cv2.imwrite("data/raw_samples/threads/template_tra_loi_exact.png", crop_tra_loi_btn)

# Also crop the like icon
crop_like_icon = crop_action2[0:20, 0:25]
cv2.imwrite("data/raw_samples/threads/template_like_icon.png", crop_like_icon)

print("Saved huongvoi_action.png, template_tra_loi_exact.png, template_like_icon.png")
