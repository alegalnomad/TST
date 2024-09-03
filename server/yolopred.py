from ultralytics import YOLO
import numpy as np
import cv2

# Load a model
model = YOLO("best.pt")  # pretrained YOLOv8n model

def resize_image(img, target_width=600):
    h, w = img.shape[:2]
    aspect_ratio = h / w
    target_height = int(target_width * aspect_ratio)
    return cv2.resize(img, (target_width, target_height))

def horizontal_center_crop(image, target_width=600):
    h, w = image.shape[:2]
    
    if w <= target_width:
        return image, (0, 0, w, h)
    
    # Calculate the crop coordinates
    left = max(0, (w - target_width) // 2)
    right = min(w, left + target_width)
    
    # Perform the crop
    cropped = image[:, left:right]
    
    return cropped, (left, 0, right, h)

def bounding_box(image):
    try:
        print("Trying YOLOInfer with horizontal center crop")
        
        # Perform horizontal center crop
        target_width = 600
        cropped_image, crop_coords = horizontal_center_crop(image, target_width)
        
        # Resize the cropped image to maintain aspect ratio
        resized_image = resize_image(cropped_image, target_width)
        
        # Run inference on resized image
        results = model([resized_image], stream=True)

        for result in results:
            boxes = result.boxes

        if len(boxes) > 0:
            # Get the bounding box coordinates in the resized image
            resize_box = boxes.xyxy[0].cpu().numpy()
            
            # Adjust bounding box coordinates to the original image
            left, _, right, _ = crop_coords
            crop_width = right - left
            scale_factor = crop_width / target_width
            
            original_box = np.array([
                resize_box[0] * scale_factor + left,
                resize_box[1] * scale_factor,
                resize_box[2] * scale_factor + left,
                resize_box[3] * scale_factor
            ])
            
            return original_box

    except Exception as e:
        print(f"YOLOInfer with horizontal center crop failed: {str(e)}")
        pass

    return np.array([])  # Return an empty array if no bounding box is detected
