import cv2
import numpy as np

# Load modal crop
modal = cv2.imread("data/raw_samples/threads/sample_modal_crop.png")

# Let's crop the exact action bars for Du Du and Huong Voi
# Top-level action bar: Y around 248:275, X around 80:300
crop_action_top = modal[245:275, 85:320]
cv2.imwrite("data/raw_samples/threads/anchor_action_top.png", crop_action_top)

# Level-2 reply action bar: Y around 322:350, X around 140:350
crop_action_reply = modal[320:348, 140:350]
cv2.imwrite("data/raw_samples/threads/anchor_action_reply.png", crop_action_reply)

# Crop the "Trả lời" text specifically
# In crop_action_top, where is "Trả lời"?
# Let's crop width around X=110 to 180 of crop_action_top
crop_tra_loi = crop_action_top[5:25, 115:175]
cv2.imwrite("data/raw_samples/threads/template_tra_loi.png", crop_tra_loi)

print("Crops saved successfully.")
