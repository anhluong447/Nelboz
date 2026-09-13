import cv2

modal = cv2.imread("data/raw_samples/threads/sample_modal_crop.png")

# Let's inspect the exact action bar below Du Du's comment
# Du Du text ends around Y ~ 240
# Action bar is around Y ~ 245 to 275
# Let's crop Y from 240 to 280, X from 70 to 350
crop1 = modal[245:278, 80:330]
cv2.imwrite("data/raw_samples/threads/crop_action_dudu.png", crop1)

# Below Huong Voi: text ends around Y ~ 315
# Action bar is around Y ~ 320 to 350
crop2 = modal[318:348, 135:360]
cv2.imwrite("data/raw_samples/threads/crop_action_huongvoi.png", crop2)

print("Saved crop_action_dudu.png and crop_action_huongvoi.png")
