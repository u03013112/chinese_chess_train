
import cv2
import numpy as np

# 读取图像
img = cv2.imread('/Users/u03013112/Downloads/cc.png')

# 转换到HSV颜色空间
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# 定义红色和黑色的颜色范围
lower_red = np.array([0, 100, 100])
upper_red = np.array([10, 255, 255])
lower_black = np.array([0, 0, 0])
upper_black = np.array([180, 255, 50])

# 对红色和黑色进行颜色过滤
mask_red = cv2.inRange(hsv, lower_red, upper_red)
mask_black = cv2.inRange(hsv, lower_black, upper_black)

# 合并颜色过滤的结果
mask = cv2.bitwise_or(mask_red, mask_black)

# 使用颜色过滤的结果进行Hough圆变换
# circles = cv2.HoughCircles(mask, cv2.HOUGH_GRADIENT, 1, 20, param1=50, param2=30, minRadius=0, maxRadius=0)
circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 10, param1=220, param2=50, minRadius=5, maxRadius=50)
# 绘制检测到的圆形
if circles is not None:
    circles = np.uint16(np.around(circles))
    for i in circles[0, :]:
        cv2.circle(img, (i[0], i[1]), i[2], (0, 255, 0), 2)

# 显示图像
cv2.imshow('detected circles', img)
cv2.waitKey(0)
cv2.destroyAllWindows()




