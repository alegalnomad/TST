import cv2

def hairremoval(image):

    grayScale = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    
    # Black hat filter
    kernel = cv2.getStructuringElement(1, (9, 9))
    blackhat = cv2.morphologyEx(grayScale, cv2.MORPH_BLACKHAT, kernel)
    
    # Gaussian filter
    bhg = cv2.GaussianBlur(blackhat, (3, 3), cv2.BORDER_DEFAULT)
    
    # Binary thresholding (MASK)
    ret, mask = cv2.threshold(bhg, 10, 255, cv2.THRESH_BINARY)
    
    if len(image.shape) == 3:
        dst = cv2.inpaint(image, mask, 6, cv2.INPAINT_TELEA)
    else:
        # If input was grayscale, convert result back to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        dst = cv2.inpaint(image_rgb, mask, 6, cv2.INPAINT_TELEA)
    
    return dst