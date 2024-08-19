import numpy as np
import torch
from segment_anything import sam_model_registry
from segment_anything.utils.transforms import ResizeLongestSide
import cv2

#Load model
sam_model = sam_model_registry['vit_b'](checkpoint="Re_sam_model_best.pth")
sam_model.to(torch.device('cpu'))
sam_transform = ResizeLongestSide(1024)

def clip_mask_to_box(mask, box):
    x0, y0, x1, y1 = map(int, box)
    clipped_mask = np.zeros_like(mask)
    clipped_mask[y0:y1, x0:x1] = mask[y0:y1, x0:x1]
    return clipped_mask

def area_predict(image, box):
    if len(box) == 0: #return the image as is if there was no bounding box detected
        return image,400  
    
    box = np.array(box).reshape(1, 4) 
    input_size = image.shape[:2]

    # preprocess: cut-off and max-min normalization
    lower_bound, upper_bound = np.percentile(image, 0.5), np.percentile(image, 99.5)
    image_data_pre = np.clip(image, lower_bound, upper_bound)
    image_data_pre = (image_data_pre - np.min(image_data_pre))/(np.max(image_data_pre)-np.min(image_data_pre))*255.0
    image_data_pre[image==0] = 0
    image_data_pre = np.uint8(image_data_pre)    

    #resizing the image
    resized_image = cv2.resize(image_data_pre, (600, 450))
    resize_image = sam_transform.apply_image(resized_image)
    image_tensor = torch.from_numpy(resize_image).float().permute(2, 0, 1) #Convert to C,H,W
    input_image = sam_model.preprocess(image_tensor.unsqueeze(0))  
    

    with torch.no_grad():
        
        ts_img_embedding = sam_model.image_encoder(input_image)
        
        bbox = sam_transform.apply_boxes(box, input_size)
        box_torch = torch.as_tensor(bbox, dtype=torch.float, device=sam_model.device)
        box_torch = box_torch.unsqueeze(1) 
        
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
        
        upscaled_masks = sam_model.postprocess_masks(sam_seg_prob, (256,256), input_size)
        sam_seg_prob = torch.sigmoid(upscaled_masks)
        
        threshold = 0.9
        sam_seg = (sam_seg_prob > threshold).cpu().numpy().squeeze().astype(np.uint8)
        
        # Clip the mask to the bounding box
        sam_seg = clip_mask_to_box(sam_seg, box[0])

    # Create a colored mask
    mask_color = np.array([30, 252, 251])  
    colored_mask = np.zeros((*sam_seg.shape, 3), dtype=np.uint8)
    colored_mask[sam_seg == 1] = mask_color

    # Blend the mask with the original image
    alpha = 0.3
    image_with_mask = cv2.addWeighted(image, 1, colored_mask, alpha, 0)

    # Draw bounding box
    x0, y0, x1, y1 = map(int, box[0])
    cv2.rectangle(image_with_mask, (x0, y0), (x1, y1), (0, 255, 0), 2)

    return image_with_mask