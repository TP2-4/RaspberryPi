import time
import cv2
import requests
import pprint
import numpy as np
from picamera2 import Picamera2
from ultralytics import YOLO
from PyQt5.QtCore import QThread, pyqtSignal, QSemaphore
from PyQt5.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QSizePolicy
from PyQt5 import uic
from picamera2.previews.qt import QGlPicamera2
from PyQt5.QtGui import QImage, QPixmap

def main():
    cv2.ocl.setUseOpenCL(True) # Only for Raspberry Pi 4+
    app = QApplication([])
    window = ParentWindow()
    window.show()
    app.exec_()

class ParentWindow(QWidget):
    def __init__(self):
        super().__init__()

        # self.setWindowIcon(QtGui.QIcon('icon.png')) # 윈도우 아이콘 필요시
        self.setWindowTitle("Camera Manager")
        self.resize(1280, 800)

        # create Parent Layout
        self.layout = QVBoxLayout()
        self.layout.setSpacing(0)
        
        # Load UI 
        self.ui = uic.loadUi("camera_controller.ui")
        self.layout.addWidget(self.ui)
        self.setLayout(self.layout)

        # Get YOLO and Sending Thread
        # self.yolo_send = YOLOSendThread()

        # Get Camera Objects
        self.front_camera = FrontCameraThread()
        self.front_camera.init_camera_signal.connect(self.init_front_camera)
        self.front_camera.update_label_signal.connect(self.update_front_label)
        self.front_camera.start()
        
        self.rear_camera = RearCameraThread()
        self.rear_camera.update_frame_signal.connect(self.update_rear_camera)
        self.rear_camera.update_label_signal.connect(self.update_rear_label)
        self.rear_camera.start()

        

        
        # button Connection
        self.ui.frontDisconnect.setDisabled(True)
        self.ui.rearDisconnect.setDisabled(True)
        self.ui.frontConnect.clicked.connect(self.frontConnect_clicked)
        self.ui.frontDisconnect.clicked.connect(self.frontDisconnect_clicked)
        self.ui.rearConnect.clicked.connect(self.rearConnect_clicked)
        self.ui.rearDisconnect.clicked.connect(self.rearDisconnect_clicked)



    def init_front_camera(self, camera : QGlPicamera2):
        self.ui.FrontCameraView.addWidget(camera)

    def update_rear_camera(self, image : QImage):
        self.ui.RearCameraViewLabel.setPixmap(QPixmap.fromImage(image))

    def update_front_label(self, messages : dict):
        for key, message in messages.items():
            if key == "status":
                self.ui.frontStatus.setText(message)
            #elif key == "response":
            #    self.ui.frontResponse.setText(message)

    def update_rear_label(self, messages : dict):
        for key, message in messages.items():
            if key == "status":
                self.ui.rearStatus.setText(message)
            #elif key == "response":
            #    self.ui.rearResponse.setText(message)
        
    def frontConnect_clicked(self):
        self.front_camera.server_connect()
        self.ui.frontConnect.setDisabled(True)
        self.ui.frontDisconnect.setDisabled(False)

    def frontDisconnect_clicked(self):
        self.front_camera.server_disconnect()
        self.ui.frontConnect.setDisabled(False)
        self.ui.frontDisconnect.setDisabled(True)

    def rearConnect_clicked(self):
        self.rear_camera.server_connect()
        self.ui.rearConnect.setDisabled(True)
        self.ui.rearDisconnect.setDisabled(False)

    def rearDisconnect_clicked(self):
        self.rear_camera.server_disconnect()
        self.ui.rearConnect.setDisabled(False)
        self.ui.rearDisconnect.setDisabled(True)
        
        


class FrontCameraThread(QThread):
    init_camera_signal  = pyqtSignal(QGlPicamera2)  # Slot For UI Init
    update_label_signal = pyqtSignal(dict)          # Slot For UI Update

    def __init__(self):
        super().__init__() # QThread init
        self.picam2 = Picamera2()
        self.video_config = self.picam2.create_preview_configuration(
            main={"size": (1280, 1280), "format": "XRGB8888"},
            lores={"size": (640, 640), "format": "RGB888"}
        )
        self.picam2.configure(self.video_config)
        self.server_connection = False
        self.qpicamera2 = QGlPicamera2(self.picam2, width=640, height=640, keep_ar=False)
        self.picam2.start()
        self.yoloThread = YOLOSendThread("Front")
        self.yoloThread.result_signal.connect(self.update_label_signal)
        

    def run(self):
        self.init_camera_signal.emit(self.qpicamera2)

        while True:
            start_time = time.time()

            # Capture
            frame = self.picam2.capture_array("lores")

            #print(f"Front Camera Frame Info")
            #print(f"Frame shape: {frame.shape}")
            #print(f"Frame dtype: {frame.dtype}")
            #print(f"Frame range: {frame.min()} - {frame.max()}")

            self.yoloThread.set_args(frame, self.server_connection)
            self.yoloThread.start()

            elapsed_msec = int((time.time() - start_time) * 1000)
            if (elapsed_msec < 1000):
                self.msleep(1000 - elapsed_msec)

    def server_connect(self):
        self.server_connection = True

    def server_disconnect(self):
        self.server_connection = False

    

class RearCameraThread(QThread):
    update_frame_signal = pyqtSignal(QImage)  # Slot For UI Update
    update_label_signal = pyqtSignal(dict)    # Slot For UI Update

    def __init__(self):
        super().__init__() # QThread init
        #v4l2-ctl --list-devices : for Check Camera Index
        self.cvcam = cv2.VideoCapture(8, cv2.CAP_V4L2)
        self.cvcam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cvcam.set(cv2.CAP_PROP_FRAME_HEIGHT, 640) 
        self.cvcam.set(cv2.CAP_PROP_FPS, 20)
        self.cvcam.set(cv2.CAP_PROP_BUFFERSIZE, 1) 
        #V4L2는 프레임 버퍼를 계속 누적함. 1로 설정하여 최신 프레임만 받도록 함
        self.server_connection = False
        self.yoloThread = YOLOSendThread("Rear", BGR2RGB=True)
        self.yoloThread.result_signal.connect(self.update_label_signal)
        

    def run(self):
        last_yolo_time = time.time()

        while True:
            # Capture (frame : NumPy Array)
            ret, frame = self.cvcam.read()
            if not ret: # Error Handling
                self.update_status_signal.emit("Error : Cannot Read Rear Camera")
                break
            
            # 1. Shrink Image and Run Inference
            frame = cv2.resize(frame, (640, 640))

            # print(f"Rear Camera Frame Info")
            # print(f"Frame shape: {frame.shape}")
            # print(f"Frame dtype: {frame.dtype}")
            # print(f"Frame range: {frame.min()} - {frame.max()}")

            # 2. Draw Captured Image to Screen 
            h, w, c = frame.shape
            qimg = QImage(frame.data, w, h, w * c, QImage.Format.Format_BGR888)
            self.update_frame_signal.emit(qimg)

            # 3. Run YOLO Every 1 Second
            if time.time() - last_yolo_time > 1:
                self.yoloThread.set_args(frame, self.server_connection)
                self.yoloThread.start()
                last_yolo_time = time.time()
            
            

    def server_connect(self):
        self.server_connection = True

    def server_disconnect(self):
        self.server_connection = False

    # def pixelFormatCheck(self, frame):
    #     fourcc_int = int(self.cvcam.get(cv2.CAP_PROP_FOURCC))
    #     fourcc = "".join([chr((fourcc_int >> (8*i)) & 0xFF) for i in range(4)])
    #     print("Current FOURCC format:", fourcc)


class YOLOSendThread(QThread):
    result_signal = pyqtSignal(dict)  # Slot For return Result

    def __init__(self, camera_type : str, BGR2RGB=False):
        super().__init__() # QThread init
        self.camera_type = camera_type
        self.bgr2rgb = BGR2RGB
        self.ncnn_model = YOLO("./yolov11n-face_ncnn_model")
        self.server_url = "http://14.47.213.122:9978/upload"
        self.labels = {}
    
    def set_args(self, frame, server_connection):
        self.frame = frame 
        self.server_connection = server_connection

    def run(self):
        self.labels = {}
        print(f"{self.camera_type} Camera Result : ")
        if self.bgr2rgb:
            self.frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
        result = self.ncnn_model.predict(self.frame, conf=0.5)[0] 

        if any(result.boxes):
            confidence_msg = ''
            for box in result.boxes:
                confidence_msg += f"{box.conf}" + ', '
            self.labels["status"] = f"{len(result.boxes)} Faces Detected, with Confidence: {confidence_msg}"
            
            if self.server_connection is True:
                try:
                    # Frame to JPEG Encoding                    
                    _, img_encoded = cv2.imencode('.jpg', self.frame)
                    is_front = 1 if self.camera_type == "Front" else 0
                    response = requests.post(self.server_url, files={"image": img_encoded.tobytes(), "is_front": is_front})
                    # Improved Version : {"image" : img_encoded.tobytes(), "is_front" : 1 / 0}

                    self.printResponse(response)
                    #self.tryJsonify(response)
                    # Reset Timeout when Response is received
                except requests.exceptions.RequestException as e:
                    self.labels["response"] = f"RequestError : {str(e)}"
                except Exception as e:
                    self.labels["response"] = f"Others Error : {str(e)}"
        else:
            self.labels["status"] = "No Face Detected"

        self.result_signal.emit(self.labels)


    def printResponse(self, response : requests.Response):
        response_dic : dict = eval(response._content.decode())[0]
        if "embedding" in response_dic:
            response_dic["embedding"] = response_dic["embedding"][:3]
        print("-- Front Camera Response --")
        pp = pprint.PrettyPrinter(compact=True)
        pp.pprint(response_dic)

    def tryJsonify(self, response : requests.Response):
        try: #Jsonnnable Check
            response.json()
            print("Can JSONify")
        except:
            print("Cannot JSONify")

main()
