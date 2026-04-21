import cv2

vid = cv2.VideoCapture("./sayingWA.mp4")
web = cv2.VideoCapture(0)

while True:
    try: 
        ret,frame = web.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame_canny = cv2.Canny(frame,50,80)
        cv2.imshow("video",frame_canny)
    except:
        pass
    if cv2.waitKey(1) & 0xff==ord('q'):
        break

cv2.destroyAllWindows()