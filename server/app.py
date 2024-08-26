from flask import Flask, request, jsonify, send_file
from yolopred import bounding_box
from hairremoval import hairremoval
from sampred import area_predict
import cv2
import numpy as np 
import io
import logging
from PIL import Image

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def read_image_file(file):
    nparr = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img
def center_crop(image, crop_width, crop_height):
    img_height, img_width = image.shape[:2]
    
    # Calculate the crop coordinates
    x1 = max(0, img_width // 2 - crop_width // 2)
    y1 = max(0, img_height // 2 - crop_height // 2)
    x2 = min(img_width, x1 + crop_width)
    y2 = min(img_height, y1 + crop_height)
    
    # Crop the image
    return image[y1:y2, x1:x2]

@app.route('/predict', methods=['POST'])
def predict():
    if request.method == 'POST':
        file = request.files.get('file')
        if file is None or file.filename == "":
            return jsonify({'error': 'no file'}), 400
        if not allowed_file(file.filename):
            return jsonify({'error': 'format not supported'}), 400

        try:
            logging.info(f"Received file: {file.filename}, Size: {file.content_length}")
        
            img = read_image_file(file)  

            crop_width = 600
            crop_height = 500

            # Perform center-weighted crop
            cropped_img = center_crop(img, crop_width, crop_height)
           
            original_cropped = cropped_img.copy()
            original_cropped = cv2.cvtColor(original_cropped, cv2.COLOR_BGR2RGB)

            logging.info("Starting hair removal")
            img_no_hair = hairremoval(cropped_img)
            logging.info("Hair removal complete")

            blur = cv2.GaussianBlur(img_no_hair, (5, 5), 0)

            # Split the blurred image into color channels
            b, g, r = cv2.split(blur)

            # Reduce the effect of the green channel and enhance red and blue
            alpha = 0.55  # Factor to reduce green channel
            beta = 1.2   # Factor to enhance red and blue channels

            modified_g = cv2.multiply(g, alpha)
            modified_r = cv2.multiply(r, beta)
            modified_b = cv2.multiply(b, beta)

            # Merge the channels back
            modified_img = cv2.merge((modified_b, modified_g, modified_r))

            # Clip values to ensure they're in the valid range [0, 255]
            modified_img = np.clip(modified_img, 0, 255).astype(np.uint8)
            #normalized_image = cv2.normalize(modified_img, None, 100, 255, cv2.NORM_MINMAX)
            # Clip values to ensure they're in the valid range [0, 255]
            modified_img= np.clip(modified_img, 0, 255).astype(np.uint8)

            logging.info("Starting bounding box detection")
            bbox = bounding_box(modified_img)
            print("Bounding Box: ", bbox)
            logging.info("Bounding box detection complete")

            logging.info("Starting area prediction")
            prediction = area_predict(img_no_hair, bbox)
            logging.info("Area prediction complete")
            if len(prediction.shape) == 2 or prediction.shape[2] == 1:
                prediction = cv2.cvtColor(prediction, cv2.COLOR_GRAY2RGB)
        
            
            prediction = cv2.cvtColor(prediction, cv2.COLOR_BGR2RGB)
            
            combined_img = np.vstack((original_cropped, prediction))
                                     
            img = Image.fromarray(combined_img)
            img_io = io.BytesIO()
            img.save(img_io, 'PNG', quality=100)
            img_io.seek(0)
            
            return send_file(img_io, mimetype='image/png')
        
        except Exception as e:
            logging.error(f"Error during prediction: {str(e)}")
            return jsonify({'error': f'Error during prediction: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)