import cv2
import numpy as np

blank = np.zeros((500,500,3), dtype = 'uint8')

cv2.imshow("",blank)
print(blank)
cv2.waitKey(0)
