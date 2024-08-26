from ultralytics import YOLO
import numpy as np
import cv2

model = YOLO("best.pt") 

def resize_image(img, target_size=(600, 450)):
    return cv2.resize(img, target_size)

def bounding_box(image):

    try:
        print("Trying YOLOInfer")
        results = model([image], stream=True) 


        for result in results:
            boxes = result.boxes  
        if len(boxes)>0:
            return np.array(boxes.xyxy[0].cpu())
    
    except:
        print("YOLOInfer failed")
        pass

    return np.array([])  