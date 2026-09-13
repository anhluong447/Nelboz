import cv2
import numpy as np
from pathlib import Path

samples_dir = Path("data/raw_samples/threads")
sample_files = sorted(list(samples_dir.glob("*.png")))

for idx, f in enumerate(sample_files[:6]):
    img = cv2.imread(str(f))
    h, w, _ = img.shape
    
    # Check rows around 300 to 700 to locate modal box
    # Modal is centered, white box with rounded corners and slight drop shadow
    # Surrounding area is darkened backdrop rgba(244, 244, 244, ...) or blurred
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Threshold for pure white/near white modal background
    _, thresh = cv2.threshold(gray, 252, 255, cv2.THRESH_BINARY)
    
    col_sum = np.sum(thresh[300:700, :], axis=0)
    active_cols = np.where(col_sum > 100 * 255)[0]
    
    row_sum = np.sum(thresh[:, active_cols[0]:active_cols[-1]], axis=1) if len(active_cols) > 0 else []
    active_rows = np.where(row_sum > 100 * 255)[0] if len(row_sum) > 0 else []
    
    if len(active_cols) > 0 and len(active_rows) > 0:
        x1, x2 = active_cols[0], active_cols[-1]
        y1, y2 = active_rows[0], active_rows[-1]
        print(f"[{idx+1}] {f.name}: Modal bounds: X=[{x1}, {x2}] (W={x2-x1}), Y=[{y1}, {y2}] (H={y2-y1})")
