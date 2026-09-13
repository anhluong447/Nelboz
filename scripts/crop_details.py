import cv2

modal = cv2.imread("data/raw_samples/threads/sample_modal_crop.png")
h, w, _ = modal.shape

# Let's crop:
# 1. Du Du action row: Y from 240 to 280, X from 70 to 350
crop_action = modal[240:280, 70:350]
cv2.imwrite("data/raw_samples/threads/dudu_action_row.png", crop_action)

# 2. Huong Voi action row: Y from 315 to 355, X from 130 to 400
crop_reply_action = modal[315:355, 130:400]
cv2.imwrite("data/raw_samples/threads/huongvoi_action_row.png", crop_reply_action)

# 3. Bottom input box: Y from 780 to 865, X from 20 to 640
crop_bottom_input = modal[780:865, 20:640]
cv2.imwrite("data/raw_samples/threads/bottom_input_row.png", crop_bottom_input)

print("Saved all 3 crops!")
