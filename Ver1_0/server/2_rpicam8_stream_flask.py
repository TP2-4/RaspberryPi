from flask import Flask, Response, render_template
import socket
import cv2
import numpy as np
import threading

app = Flask(__name__)

# 서버 IP 및 포트 설정
TCP_IP = '0.0.0.0'  # 모든 인터페이스에서 수신
TCP_PORT = 10001

# 글로벌 변수로 프레임 데이터를 관리
frame_data = None

def socket_server():
    global frame_data
    # TCP 소켓 설정 및 대기
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((TCP_IP, TCP_PORT))
    sock.listen(1)
    print("Waiting for connection...")
    conn, addr = sock.accept()
    print('Connection address:', addr)

    try:
        while True:
            # 프레임 크기 수신
            length_data = conn.recv(4)
            if not length_data:
                break
            length = int.from_bytes(length_data, byteorder='big')

            # 프레임 데이터 수신
            data = b''
            while len(data) < length:
                packet = conn.recv(length - len(data))
                if not packet:
                    break
                data += packet

            # 프레임을 디코딩하여 전역 변수로 저장
            frame = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
            if frame is not None:
                _, buffer = cv2.imencode('.jpg', frame)
                frame_data = buffer.tobytes()

    finally:
        conn.close()
        sock.close()

def generate_frames():
    global frame_data
    while True:
        if frame_data is None:
            continue
        # 수신된 프레임을 yield 하여 웹 페이지에 스트리밍
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')

@app.route('/')
def index():
    return render_template('rpicam8.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    # 소켓 서버를 별도의 스레드에서 실행
    socket_thread = threading.Thread(target=socket_server, daemon=True)
    socket_thread.start()
    
    # Flask 서버 실행
    app.run(host='0.0.0.0', port=5000)
