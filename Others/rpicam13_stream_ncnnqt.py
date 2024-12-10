import time
import cv2
import requests
import pprint
from picamera2 import Picamera2
from ultralytics import YOLO
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget
from picamera2.previews.qt import QGlPicamera2

picam2 = Picamera2()
video_config = picam2.create_preview_configuration(
    main={"size": (1280, 1280), "format": "XRGB8888"},
    lores={"size": (640, 640), "format": "RGB888"}
)
picam2.configure(video_config)

ncnn_model = YOLO("./yolov11n-face_ncnn_model")
server_url = "http://14.47.213.122:9978/upload"

class CameraThread(QThread):
    frame_processed = pyqtSignal(str)  # UI ������Ʈ �ñ׳�

    def run(self):
        while True:
            start_time = time.time()

            # 카메라에서 프레임 캡처 (default : main camera임)
            frame = picam2.capture_array("lores")
            # Run batched inference on a list of images
            result = ncnn_model.predict(frame, conf=0.5)[0]  # return a list of Results objects

            if any(result.boxes):
                for box in result.boxes:
                    print(f"Face Detected, with Confidence: {box.conf}")
                try:
                    # 프레임을 JPEG 형식으로 인코딩
                    _, img_encoded = cv2.imencode('.jpg', frame)

                    response = requests.post(server_url, files={"image": img_encoded.tobytes(), "is_front" : 1})
                    #기능 추가 시 : {"image" : ����, "is_front" : 1 / 0}
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
            self.frame_processed.emit("Per loop")

app = QApplication([])

qpicamera2 = QGlPicamera2(picam2, width=800, height=800, keep_ar=False)
button = QPushButton("Connect Server")
window = QWidget()

layout_v = QVBoxLayout()
layout_v.addWidget(qpicamera2)
layout_v.addWidget(button)
window.setLayout(layout_v)
window.resize(800, 800)
window.setWindowTitle("Camera Manager")

picam2.start()

def update_ui(message):
    print(f"UI Updated: {message}")

camera_thread = CameraThread()
camera_thread.frame_processed.connect(update_ui)
button.clicked.connect(camera_thread.start)

window.show()
app.exec()
