import cv2

#v4l2-ctl --list-devices 로 확인
cap = cv2.VideoCapture(8)


if not cap.isOpened():
    print("ī�޶� �� �� �����ϴ�. GStreamer ��� Video4Linux2�� ����� ������.")
else:
    print("ī�޶� ���������� ���Ƚ��ϴ�.")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("�������� ���� �� �����ϴ�.")
            break
        
        cv2.imshow("Camera Test", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
