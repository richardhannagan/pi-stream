#!/usr/bin/env python3
"""
Pi Camera Web Server Script v3
Captures a photo with Pi Camera and serves it via local web server
Designed for Pi Zero W running Bookworm
"""

import os
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import socket

# Configuration
PHOTO_DIR = "/tmp/picam"
PHOTO_NAME = "current_photo.jpg"
SERVER_PORT = 8080

class CameraWebHandler(BaseHTTPRequestHandler):
    """HTTP request handler for serving the camera photo and web interface"""
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            # Serve the main HTML page
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Pi Camera Viewer</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        max-width: 800px;
                        margin: 0 auto;
                        padding: 20px;
                        background-color: #f0f0f0;
                    }}
                    .container {{
                        background-color: white;
                        padding: 20px;
                        border-radius: 10px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }}
                    h1 {{
                        color: #333;
                        text-align: center;
                    }}
                    .photo-container {{
                        text-align: center;
                        margin: 20px 0;
                    }}
                    img {{
                        max-width: 100%;
                        height: auto;
                        border: 2px solid #ddd;
                        border-radius: 5px;
                    }}
                    .buttons {{
                        text-align: center;
                        margin: 20px 0;
                    }}
                    button {{
                        background-color: #4CAF50;
                        color: white;
                        padding: 10px 20px;
                        border: none;
                        border-radius: 5px;
                        cursor: pointer;
                        font-size: 16px;
                        margin: 0 10px;
                    }}
                    button:hover {{
                        background-color: #45a049;
                    }}
                    .info {{
                        background-color: #e7f3ff;
                        padding: 10px;
                        border-radius: 5px;
                        margin: 10px 0;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Pi Camera Viewer</h1>
                    <div class="info">
                        <strong>Last photo taken:</strong> {get_photo_timestamp()}
                    </div>
                    <div class="photo-container">
                        <img src="/photo" alt="Pi Camera Photo" id="photo">
                    </div>
                    <div class="buttons">
                        <button onclick="takeNewPhoto()">Take New Photo</button>
                        <button onclick="refreshPhoto()">Refresh</button>
                    </div>
                </div>
                
                <script>
                    function takeNewPhoto() {{
                        fetch('/capture')
                            .then(response => response.text())
                            .then(data => {{
                                alert('New photo captured!');
                                refreshPhoto();
                            }})
                            .catch(error => {{
                                alert('Error taking photo: ' + error);
                            }});
                    }}
                    
                    function refreshPhoto() {{
                        document.getElementById('photo').src = '/photo?' + new Date().getTime();
                        location.reload();
                    }}
                    
                    // Auto-refresh every 30 seconds
                    setInterval(refreshPhoto, 30000);
                </script>
            </body>
            </html>
            """
            self.wfile.write(html_content.encode())
            
        elif parsed_path.path == '/photo':
            # Serve the photo
            photo_path = os.path.join(PHOTO_DIR, PHOTO_NAME)
            if os.path.exists(photo_path):
                self.send_response(200)
                self.send_header('Content-type', 'image/jpeg')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                
                with open(photo_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'Photo not found')
                
        elif parsed_path.path == '/capture':
            # Capture a new photo
            if capture_photo():
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Photo captured successfully')
            else:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b'Failed to capture photo')
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not found')
    
    def log_message(self, format, *args):
        """Override to customize logging"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")

def setup_camera():
    """Initialize camera settings and directory"""
    # Create photo directory if it doesn't exist
    os.makedirs(PHOTO_DIR, exist_ok=True)
    
    # Check if camera is available
    try:
        # Test camera with a quick capture
        test_cmd = f"libcamera-still --immediate --output /tmp/test_cam.jpg --width 640 --height 480 --timeout 1"
        result = os.system(test_cmd)
        if result == 0:
            os.remove("/tmp/test_cam.jpg")
            print("Camera test successful")
            return True
        else:
            print("Camera test failed")
            return False
    except Exception as e:
        print(f"Camera setup error: {e}")
        return False

def capture_photo():
    """Capture a photo using libcamera-still"""
    photo_path = os.path.join(PHOTO_DIR, PHOTO_NAME)
    
    try:
        # Use libcamera-still for Bookworm
        cmd = f"libcamera-still --output {photo_path} --width 1640 --height 1232 --timeout 2000 --immediate"
        print(f"Capturing photo: {cmd}")
        
        result = os.system(cmd)
        
        if result == 0 and os.path.exists(photo_path):
            print(f"Photo saved: {photo_path}")
            return True
        else:
            print(f"Photo capture failed (exit code: {result})")
            return False
            
    except Exception as e:
        print(f"Error capturing photo: {e}")
        return False

def get_photo_timestamp():
    """Get the timestamp of the current photo"""
    photo_path = os.path.join(PHOTO_DIR, PHOTO_NAME)
    if os.path.exists(photo_path):
        timestamp = os.path.getmtime(photo_path)
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    return "No photo available"

def get_local_ip():
    """Get the local IP address"""
    try:
        # Connect to a remote address to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def main():
    """Main function to start the camera web server"""
    print("Pi Camera Web Server Starting...")
    print("=" * 50)
    
    # Setup camera
    if not setup_camera():
        print("Camera setup failed. Please check your camera connection.")
        return
    
    # Take initial photo
    print("Taking initial photo...")
    if not capture_photo():
        print("Initial photo capture failed, but server will start anyway")
    
    # Start web server
    server_address = ('', SERVER_PORT)
    httpd = HTTPServer(server_address, CameraWebHandler)
    
    local_ip = get_local_ip()
    
    print(f"\nWeb server started!")
    print(f"Access your camera at:")
    print(f"   • Local: http://localhost:{SERVER_PORT}")
    print(f"   • Network: http://{local_ip}:{SERVER_PORT}")
    print(f"\nTips:")
    print(f"   • Click 'Take New Photo' to capture a new image")
    print(f"   • Page auto-refreshes every 30 seconds")
    print(f"   • Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
        httpd.server_close()

if __name__ == "__main__":
    main()
