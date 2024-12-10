from picamera2 import Picamera2, Preview
from libcamera import Transform
import time

picam2 = Picamera2()
config = picam2.create_preview_configuration()
picam2.configure(config)
print("Preview NULL Start!")
picam2.start() #공식문서 12p에서 start_preview를 생략하면 Preview.NULL을 선택한다고 한다.

time.sleep(2) # 아무것도 뜨지 않는 것은 정상

picam2.stop_preview()
#공식문서 11p : start Preview 함수에서 카메라의 offset 및 가로 세로 크기, 화면 뒤집기를 지정할 수 있다.
picam2.start_preview(Preview.QT, x=0, y=0, width=720, height=600, 
transform=Transform(vflip=1))

time.sleep(2)

picam2.stop_preview()
picam2.start_preview(True) #공식문서 13p : 알아서 첫번째 인자를 선택함.

time.sleep(2)