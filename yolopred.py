from ultralytics import YOLO
import numpy as np
import cv2

# Load a model
model = YOLO("yolofinetuned.pt")  # pretrained YOLOv8n model

def resize_image(img, target_size=(600, 450)):
    return cv2.resize(img, target_size)

def bounding_box(image):

    try:
        print("Trying Original YOLOPred")
        # Resize image
        original_size = image.shape[:2]  # (height, width)
        resized_image = resize_image(image)
        
        # Run inference on images
        results = model([resized_image], stream=True)  # return a generator of Results objects

        # Process results generator
        for result in results:
            boxes = result.boxes  # Boxes object for bounding box outputs

        if len(boxes) > 0:
            dim = boxes.xyxy[0]
            dim_list = dim.cpu().tolist()
            
            # Adjust bounding box coordinates to original image size
            h_ratio = original_size[0] / 450
            w_ratio = original_size[1] / 600
            adjusted_dim = [
                dim_list[0] * w_ratio,
                dim_list[1] * h_ratio,
                dim_list[2] * w_ratio,
                dim_list[3] * h_ratio
            ]
            
            return np.array(adjusted_dim)  # Return as a 2D array
    except:
        print("Original failed")
        pass

    try:
        print("Trying YOLOInfer")
        results = model([image], stream=True)  # return a generator of Results objects


        for result in results:
            boxes = result.boxes  
        if len(boxes)>0:
            return np.array(boxes.xyxy[0].cpu())
    
    except:
        print("YOLOInfer failed")
        pass
    

        
        

    return np.array([])  # Return an empty array if no bounding box is detected
