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
           
            logging.info("Starting hair removal")
            img_no_hair = hairremoval(img)
            logging.info("Hair removal complete")
            
            logging.info("Starting bounding box detection")
            bbox = bounding_box(img_no_hair)
            print("Bounding Box: ", bbox)
            logging.info("Bounding box detection complete")

            logging.info("Starting area prediction")
            prediction = area_predict(img_no_hair, bbox)
            logging.info("Area prediction complete")
            if len(prediction.shape) == 2 or prediction.shape[2] == 1:
                prediction = cv2.cvtColor(prediction, cv2.COLOR_GRAY2RGB)
        
            
            prediction = cv2.cvtColor(prediction, cv2.COLOR_BGR2RGB)
            
            img = Image.fromarray(prediction)
            img_io = io.BytesIO()
            img.save(img_io, 'PNG', quality=100)
            img_io.seek(0)
            
            return send_file(img_io, mimetype='image/png')
        
        except Exception as e:
            logging.error(f"Error during prediction: {str(e)}")
            return jsonify({'error': f'Error during prediction: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)