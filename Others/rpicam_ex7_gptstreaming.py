#!/usr/bin/python3

import socket
import time
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput

SERVER_IP = "172.30.1.92" 
SERVER_PORT = 10001        

# Picamera2 �� H264Encoder ����
picam2 = Picamera2()
video_config = picam2.create_video_configuration({"size": (1280, 720)})
picam2.configure(video_config)
encoder = H264Encoder(bitrate=1000000) 

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    try:
        sock.connect((SERVER_IP, SERVER_PORT))
        print(f"Connected to {SERVER_IP}:{SERVER_PORT}")
        
        stream = sock.makefile("wb")
        encoder.output = FileOutput(stream)
        picam2.start_encoder(encoder)
        picam2.start()
        
        time.sleep(20)  

        picam2.stop()
        picam2.stop_encoder()
        print("Streaming ended.")
        
    except socket.error as e:
        print(f"Socket error: {e}")
