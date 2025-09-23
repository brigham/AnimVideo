import http.server
import socketserver
import os
import sys
import time
import threading
import json
from pathlib import Path

# --- Configuration ---
PORT = 8000
VIDEO_FILE_PATH = ""
VIDEO_MIME_TYPE = "video/mp4" # Default, will be updated based on file extension

# --- HTML Template ---
# This will be formatted with the body content and script
HTML_SHELL = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Video Player</title>
    <style>
        body, html {{
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
            background-color: #000;
            color: #eee;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            text-align: center;
        }}
        video {{
            position: absolute;
            top: 50%;
            left: 50%;
            width: 100%;
            height: 100%;
            object-fit: contain; /* Use 'contain' to respect aspect ratio without cropping */
            transform: translate(-50%, -50%);
        }}
        .message-container h1 {{
            font-weight: 300;
        }}
        .message-container code {{
            background-color: #333;
            padding: 0.2em 0.4em;
            border-radius: 4px;
            font-family: "Menlo", "Consolas", monospace;
        }}
    </style>
</head>
<body>
    {body_content}
    {script}
</body>
</html>
"""

class VideoRequestHandler(http.server.SimpleHTTPRequestHandler):
    """A custom request handler to serve the video and status updates."""

    def do_GET(self):
        """Handle GET requests."""
        # The path can contain a query string for cache-busting, so we parse it.
        request_path = self.path.split('?')[0]

        if request_path == '/':
            self.serve_html_player()
        elif request_path == '/status':
            self.serve_status()
        elif request_path.lstrip('/') == VIDEO_FILE_PATH:
            # Let the base class handle serving the video file if it exists.
            # The base handler correctly ignores the query string.
            if os.path.exists(VIDEO_FILE_PATH):
                super().do_GET()
            else:
                self.send_error(404, "File not found")
        else:
            self.send_error(404, "File not found")

    def serve_html_player(self):
        """Serves the main HTML page, showing the video or a 'not found' message."""
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()

        initial_timestamp = 0
        body_content = ""

        try:
            initial_timestamp = os.path.getmtime(VIDEO_FILE_PATH)
            # Append a timestamp to the video source URL to prevent browser caching
            body_content = f'<video id="video-player" src="{VIDEO_FILE_PATH}?v={initial_timestamp}" autoplay loop muted playsinline></video>'
        except OSError:
            # File doesn't exist, so we'll show the message.
            body_content = f"""
            <div class="message-container">
                <h1>Video file not found</h1>
                <p>Waiting for <code>{VIDEO_FILE_PATH}</code> to appear...</p>
            </div>
            """

        polling_script = f"""
        <script>
            // --- Auto-reload script ---
            const initialTimestamp = {initial_timestamp};

            // Poll the server every 2 seconds to check if the file has changed.
            setInterval(async () => {{
                try {{
                    const response = await fetch('/status');
                    if (!response.ok) {{
                        console.error("Status check failed:", response.statusText);
                        return;
                    }}
                    const data = await response.json();

                    // If the timestamp on the server is different, reload the page.
                    if (data.last_modified !== initialTimestamp) {{
                        console.log('Video file status has changed. Reloading...');
                        window.location.reload(true);
                    }}
                }} catch (error) {{
                    console.error("Error checking for video update:", error);
                }}
            }}, 2000);
        </script>
        """

        full_html = HTML_SHELL.format(body_content=body_content, script=polling_script)
        self.wfile.write(full_html.encode('utf-8'))


    def serve_status(self):
        """Serves a JSON response with the video's last modification time."""
        try:
            current_mtime = os.path.getmtime(VIDEO_FILE_PATH)
        except OSError:
            current_mtime = 0 # File doesn't exist, report timestamp as 0

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        response = {
            'last_modified': current_mtime
        }
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def log_message(self, format, *args):
        # Suppress the default logging to keep the console clean
        return


def get_mime_type(filename):
    """Determine the MIME type based on the file extension."""
    ext = Path(filename).suffix.lower()
    types = {
        ".mp4": "video/mp4",
        ".webm": "video/webm",
        ".ogv": "video/ogg",
        ".mov": "video/quicktime",
        ".mkv": "video/x-matroska",
    }
    return types.get(ext, "video/mp4")


def main():
    """Main function to start the server."""
    global VIDEO_FILE_PATH, VIDEO_MIME_TYPE

    if len(sys.argv) < 2:
        print("Usage: python {} <video_file>".format(sys.argv[0]))
        sys.exit(1)

    video_path_arg = sys.argv[1]
    if not os.path.exists(video_path_arg):
        print(f"Warning: Video file not found at '{video_path_arg}'. Waiting for it to appear.")

    VIDEO_FILE_PATH = video_path_arg
    VIDEO_MIME_TYPE = get_mime_type(VIDEO_FILE_PATH)
    # Monkey-patch the mimetypes map for the handler
    VideoRequestHandler.extensions_map[Path(VIDEO_FILE_PATH).suffix] = VIDEO_MIME_TYPE

    with socketserver.TCPServer(("", PORT), VideoRequestHandler) as httpd:
        print(f"Serving video '{VIDEO_FILE_PATH}' at http://localhost:{PORT}")
        print("The server will wait for the file if it doesn't exist.")
        print("Press Ctrl+C to stop the server.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
            #httpd.shutdown()
            pass

if __name__ == "__main__":
    main()
