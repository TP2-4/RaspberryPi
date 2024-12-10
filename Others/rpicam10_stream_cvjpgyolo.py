
import time
import cv2
import requests
import pprint
from picamera2 import Picamera2, Preview
from ultralytics import YOLO
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QPushButton, QVBoxLayout, QApplication, QWidget
from PyQt5.QtCore import QThread, pyqtSignal
from picamera2.previews.qt import QGlPicamera2

# Picamera2 객체 초기화
picam2 = Picamera2()

# 카메라 설정 (포맷 반드시 XRGB8888로 변경)
#video_config = picam2.create_video_configuration({"size": (1280, 1280), "format" : "XRGB8888"}) 
video_config = picam2.create_preview_configuration(
    main={"size": (1280, 1280), "format" : "XRGB8888"}, #For GUI
    lores={"size" : (640,640), "format":"RGB888"}       #For Capture and Send to Server
)     
picam2.configure(video_config)
print(video_config["main"])

# # QT 창으로 Preview 시작
# picam2.start_preview(Preview.QT)
# picam2.start()

server_url = "http://14.47.213.122:9978/upload"
#server_url = "http://localhost:13131/upload"

# SERVER_IP = '49.247.171.103'  # Server IP Address needed
# SERVER_PORT = 9978

# TCP Socket Configuration
# sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# sock.connect((SERVER_IP, SERVER_PORT))
# print(f"Connected to {SERVER_IP}:{SERVER_PORT}")

model = YOLO("yolov11n-face.pt")

def run():
    while True:
        print("Clicked")
        start_time = time.time()

        # 카메라에서 프레임 캡처 (default : main camera임)
        frame = picam2.capture_array("lores")
        # Run batched inference on a list of images
        print("Clicked")
        result = model.predict(frame, conf=0.5)[0]  # return a list of Results objects

        if any(result.boxes):
            for box in result.boxes:
                print(f"Face Detected, with Confidence: {box.conf}")
            try:
                # 프레임을 JPEG 형식으로 인코딩
                _, img_encoded = cv2.imencode('.jpg', frame)

                response = requests.post(server_url, files={"image": img_encoded.tobytes()})

                #현재 응답이 항상 표준 json이 아님
                response_dic : dict = eval(response._content.decode())[0]
                if "embedding" in response_dic:
                    response_dic["embedding"] = response_dic["embedding"][:3]
                pp = pprint.PrettyPrinter(compact=True)
                pp.pprint(response_dic)

                #Jsonnnable 체크
                try:
                    response.json()
                    print("Can JSONify")
                except:
                    print("Cannot JSONify") 
            except Exception as e:
                print(f"Error sending frame: {str(e)}")
        else:
            print("No Face Detected")


        elapsed_time = time.time() - start_time
        print("Processing Time : ", elapsed_time)

        if (elapsed_time < 1.0):
            time.sleep(1.0 - elapsed_time)
        #cfg = picam2.create_still_configuration()
        #picam2.switch_mode_and_capture_file(cfg, "test.jpg", signal_function=qpicamera2.signal_done)
  
def on_button_clicked():
    run()

app = QApplication([])
qpicamera2 = QGlPicamera2(picam2, width=800, height=800, keep_ar=False)
button = QPushButton("Click start send")
window = QWidget()
button.clicked.connect(on_button_clicked)

layout_v = QVBoxLayout()
layout_v.addWidget(qpicamera2)
layout_v.addWidget(button)

window.setWindowTitle("Qt Picamera2 App")
window.resize(800, 800)
window.setLayout(layout_v)
picam2.start()
window.show()
app.exec()


    
        
