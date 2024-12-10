from ultralytics import YOLO

# Load the exported NCNN model
ncnn_model = YOLO("./yolov11n-face_ncnn_model")

# Run inference
results = ncnn_model("https://ultralytics.com/images/bus.jpg")

for result in results:
    boxes = result.boxes  # Boxes object for bounding box outputs
    masks = result.masks  # Masks object for segmentation masks outputs
    keypoints = result.keypoints  # Keypoints object for pose outputs
    probs = result.probs  # Probs object for classification outputs
    obb = result.obb  # Oriented boxes object for OBB outputs
    result.show()  # display to screen
    result.save(filename="result.jpg")  # save to disk
