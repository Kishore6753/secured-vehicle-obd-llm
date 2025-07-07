# receiver.py
from flask import Flask, request
import os
from datetime import datetime

app = Flask(__name__)
UPLOAD_DIR = "received_jsons"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.route('/upload-json', methods=['POST'])
def upload_json_file():
    if 'file' not in request.files:
        return {"status": "error", "message": "No file uploaded"}, 400

    uploaded_file = request.files['file']

    if uploaded_file.filename == '':
        return {"status": "error", "message": "Empty filename"}, 400

    if uploaded_file and uploaded_file.filename.endswith('.json'):
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"uploaded_{timestamp}.json"
        save_path = os.path.join(UPLOAD_DIR, filename)
        uploaded_file.save(save_path)
        return {"status": "success", "file": save_path}, 200

    return {"status": "error", "message": "Invalid file format"}, 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


