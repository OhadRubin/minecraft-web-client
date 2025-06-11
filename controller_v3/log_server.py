#!/usr/bin/env python3
"""
Simple HTTP server with logging endpoint for controller_v3
Serves static files and handles POST /log requests
"""

import http.server
import socketserver
import json

class LoggingHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/log':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                log_data = json.loads(post_data.decode('utf-8'))
                message = log_data.get('message', 'No message')
                
                # Print to server console with clear formatting
                print(f"\n🎮 CONTROLLER LOG: {message}")
                
                # Send success response
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.end_headers()
                
                response = {'status': 'logged'}
                self.wfile.write(json.dumps(response).encode())
                
            except Exception as e:
                print(f"❌ Error processing log: {e}")
                self.send_response(500)
                self.end_headers()
        else:
            # For other POST requests, return 404
            self.send_response(404)
            self.end_headers()
    
    def do_OPTIONS(self):
        # Handle CORS preflight requests
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

if __name__ == "__main__":
    PORT = 8091
    
    print(f"🚀 Starting controller_v3 server with logging on port {PORT}")
    print(f"📁 Serving files from: {__file__.replace('/log_server.py', '')}")
    print(f"📝 Logs from sendCommand() will appear below:")
    print("=" * 60)
    
    with socketserver.TCPServer(("", PORT), LoggingHTTPRequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print(f"\n🛑 Server stopped")