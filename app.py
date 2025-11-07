import os
import cv2
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Detect Render vs Local
if os.environ.get('RENDER'):
    BASE_OUTPUT_DIR = '/tmp/INDOWINGS_OUTPUT'
    UPLOAD_FOLDER = '/tmp/uploads'
else:
    BASE_OUTPUT_DIR = os.path.join(os.getcwd(), 'INDOWINGS_OUTPUT')
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')

os.makedirs(BASE_OUTPUT_DIR, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    try:
        files = request.files.getlist('files[]')
        output_choice = request.form.get('output_folder', 'INDOWINGS_OUTPUT')
        if not files:
            return jsonify({'status': 'error', 'message': 'No files uploaded!'})

        output_path = os.path.join(BASE_OUTPUT_DIR, output_choice)
        os.makedirs(output_path, exist_ok=True)
        sr_urls = []

        for file in files:
            filename = file.filename
            upload_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(upload_path)

            # Process: extract frames
            video_cap = cv2.VideoCapture(upload_path)
            frame_dir = os.path.join(output_path, os.path.splitext(filename)[0] + '_frames')
            os.makedirs(frame_dir, exist_ok=True)

            frame_count = 0
            while True:
                ret, frame = video_cap.read()
                if not ret:
                    break
                frame_path = os.path.join(frame_dir, f'frame_{frame_count:04d}.jpg')
                cv2.imwrite(frame_path, frame)
                frame_count += 1
            video_cap.release()

            sr_urls.append(f'/download/{output_choice}/{os.path.basename(frame_dir)}')

        return jsonify({'status': 'success', 'sr_urls': sr_urls})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/download/<output_choice>/<folder>')
def download_folder(output_choice, folder):
    folder_path = os.path.join(BASE_OUTPUT_DIR, output_choice, folder)
    return send_from_directory(folder_path, '')

@app.route('/open-output-folder', methods=['GET'])
def open_output_folder():
    dirs = os.listdir(BASE_OUTPUT_DIR)
    return jsonify({'folders': dirs})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
