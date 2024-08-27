import cv2
import numpy as np
import os


def mask_to_yolo(mask_image):
                    
    # Get image dimensions
    height, width = mask_image.shape
    yolo_annotations = []
    if np.any(mask_image > 0):
        #Generating bounding box from ground truth
        y_indices, x_indices = np.where(mask_image > 0)
        x_min, x_max = np.min(x_indices), np.max(x_indices)
        y_min, y_max = np.min(y_indices), np.max(y_indices)
        # add perturbation to bounding box coordinates
        x_min = max(0, x_min - np.random.randint(0, 20))
        x_max = min(width, x_max + np.random.randint(0, 20))
        y_min = max(0, y_min - np.random.randint(0, 20))
        y_max = min(height, y_max + np.random.randint(0, 20))
            
        # Convert to YOLO format
        x_center = (x_max + x_min) / (2*width)
        y_center = (y_max + y_min) /(2*height)
        norm_width = (x_max-x_min) / width
        norm_height = (y_max-y_min) / height
        
        # Assume class 0 for this example
        yolo_annotation = f"0 {x_center:.6f} {y_center:.6f} {norm_width:.6f} {norm_height:.6f}"
        yolo_annotations.append(yolo_annotation)

    return yolo_annotations
   
        


def process_masks(mask_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filename in os.listdir(mask_dir):
        if filename.endswith(('.png', '.jpg', '.jpeg')):  # Add other extensions if needed
            mask_path = os.path.join(mask_dir, filename)
            mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
            
            yolo_annotations = mask_to_yolo(mask)
            
            # Create a text file with the same name as the image
            base_name = os.path.splitext(filename)[0]
            # base_name = base_name.split("_")
            # print(base_name)
            # base_name = f"{base_name[0]}_{base_name[1]}"
            print(base_name)
            txt_filename = f"{base_name}.txt"
            txt_path = os.path.join(output_dir, txt_filename)
            
            # Write annotations to the text file
            with open(txt_path, 'w') as f:
                for annotation in yolo_annotations:
                    f.write(annotation)
            
            print(f"Processed {filename} and saved annotations to {txt_filename}")


# Example usage
mask_directory = "C:/Users/anand/OneDrive - The University of Nottingham/MScProject/YOLO/train/masks"
output_directory = "C:/Users/anand/OneDrive - The University of Nottingham/MScProject/YOLO/train/labels"

process_masks(mask_directory, output_directory)