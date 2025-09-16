import cv2
from flask import Flask, Response, request, jsonify

app = Flask(__name__)

# Global variables to manage the video stream
current_stream_url = ""
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
            # Encode the frame in JPEG format
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            
            # Yield the frame in byte format
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    
    # Release the camera when streaming stops
    if camera:
        camera.release()
    camera = None
    is_streaming = False

@app.route('/')
def index():
    # Serve the HTML page directly from the same directory
    with open('app.html', 'r') as f:
        html_content = f.read()
    return html_content

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), 
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/start_stream', methods=['POST'])
def start_stream():
    global current_stream_url, camera, is_streaming
    
    # Stop any existing stream
    if camera:
        camera.release()
        camera = None
        is_streaming = False
    
    # Get the stream URL from the request
    stream_url = request.form.get('stream_url')
    
    if not stream_url:
        return jsonify({'success': False, 'message': 'No stream URL provided'})
    
    try:
        # Try to open the video stream
        camera = cv2.VideoCapture(stream_url)
        
        if not camera.isOpened():
            return jsonify({'success': False, 'message': 'Cannot open stream. Check the URL.'})
        
        current_stream_url = stream_url
        is_streaming = True
        
        return jsonify({'success': True, 'message': 'Stream started successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/stop_stream', methods=['POST'])
def stop_stream():
    global camera, is_streaming
    
    if camera:
        camera.release()
        camera = None
    
    is_streaming = False
    return jsonify({'success': True, 'message': 'Stream stopped'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)