import cv2


img = cv2.imread("./lloy_boi.png")

# print(img.shape)
img = cv2.resize(img, (900,600))

cv2.imshow("Image_Preview", img)
cv2.waitKey(0)
cv2.destroyAllWindows()

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

cv2.imshow("Image_Preview_Gray", gray)
cv2.waitKey(0)
cv2.destroyAllWindows()
