import numpy as np
import torch
from segment_anything import sam_model_registry
from segment_anything.utils.transforms import ResizeLongestSide
import cv2

# Load Model (do this only once when the app starts)
sam_model = sam_model_registry['vit_b'](checkpoint="sam_model_latest.pth")
sam_transform = ResizeLongestSide(1024)

def area_predict(image, box):
        
    if len(box) == 0:
        return image  # Return the original image if no bounding box is detected

    # Ensure box is in the correct format
    box = np.array(box).reshape(1, 4)  # Reshape to (1, 4)
    print(box)
    input_size = image.shape[:2]
    print(f"input image size: {input_size}")
    
    resized_image = cv2.resize(image, (600, 450))

    resize_image = sam_transform.apply_image(resized_image)
    print(f'resize image: {resize_image.shape}')
    image_tensor = torch.from_numpy(resize_image).float().permute(2, 0, 1)
    input_image = sam_model.preprocess(image_tensor.unsqueeze(0))  # Add batch dimension
    print(f'preprocessed image: {input_image.shape}')

    with torch.no_grad():
        # Pre-compute the image embedding
        ts_img_embedding = sam_model.image_encoder(input_image)
        
        # Convert box to 1024x1024 grid
        bbox = sam_transform.apply_boxes(box, input_size)
        box_torch = torch.as_tensor(bbox, dtype=torch.float, device=sam_model.device)
        box_torch = box_torch.unsqueeze(1)  # (1, 1, 4)
        
        sparse_embeddings, dense_embeddings = sam_model.prompt_encoder(
            points=None,
            boxes=box_torch,
            masks=None,
        )
        sam_seg_prob, _ = sam_model.mask_decoder(
            image_embeddings=ts_img_embedding,
            image_pe=sam_model.prompt_encoder.get_dense_pe(),
            sparse_prompt_embeddings=sparse_embeddings,
            dense_prompt_embeddings=dense_embeddings,
            multimask_output=False,
        )
        
        upscaled_masks = sam_model.postprocess_masks(sam_seg_prob, (256,256) ,input_size)
        sam_seg_prob = torch.sigmoid(upscaled_masks)
        sam_seg = (sam_seg_prob > 0.5).cpu().numpy().squeeze().astype(np.uint8)
        print("training complete")
    # Create a colored mask
    mask_color = np.array([251, 252, 30], dtype=np.uint8)  # Yellow color
    colored_mask = np.zeros((*sam_seg.shape, 3), dtype=np.uint8)
    colored_mask[sam_seg == 1] = mask_color

    # Blend the mask with the original image
    alpha = 0.3
    image_with_mask = cv2.addWeighted(image, 1, colored_mask, alpha, 0)

    # Draw bounding box
    x0, y0, x1, y1 = map(int, box[0])
    cv2.rectangle(image_with_mask, (x0, y0), (x1, y1), (0, 255, 0), 2)

    return image_with_mask