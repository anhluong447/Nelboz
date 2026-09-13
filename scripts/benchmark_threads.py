import cv2
import numpy as np
from pathlib import Path

template = cv2.imread("data/raw_samples/threads/template_like_clean.png", 0)
th, tw = template.shape

samples_dir = Path("data/raw_samples/threads")
sample_files = sorted(list(samples_dir.glob("threads_*.png")))

print(f"Testing on all {len(sample_files)} thread samples...")

passed = 0
for idx, f in enumerate(sample_files):
    img = cv2.imread(str(f))
    # Extract modal region (modal is always centered horizontally from ~600 to 1265)
    # or search in the middle 50% of the screen: X from 550 to 1350, Y from 150 to 950
    modal_crop = img[150:950, 550:1350]
    gray = cv2.cvtColor(modal_crop, cv2.COLOR_BGR2GRAY)
    
    res = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
    loc = np.where(res >= 0.70)
    
    pts = []
    for pt in zip(*loc[::-1]):
        if not any(abs(pt[0] - p[0]) < 15 and abs(pt[1] - p[1]) < 15 for p in pts):
            pts.append(pt)
            
    pts = sorted(pts, key=lambda p: p[1])
    l1_count = sum(1 for p in pts if p[0] <= 130)
    l2_count = sum(1 for p in pts if p[0] > 130)
    
    print(f"[{idx+1:02d}] {f.name}: Found {len(pts)} anchors (L1: {l1_count}, L2: {l2_count})")
    if len(pts) > 0:
        passed += 1

print(f"\nResult: Detected comment anchors in {passed}/{len(sample_files)} samples ({passed/len(sample_files)*100:.1f}%)")
