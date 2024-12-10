
import socket
import cv2
from picamera2 import Picamera2, Preview

# Picamera2 객체 초기화
picam2 = Picamera2()

# 카메라 설정 (포맷 반드시 XRGB8888로 변경)
video_config = picam2.create_video_configuration({"size": (1280, 720), "format" : "XRGB8888"}) 
picam2.configure(video_config)
print(video_config["main"])

# QT 창으로 Preview 시작
picam2.start_preview(Preview.QT)
picam2.start()

SERVER_IP = '172.30.1.92'  # Server IP Address needed
SERVER_PORT = 10001

# TCP Socket Configuration
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((SERVER_IP, SERVER_PORT))
print(f"Connected to {SERVER_IP}:{SERVER_PORT}")

try:
    while True:
        # 카메라에서 프레임 캡처 (default : main camera임)
        frame = picam2.capture_array()
        
        # 프레임을 JPEG 형식으로 인코딩
        _, buffer = cv2.imencode('.jpg', frame)
        data = buffer.tobytes()

        # TCP 소켓을 통해 JPEG 전송
        sock.sendall(len(data).to_bytes(4, byteorder='big'))
        sock.sendall(data)

except KeyboardInterrupt:
    print("Streaming stopped.")

finally:
    # 소켓 닫기
    sock.close()
    picam2.stop_preview()
    picam2.stop()
