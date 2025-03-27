import cv2
import torch
from ultralytics import YOLO

model = YOLO("yolo11l.pt")  # Ensure you have the correct model file

cap = cv2.VideoCapture(0)  # Use 0 for the default webcam

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    
    # Perform object detection
    results = model(frame)
    
    # Draw detection results on the frame
    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])  # Bounding box coordinates
            confidence = box.conf[0].item()  # Confidence score
            label = result.names[int(box.cls[0])]  # Class name
            
            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"{label} {confidence:.2f}", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    # Show the processed frame
    cv2.imshow("YOLO11 Object Detection", frame)
    
    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
