from ultralytics import YOLO
import numpy as np
import cv2

# Load a model
model = YOLO("C:/Users/anand/OneDrive - The University of Nottingham/MScProject/app/best.pt")  # pretrained YOLOv8n model

def resize_image(img, target_size=(600, 450)):
    return cv2.resize(img, target_size)

def center_weighted_crop(image, crop_size=(600, 450)):
    h, w = image.shape[:2]
    ch, cw = crop_size
    
    # Calculate the crop coordinates
    top = max(0, (h - ch) // 2)
    left = max(0, (w - cw) // 2)
    bottom = min(h, top + ch)
    right = min(w, left + cw)
    
    # Perform the crop
    cropped = image[top:bottom, left:right]
    
    # Resize if necessary
    if cropped.shape[:2] != crop_size:
        cropped = cv2.resize(cropped, crop_size)
    
    return cropped, (left, top, right, bottom)

def bounding_box(image):
    try:
        print("Trying YOLOInfer with center-weighted crop")
        
        # Perform center-weighted crop
        crop_size = (600, 450)
        cropped_image, crop_coords = center_weighted_crop(image, crop_size)
        
        # Run inference on cropped image
        results = model([cropped_image], stream=True)

        for result in results:
            boxes = result.boxes

        if len(boxes) > 0:
            # Get the bounding box coordinates in the cropped image
            crop_box = boxes.xyxy[0].cpu().numpy()
            
            # Adjust bounding box coordinates to the original image
            left, top, right, bottom = crop_coords
            original_box = np.array([
                crop_box[0] + left,
                crop_box[1] + top,
                crop_box[2] + left,
                crop_box[3] + top
            ])
            
            return original_box

    except Exception as e:
        print(f"YOLOInfer with center-weighted crop failed: {str(e)}")
        pass

    return np.array([]) 