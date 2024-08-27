import os
import shutil
import numpy as np
from PIL import Image
from sklearn.model_selection import train_test_split

def load_data(image_dir, mask_dir):
    images = []
    masks = []
    image_paths = []
    mask_paths = []
    
    for filename in sorted(os.listdir(image_dir)):
        if filename.endswith(('.png', '.jpg', '.jpeg')):
            # Load image
            img_path = os.path.join(image_dir, filename)
            img = np.array(Image.open(img_path).convert('RGB'))
            images.append(img)
            image_paths.append(img_path)
            
            # Load corresponding mask
            mask_filename = filename 
            mask_path = os.path.join(mask_dir, mask_filename)
            mask = np.array(Image.open(mask_path).convert('L'))  # Convert to grayscale
            masks.append(mask)
            mask_paths.append(mask_path)
    
    return np.array(images), np.array(masks), image_paths, mask_paths

def split_and_save_data(X, y, image_paths, mask_paths, output_base_dir, test_size=0.1, random_state=42):
    # Perform train-test split
    X_train, X_test, y_train, y_test, train_img_paths, test_img_paths, train_mask_paths, test_mask_paths = train_test_split(
        X, y, image_paths, mask_paths, test_size=test_size, random_state=random_state
    )

    # Create output directories
    dirs = {
        'train_images': os.path.join(output_base_dir, 'train', 'images'),
        'train_masks': os.path.join(output_base_dir, 'train', 'masks'),
        'test_images': os.path.join(output_base_dir, 'test', 'images'),
        'test_masks': os.path.join(output_base_dir, 'test', 'masks')
    }
    
    for dir_path in dirs.values():
        os.makedirs(dir_path, exist_ok=True)
    # Function to copy files
    def copy_files(img_paths, mask_paths, image_dir, mask_dir):
        for img_path, mask_path in zip(img_paths, mask_paths):
            shutil.copy2(img_path, os.path.join(image_dir, os.path.basename(img_path)))
            shutil.copy2(mask_path, os.path.join(mask_dir, os.path.basename(mask_path)))

    # Copy train files
    copy_files(train_img_paths, train_mask_paths, dirs['train_images'], dirs['train_masks'])

    # Copy test files
    copy_files(test_img_paths, test_mask_paths, dirs['test_images'], dirs['test_masks'])

    print(f"Train images: {len(X_train)}")
    print(f"Test images: {len(X_test)}")

def main():
    # Set your directories here
    image_dir = "C:/Users/anand/Desktop/Wound Segmentation/data/images"
    mask_dir = "C:/Users/anand/Desktop/Wound Segmentation/data/labels"
    output_base_dir = "C:/Users/anand/Desktop/Wound Segmentation"

    # Load the data
    X, y, image_paths, mask_paths = load_data(image_dir, mask_dir)

    print(f"Loaded {len(X)} images and masks")
    print(f"Image shape: {X[0].shape}")
    print(f"Mask shape: {y[0].shape}")

    # Split and save the data
    split_and_save_data(X, y, image_paths, mask_paths, output_base_dir)

    print("Data split and saved successfully!")

if __name__ == "__main__":
    main()