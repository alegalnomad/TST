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

def remove_shadows(image, amount=0.4):
    rgb_planes = cv2.split(image)
    result_planes = []
    
    for plane in rgb_planes:
        dilated_img = cv2.dilate(plane, np.ones((7,7), np.uint8))
        bg_img = cv2.medianBlur(dilated_img, 21)
        diff_img = 255 - cv2.absdiff(plane, bg_img)
        
        # Blend the original and the shadow-free image
        result_planes.append(cv2.addWeighted(plane, 1 - amount, diff_img, amount, 0))
    
    result = cv2.merge(result_planes)
    return result

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

            original_cropped = img.copy()
            original_cropped = cv2.cvtColor(original_cropped, cv2.COLOR_BGR2RGB)

            logging.info("Starting hair removal")
            img_no_hair = hairremoval(img)
            logging.info("Hair removal complete")
                # preprocess: cut-off and max-min normalization
            lower_bound, upper_bound = np.percentile(img_no_hair, 1), np.percentile(img_no_hair, 99)
            image_data_pre = np.clip(img_no_hair, lower_bound, upper_bound)
            image_data_pre = (image_data_pre - np.min(image_data_pre))/(np.max(image_data_pre)-np.min(image_data_pre))*255.0
            image_data_pre[img_no_hair==0] = 0
            image_data_pre = np.uint8(image_data_pre)   

            image_no_shadow = remove_shadows(image_data_pre)

            blur = cv2.GaussianBlur(image_no_shadow, (3, 3), 0)

            b, g, r = cv2.split(blur)

            alpha = 1 
            beta = 1.6

            modified_g = cv2.multiply(g, alpha)
            modified_r = cv2.multiply(r, beta)
            modified_b = cv2.multiply(b, beta)

            modified_img = cv2.merge((modified_b, modified_g, modified_r))
            modified_img = np.clip(modified_img, 0, 255).astype(np.uint8)

            logging.info("Starting bounding box detection")
            bbox = bounding_box(modified_img)
            print("Bounding Box: ", bbox)
            logging.info("Bounding box detection complete")

            logging.info("Starting area prediction")
            prediction = area_predict(image_data_pre, bbox)
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
