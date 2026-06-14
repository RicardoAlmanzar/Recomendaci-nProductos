#!/usr/bin/env python3
"""
Simple HTTP server to serve frontend files from http://localhost:3000
"""
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path


class FrontendHandler(SimpleHTTPRequestHandler):
    """Serve files from the frontend directory and handle SPA routing"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path(__file__).parent / "frontend"), **kwargs)
    
    def end_headers(self):
        """Add CORS headers"""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()
    
    def log_message(self, format, *args):
        """Simplify log messages"""
        print(f"[SERVER] {format % args}")


if __name__ == "__main__":
    PORT = 3000
    server = HTTPServer(("localhost", PORT), FrontendHandler)
    print(f"=> Serving frontend on http://localhost:{PORT}")
    print("Press Ctrl+C to stop the server")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n✓ Server stopped")
        server.server_close()
