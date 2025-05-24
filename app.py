import os
import cv2
import torch
from flask import Flask, request, redirect, url_for, render_template_string, Response
from werkzeug.utils import secure_filename
from PIL import Image

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
RESULT_FOLDER = 'static/results'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def detect_image(input_path, output_path):
    img = Image.open(input_path)
    results = model(img)
    results.render()
    result_img = results.ims[0]
    result_img = cv2.cvtColor(result_img, cv2.COLOR_RGB2BGR)
    cv2.imwrite(output_path, result_img)

# HTML templates with Bootstrap and colorful styling
INDEX_HTML = '''
<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>YOLOv5 Detection</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body {
      background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
      min-height: 100vh;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .card {
      background: white;
      border-radius: 15px;
      box-shadow: 0 8px 20px rgba(0,0,0,0.2);
    }
    h1 {
      color: #2575fc;
      font-weight: 700;
    }
    .btn-primary {
      background-color: #6a11cb;
      border: none;
    }
    .btn-primary:hover {
      background-color: #4a0ea2;
    }
    .btn-success {
      background-color: #2575fc;
      border: none;
    }
    .btn-success:hover {
      background-color: #0d47a1;
    }
    input[type="file"] {
      border-radius: 5px;
    }
  </style>
</head>
<body>
  <div class="container d-flex justify-content-center align-items-center" style="min-height: 100vh;">
    <div class="card p-5" style="width: 400px;">
      <h1 class="mb-4 text-center">YOLOv5 Object Detection</h1>
      <form method="post" enctype="multipart/form-data" class="mb-4">
        <input type="file" name="file" accept=".jpg,.jpeg,.png" required class="form-control mb-3" />
        <button type="submit" class="btn btn-success w-100">Upload Image & Detect</button>
      </form>
      <a href="/camera" class="btn btn-primary w-100">Start Real-Time Camera Detection</a>
    </div>
  </div>
</body>
</html>
'''

RESULT_HTML = '''
<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Detection Result</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body {
      background: linear-gradient(135deg, #2575fc 0%, #6a11cb 100%);
      min-height: 100vh;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .card {
      background: white;
      border-radius: 15px;
      box-shadow: 0 8px 20px rgba(0,0,0,0.25);
    }
    h1 {
      color: #2575fc;
      font-weight: 700;
    }
    .btn-secondary {
      background-color: #6a11cb;
      border: none;
    }
    .btn-secondary:hover {
      background-color: #4a0ea2;
    }
  </style>
</head>
<body>
  <div class="container d-flex justify-content-center align-items-center py-5" style="min-height: 100vh;">
    <div class="card p-4 text-center" style="max-width: 700px; width: 100%;">
      <h1 class="mb-4">Detection Result</h1>
      <img src="{{ url_for('static', filename='results/' + filename) }}" alt="Detected Image" class="img-fluid rounded border mb-4" />
      <a href="/" class="btn btn-secondary px-4">Back to Home</a>
    </div>
  </div>
</body>
</html>
'''

CAMERA_HTML = '''
<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Live Camera Detection</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body {
      background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
      min-height: 100vh;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .card {
      background: white;
      border-radius: 15px;
      box-shadow: 0 8px 20px rgba(0,0,0,0.3);
    }
    h1 {
      color: #2575fc;
      font-weight: 700;
    }
    .btn-danger {
      background-color: #d9534f;
      border: none;
    }
    .btn-danger:hover {
      background-color: #b52b27;
    }
    .btn-secondary {
      background-color: #6a11cb;
      border: none;
    }
    .btn-secondary:hover {
      background-color: #4a0ea2;
    }
  </style>
</head>
<body>
  <div class="container d-flex flex-column justify-content-center align-items-center py-5" style="min-height: 100vh;">
    <div class="card p-4 text-center" style="max-width: 700px; width: 100%;">
      <h1 class="mb-4">Live YOLOv5 Detection</h1>
      <img src="{{ url_for('video_feed') }}" alt="Live Camera Feed" class="img-fluid rounded border mb-4" />
      <div class="d-flex justify-content-center gap-3">
        <a href="/stop_camera" class="btn btn-danger btn-lg px-4">Stop Camera</a>
        <a href="/" class="btn btn-secondary btn-lg px-4">Back to Home</a>
      </div>
    </div>
  </div>
</body>
</html>
'''

camera_on = True

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            input_path = os.path.join(UPLOAD_FOLDER, filename)
            output_filename = "result_" + filename
            output_path = os.path.join(RESULT_FOLDER, output_filename)
            file.save(input_path)

            try:
                detect_image(input_path, output_path)
            except Exception as e:
                return f"<h3>Error during detection: {str(e)}</h3><a href='/'>Try Again</a>"

            return redirect(url_for('show_result', filename=output_filename))
        else:
            return "<h3>Invalid file format. Only JPG, JPEG, PNG allowed.</h3><a href='/'>Back</a>"

    return render_template_string(INDEX_HTML)

@app.route('/result/<filename>')
def show_result(filename):
    return render_template_string(RESULT_HTML, filename=filename)

def generate_frames():
    global camera_on
    cap = cv2.VideoCapture(0)
    while camera_on:
        success, frame = cap.read()
        if not success:
            break
        results = model(frame)
        results.render()
        frame = results.ims[0]
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    cap.release()

@app.route('/video_feed')
def video_feed():
    global camera_on
    camera_on = True
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/camera')
def camera():
    return render_template_string(CAMERA_HTML)

@app.route('/stop_camera')
def stop_camera():
    global camera_on
    camera_on = False
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
