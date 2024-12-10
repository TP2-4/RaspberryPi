from picamera2 import Picamera2
import time 

picam2 = Picamera2()
config = picam2.create_video_configuration()
picam2.configure(config)
picam2.start(show_preview=True)

# 공식 문서 14p : 창 상단바에 다음 정보를 출력
picam2.title_fields = {"ExposureTime", "AnalogueGain"}

time.sleep(10)