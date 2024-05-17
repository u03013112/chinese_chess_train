import cv2
from ultralytics import YOLO

modelFile = '/Users/u03013112/.pyenv/runs/detect/train6/weights/last.pt'
# Load a pretrained YOLOv8n model
model = YOLO(modelFile)

# Read an image using OpenCV
source = cv2.imread('/Users/u03013112/Documents/git/chinese_chess_train/yolo/images/val/2.jpg')
source = cv2.resize(source, (320, 320))

names = {0: 'A', 1: 'K', 2: 'B', 3: 'N', 4: 'P', 5: 'C', 6: 'R', 7: 'a', 8: 'c', 9: 'r', 10: 'p', 11: 'k', 12: 'b', 13: 'n'}

# Run inference on the source
results = model(source)  # list of Results objects

# Get the height and width of the image
height, width = source.shape[:2]

for result in results:
    # Get the bounding boxes and their labels
    boxes = result.boxes.xyxy  # box with xyxy format, (N, 4)
    labels = result.boxes.cls  # cls, (N, 1)

    # Draw the bounding boxes and labels on the image
    for i in range(len(boxes)):
        x1, y1, x2, y2 = [int(x) for x in boxes[i]]
        label = labels[i]
        name = names[int(label.item())]
        cv2.rectangle(source, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(source, name, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36,255,12), 2)

# Display the image
cv2.imshow('Image', source)
cv2.waitKey(0)
cv2.destroyAllWindows()
