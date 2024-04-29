from mss import mss
import numpy as np
import cv2
import time
# 定义截取区域
left, top, width, height = 0, 0, 3024//4,1964//4

with mss() as sct:
    monitor = {"left": left, "top": top, "width": width, "height": height}
    monitor = sct.monitors[0]
    startTime = time.time()
    sct_img = sct.grab(monitor)
    print(f"Time: {time.time() - startTime}")
    img_np = np.array(sct_img)
    print(f"Image shape: {img_np.shape}")
    # img_np = cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGR)

# 显示截取到的图像
cv2.imshow("Captured Image", img_np)
cv2.waitKey(0)
cv2.destroyAllWindows()
