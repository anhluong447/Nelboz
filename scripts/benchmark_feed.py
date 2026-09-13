import cv2
import numpy as np
from pathlib import Path

template = cv2.imread("data/raw_samples/feed/feed_template_like.png", 0)
th, tw = template.shape

samples_dir = Path("data/raw_samples/feed")
sample_files = sorted(list(samples_dir.glob("feed_20260913_183*.png")))

print(f"Testing on {len(sample_files)} recent feed samples...")

total_detected = 0
for idx, f in enumerate(sample_files):
    img = cv2.imread(str(f))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Search within feed column: X: 600..1270, Y: 180..1050
    roi = gray[180:1050, 600:1270]
    res = cv2.matchTemplate(roi, template, cv2.TM_CCOEFF_NORMED)
    loc = np.where(res >= 0.70)
    
    pts = []
    for pt in zip(*loc[::-1]):
        abs_pt = (pt[0] + 600, pt[1] + 180)
        if not any(abs(abs_pt[0] - p[0]) < 20 and abs(abs_pt[1] - p[1]) < 20 for p in pts):
            pts.append(abs_pt)
            
    print(f"[{idx+1:02d}] {f.name}: Found {len(pts)} post action bars at Y={[p[1] for p in pts]}")
    if len(pts) > 0:
        total_detected += 1

print(f"\nResult: Detected feed action bars in {total_detected}/{len(sample_files)} samples ({total_detected/len(sample_files)*100:.1f}%)")
