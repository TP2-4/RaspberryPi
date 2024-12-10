
import time
import cv2
import requests
import pprint
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

server_url = "http://14.47.213.122:9978/upload"
#server_url = "http://localhost:13131/upload"

# SERVER_IP = '49.247.171.103'  # Server IP Address needed
# SERVER_PORT = 9978

# TCP Socket Configuration
# sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# sock.connect((SERVER_IP, SERVER_PORT))
# print(f"Connected to {SERVER_IP}:{SERVER_PORT}")

while True:
    # 카메라에서 프레임 캡처 (default : main camera임)
    frame = picam2.capture_array()
        
    # 프레임을 JPEG 형식으로 인코딩
    _, img_encoded = cv2.imencode('.jpg', frame)

    # Flask 서버로 프레임 전송
    try:
        response = requests.post(server_url, files={"image": img_encoded.tobytes()})
        #print(f"Server response: {response.json()}")
        #현재 응답이 항상 표준 json이 아님
        response_dic : dict = eval(response._content.decode())[0]
        if "embedding" in response_dic:
            response_dic["embedding"] = response_dic["embedding"][:3]
        pp = pprint.PrettyPrinter(compact=True)
        pp.pprint(response_dic)

        try:
            response.json()
            print("Can JSONify")
        except:
            print("Cannot JSONify") 
    except Exception as e:
        print(f"Error sending frame: {str(e)}")
        
    time.sleep(1) #1초 휴식
    

    # if cv2.waitKey(1) & 0xFF == ord('q'):
    #     print("Streaming stopped")
    #     picam2.stop_preview()
    #     picam2.stop()
    #     break
        
