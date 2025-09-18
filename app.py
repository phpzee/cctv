import cv2
from flask import Flask, Response, request, jsonify
import os

app = Flask(__name__)

# Global variables
camera = None
is_streaming = False


def generate_frames():
    global camera, is_streaming
    while is_streaming:
        if camera is None:
            break

        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    if camera:
        camera.release()
    camera = None
    is_streaming = False


@app.route('/')
def index():
    with open("app.html", "r") as f:
        return f.read()


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/start_stream', methods=['POST'])
def start_stream():
    global camera, is_streaming
    if camera:
        camera.release()
        camera = None
        is_streaming = False

    stream_url = request.form.get("stream_url")
    if not stream_url:
        return jsonify({"success": False, "message": "No stream URL provided"})

    try:
        camera = cv2.VideoCapture(stream_url)
        if not camera.isOpened():
            return jsonify({"success": False, "message": "Cannot open stream. Check URL."})

        is_streaming = True
        return jsonify({"success": True, "message": "Stream started"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"})


@app.route('/stop_stream', methods=['POST'])
def stop_stream():
    global camera, is_streaming
    if camera:
        camera.release()
        camera = None
    is_streaming = False
    return jsonify({"success": True, "message": "Stream stopped"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
