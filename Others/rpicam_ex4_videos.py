from picamera2.encoders import H264Encoder, Quality
from picamera2 import Picamera2, Preview
import time
picam2 = Picamera2()
video_config = picam2.create_video_configuration()
picam2.configure(video_config)
encoder = H264Encoder(bitrate=10000000)
output = "test.h264"

picam2.start_preview(Preview.QT)
picam2.start_recording(encoder, output, quality=Quality.VERY_HIGH)
time.sleep(10)
picam2.stop_recording()
picam2.stop_preview()