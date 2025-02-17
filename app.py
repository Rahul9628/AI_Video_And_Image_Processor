from flask import Flask, render_template, request, jsonify
import os
import cv2
import numpy as np
from werkzeug.utils import secure_filename
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
import torch

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1GB
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'mp4', 'mov'}

# Initialize BLIP model
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def extract_keyframes(video_path, num_frames=5):
    cap = cv2.VideoCapture(video_path)
    frames = []
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Select evenly spaced frames
    indices = np.linspace(0, total_frames-1, num=num_frames, dtype=int)
    
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if ret:
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    cap.release()
    return frames

def generate_caption(image_path):
    raw_image = Image.open(image_path).convert('RGB')
    inputs = processor(raw_image, return_tensors="pt")
    out = model.generate(**inputs, max_length=50)
    return processor.decode(out[0], skip_special_tokens=True)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_type = 'videos' if filename.lower().endswith(('mp4', 'mov')) else 'images'
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], file_type, filename)
        file.save(save_path)
        
        if file_type == 'videos':
            keyframes = extract_keyframes(save_path)
            results = []
            for i, frame in enumerate(keyframes):
                img_path = os.path.join(app.config['UPLOAD_FOLDER'], 'images', f'frame_{i}_{filename}.jpg')
                Image.fromarray(frame).save(img_path)
                caption = generate_caption(img_path)
                results.append({
                    'frame': img_path.replace('\\', '/'),  # Windows path fix
                    'caption': caption
                })
            return jsonify({'type': 'video', 'results': results})
        
        else:  # Image processing
            caption = generate_caption(save_path)
            return jsonify({
                'type': 'image',
                'path': save_path.replace('\\', '/'),
                'caption': caption
            })
    
    return jsonify({'error': 'Invalid file type'}), 400

if __name__ == '__main__':
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'images'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'videos'), exist_ok=True)
    app.run(debug=True)